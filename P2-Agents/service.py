# -*- coding: utf-8 -*-
"""service.py — 获客矩阵 HTTP 服务（:8001）

让项目5 网页能触发并读取「内容→运营→销售」整套闭环，
而不只是 CLI 演示。标准库实现，零额外依赖。

端点：
  POST /api/acquire/run           启动后台闭环任务，立即返回 task_id
  GET  /api/acquire/task/<id>     查任务进度（status/progress/eta）
  GET  /api/acquire/task/<id>/result  取任务最终结果（仅 completed 时）
  POST /api/acquire/crawl         抓取→识别→接待 全链路（真数据源接入）
  GET  /api/acquire/crawlers      列出已配置的爬虫与启用状态
  POST /api/inbox                 接收一条真实社媒消息，追加到 data/inbox.json
  GET  /health                    健康检查
"""
import json
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from orchestrator import reset_crm
import agents.content_agent as content_agent
import agents.ops_agent as ops_agent
import agents.sales_agent as sales_agent
import state.leads as leads_state
from crawlers import get_enabled_crawlers, all_crawler_status, RawLead

# ==== 异步任务表（闭环跑得久，丢后台线程；前台轮询进度）====
_TASKS = {}
_TASKS_LOCK = threading.Lock()


def _new_task():
    tid = uuid.uuid4().hex[:12]
    with _TASKS_LOCK:
        _TASKS[tid] = {
            "status": "running",                # running / completed / failed
            "step": "init",
            "progress": 0,                       # 0..100
            "message": "已派发任务…",
            "started_at": time.time(),
            "finished_at": None,
            "result": None,
            "error": None,
        }
    return tid


def _patch_task(tid, **kv):
    with _TASKS_LOCK:
        if tid in _TASKS:
            _TASKS[tid].update(kv)


def _eta(task):
    """粗估剩余秒数（基于已完成 progress 与耗时线性外推）"""
    if task["status"] != "running":
        return None
    pct = task.get("progress", 0)
    if pct <= 0:
        return None
    elapsed = time.time() - task.get("started_at", time.time())
    total_est = elapsed / (pct / 100.0)
    return max(0, int(total_est - elapsed))


def run_acquire(progress=None):
    """跑 内容→运营→销售 闭环，每次都是干净结果，返回结构化数据
       progress(step, msg, pct) 回调用于浏览器实时显示
    """
    reset_crm()                               # 清空上次闭环的线索
    if progress: progress("content", "① 内容 Agent：起草 3 平台获客帖…", 15)
    posts = content_agent.run_return()        # ① 内容Agent：3 平台获客帖
    if progress: progress("ops", "② 运营 Agent：识别社媒线索入库…", 45)
    ops_agent.run()                           # ② 运营Agent：识别线索入库
    if progress: progress("sales", "③ 销售 Agent：逐条起草英文话术…", 70)
    sales_agent.run()                         # ③ 销售Agent：起草话术回写
    if progress: progress("done", "完成，结果已落库", 100)
    return {"posts": posts, "leads": leads_state.load_leads()}


def run_acquire_async():
    """派发后台线程跑 run_acquire，前台立即拿到 task_id"""
    tid = _new_task()

    def worker():
        def cb(step, msg, pct):
            _patch_task(tid, step=step, message=msg, progress=pct)
        try:
            result = run_acquire(progress=cb)
            _patch_task(tid, status="completed", result=result,
                        finished_at=time.time())
        except Exception as e:
            _patch_task(tid, status="failed", error=str(e),
                        finished_at=time.time())
    threading.Thread(target=worker, daemon=True).start()
    return tid


def add_inbox_message(m):
    """把一条真实社媒消息追加到 data/inbox.json，供下次闭环识别"""
    inbox_file = BASE / "data" / "inbox.json"
    data = json.load(open(inbox_file, encoding="utf-8"))
    data.setdefault("messages", [])
    data["messages"].append({
        "source": m.get("source", "Web form"),
        "contact": m.get("contact", "anonymous"),
        "text": m.get("text", ""),
    })
    json.dump(data, open(inbox_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return {"source": m.get("source"), "contact": m.get("contact")}


def append_inbox_messages(leads):
    """批量追加 RawLead 列表到 inbox.json，返回追加条数"""
    inbox_file = BASE / "data" / "inbox.json"
    data = json.load(open(inbox_file, encoding="utf-8"))
    data.setdefault("messages", [])
    appended = 0
    for lead in leads:
        if isinstance(lead, RawLead):
            data["messages"].append(lead.to_inbox())
        else:
            data["messages"].append({
                "source": lead.get("source", "Web form"),
                "contact": lead.get("contact", "anonymous"),
                "text": lead.get("text", ""),
            })
        appended += 1
    json.dump(data, open(inbox_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return appended


def run_crawl_and_acquire(query: str = "", limit: int = 5, run_pipeline: bool = True):
    """抓取→识别→接待 全链路。
       按 .env 的 CRAWLERS 顺序跑爬虫，抓到的 RawLead 写入 inbox，
       若 run_pipeline=True 再跑 ops_agent（识别）+ sales_agent（接待）。
    """
    crawlers = get_enabled_crawlers()
    crawl_results = []     # [{crawler, ok, count, error, leads?}]
    all_fetched = []
    for c in crawlers:
        try:
            leads = c.fetch(query, limit=limit)
            crawl_results.append({"crawler": c.name, "ok": True, "count": len(leads), "leads": [l.to_inbox() for l in leads]})
            all_fetched.extend(leads)
            if len(all_fetched) >= limit:
                break  # 够了
        except Exception as e:
            crawl_results.append({"crawler": c.name, "ok": False, "error": str(e)})

    appended = append_inbox_messages(all_fetched[:limit])

    posts = []
    lead_output = []
    if run_pipeline and appended > 0:
        try:
            posts = content_agent.run_return()
        except Exception as e:
            posts = []
            crawl_results.append({"stage": "content", "ok": False, "error": str(e)})
        try:
            ops_agent.run()
            sales_agent.run()
            lead_output = leads_state.load_leads()
        except Exception as e:
            crawl_results.append({"stage": "ops+sales", "ok": False, "error": str(e)})

    return {
        "query": query,
        "limit": limit,
        "crawlers": crawl_results,
        "fetched_count": len(all_fetched[:limit]),
        "appended_to_inbox": appended,
        "posts": posts,
        "leads": lead_output,
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"status": "ok"})
        if self.path == "/api/acquire/crawlers":
            return self._send(200, {"crawlers": all_crawler_status()})
        # 任务进度查询：/api/acquire/task/<id>  或  /api/acquire/task/<id>/result
        if self.path.startswith("/api/acquire/task/"):
            rest = self.path[len("/api/acquire/task/"):]
            parts = rest.split("/")
            tid = parts[0]
            with _TASKS_LOCK:
                t = _TASKS.get(tid)
            if not t:
                return self._send(404, {"error": "task not found"})
            if len(parts) == 2 and parts[1] == "result":
                if t["status"] != "completed":
                    return self._send(409, {"error": "not ready", "status": t["status"]})
                return self._send(200, t["result"])
            # 默认返回进度（脱敏 result 以免巨大 payload）
            view = {k: v for k, v in t.items() if k != "result"}
            view["eta_sec"] = _eta(t)
            return self._send(200, view)
        self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
        except Exception:
            payload = {}
        if self.path == "/api/acquire/run":
            try:
                tid = run_acquire_async()
                return self._send(202, {
                    "task_id": tid,
                    "status": "running",
                    "message": "闭环已在后台启动，前台每 2 秒轮询 /api/acquire/task/<id>",
                    "poll_url": f"/api/acquire/task/{tid}",
                    "result_url": f"/api/acquire/task/{tid}/result",
                })
            except Exception as e:
                return self._send(500, {"error": str(e)})
        if self.path == "/api/acquire/crawl":
            try:
                q = payload.get("query", "")
                limit = int(payload.get("limit", 5))
                run_pipeline = bool(payload.get("pipeline", True))
                return self._send(200, run_crawl_and_acquire(q, limit=limit, run_pipeline=run_pipeline))
            except Exception as e:
                return self._send(500, {"error": str(e)})
        if self.path == "/api/inbox":
            try:
                return self._send(200, {"added": add_inbox_message(payload)})
            except Exception as e:
                return self._send(400, {"error": str(e)})
        self._send(404, {"error": "not found"})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("获客矩阵服务已启动 :8001  (POST /api/acquire/run → 异步 + 轮询)")
    HTTPServer(("0.0.0.0", 8001), Handler).serve_forever()
