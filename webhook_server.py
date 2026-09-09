# -*- coding: utf-8 -*-
"""webhook_server.py — 社媒私信 webhook 接收服务（零第三方依赖，纯标准库）

启动：
    python webhook_server.py
    → 审核台  http://localhost:8002
    → 各平台 webhook 地址  http://你的公网域名/webhook/<平台名>
      例：/webhook/instagram  /webhook/whatsapp  /webhook/tiktok  /webhook/linkedin

为什么不用 FastAPI：
  这个服务只做三件事（收 JSON、查库、回 JSON），标准库够用且零安装成本。
  真要并入项目5的平台，把下面 4 个路由原样搬成 FastAPI 路由即可，业务函数不用改。

对外暴露注意：
  平台要求 webhook 必须是 HTTPS 公网地址。本地开发用内网穿透
  （ngrok / cpolar / 花生壳）把 8002 映射出去，Meta 才肯推消息。
"""
import json
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

import social
from channels import get_channel, PLATFORM_LABEL

PORT = 8002


class Handler(BaseHTTPRequestHandler):
    server_version = "SocialWebhook/1.0"

    # ---------- 输出工具 ----------
    def _send(self, body, ctype="application/json; charset=utf-8", code=200):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(json.dumps(obj, ensure_ascii=False), code=code)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw or b"{}")
        except Exception:
            return {}

    # ---------- GET ----------
    def do_GET(self):
        u = urlparse(self.path)
        path, qs = u.path, parse_qs(u.query)

        if path in ("/", "/ui"):
            f = BASE / "web_ui.html"
            self._send(f.read_text(encoding="utf-8") if f.exists() else "<h1>缺少 web_ui.html</h1>",
                       ctype="text/html; charset=utf-8")
            return

        # 平台注册 webhook 时的校验请求（Meta/WhatsApp/TikTok 都会先发一次 GET）
        if path.startswith("/webhook/"):
            ch = path.rstrip("/").split("/")[-1]
            try:
                challenge = get_channel(ch).verify_webhook({k: v[0] for k, v in qs.items()})
            except KeyError as e:
                return self._json({"error": str(e)}, 400)
            if challenge is None:
                return self._json({"error": "verify_token 不匹配"}, 403)
            return self._send(str(challenge), ctype="text/plain; charset=utf-8")

        if path == "/api/messages":
            return self._json(social.list_messages(
                status=qs.get("status", [None])[0],
                channel=qs.get("channel", [None])[0]))

        if path == "/api/stats":
            return self._json(social.stats())

        return self._json({"error": "not found"}, 404)

    # ---------- POST ----------
    def do_POST(self):
        path = urlparse(self.path).path
        payload = self._read_json()

        if path.startswith("/webhook/"):
            ch = path.rstrip("/").split("/")[-1]
            try:
                items = social.ingest_payload(ch, payload)
            except KeyError as e:
                return self._json({"error": str(e)}, 400)
            print(f"[{datetime.now():%H:%M:%S}] 收到 {ch} 私信 {len(items)} 条")
            return self._json({"received": len(items), "items": items})

        parts = [p for p in path.split("/") if p]
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "messages":
            mid, action = parts[2], None
        elif len(parts) == 4 and parts[0] == "api" and parts[1] == "messages":
            mid, action = parts[2], parts[3]
        else:
            return self._json({"error": "not found"}, 404)

        if action == "approve":
            res = social.approve(mid, edited_text=payload.get("text"))
            print(f"[{datetime.now():%H:%M:%S}] 放行 {mid} → {'成功' if res['ok'] else res.get('error')}")
            return self._json(res)
        if action == "reject":
            return self._json(social.reject(mid, payload.get("reason", "")))

        return self._json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        pass  # 静音默认日志，改用上面的中文打印


def main():
    social.db.init_db()
    social.init_social_db()
    print("=" * 56)
    print(" 社媒私信接入服务已启动")
    print("=" * 56)
    print(f" 审核台        http://localhost:{PORT}")
    print(f" webhook 地址  http://你的公网域名/webhook/<平台>")
    print(f" 支持平台      {', '.join(sorted(PLATFORM_LABEL))}")
    print(f" 数据库        {social.DB_PATH}")
    print("\n 本地调试：先跑 python social.py 灌入演示数据，再开审核台看效果")
    print(" Ctrl+C 停止\n")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
