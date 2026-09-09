# -*- coding: utf-8 -*-
"""social.py — 社媒私信流水线：入站 → 意图分类 → 转线索 → 起草回复 → 人工确认 → 发出 → 统计

和 collector.py 的分工（面试要讲清楚）：
  collector.py  = 【拉】主动去搜公开线索（别人留的邮箱/公司）
  social.py     = 【推】接住企业社媒账号收到的主动咨询（用户主动发来的私信）
  两条线最终都汇入同一张 leads 表，下游三个 Agent 完全无感知来源。

为什么不自动回复（关键设计决策）：
  1. B2B 定制家具单条线索价值几千到几万美金，AI 说错一句 MOQ 或交期可能直接丢单
  2. Meta/TikTok 等平台对自动化发送有严格风控，无脑自动发会限流甚至封企业号
  3. 所以设计成"AI 起草 + 人工一键确认"：省掉 90% 打字时间，但人保留最终决定权
  → 真要全自动，把 AUTO_SEND 打开即可（按渠道白名单控制）
"""
import hashlib
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

import db                      # 复用项目4的线索表
from config import DB_PATH
from channels import get_channel, InboundMessage, PLATFORM_LABEL

SCHEMA = """
CREATE TABLE IF NOT EXISTS social_messages (
  id               TEXT PRIMARY KEY,
  channel          TEXT NOT NULL,
  external_user_id TEXT NOT NULL,
  handle           TEXT,
  direction        TEXT NOT NULL DEFAULT 'inbound',
  text             TEXT NOT NULL,
  intent           TEXT,
  lead_id          TEXT,
  reply_draft      TEXT,
  draft_source     TEXT,
  status           TEXT NOT NULL DEFAULT 'pending_review',
  received_at      TEXT,
  reviewed_at      TEXT,
  sent_at          TEXT,
  updated_at       TEXT
);
CREATE INDEX IF NOT EXISTS idx_sm_status  ON social_messages(status);
CREATE INDEX IF NOT EXISTS idx_sm_channel ON social_messages(channel);
"""

# 意图词表：海外 B2B 定制家具场景（英文为主，中文兜底国内客户）
INTENT_RULES = [
    ("quote", ("price", "quote", "moq", "cost", "how much", "budget",
               "价格", "报价", "多少钱", "起订", "报价单")),
    ("sample", ("sample", "样品", "寄样", "trial order", "试单")),
    ("partner", ("distributor", "agent", "partner", "wholesale", "reseller",
                 "代理", "经销", "合作")),
    ("cert", ("certification", "carb", "tsca", "fsc", "ce ", "e1", "compliance",
              "认证", "环保", "资质")),
    ("catalog", ("catalog", "catalogue", "brochure", "portfolio", "产品册", "目录")),
]

# 自动发送开关：默认关闭（人工确认制）。设为渠道名集合可开启全自动，例：{"whatsapp"}
AUTO_SEND = set()


# ══════════════════════ 数据层 ══════════════════════
def _conn():
    return sqlite3.connect(DB_PATH)


def init_social_db():
    with _conn() as conn:
        conn.executescript(SCHEMA)


# ══════════════════════ 意图分类 ══════════════════════
def classify_intent(text):
    """按词表打分取最高命中；无命中返回 general"""
    t = (text or "").lower()
    for intent, kws in INTENT_RULES:
        if any(k in t for k in kws):
            return intent
    return "general"


# ══════════════════════ 入站处理 ══════════════════════
def _mid(channel, uid, text):
    return hashlib.md5(f"{channel}:{uid}:{text[:32]}".encode("utf-8")).hexdigest()[:12]


def to_lead(msg, intent):
    """私信 → leads 表一条线索（contact 用 平台:用户ID，保证唯一索引去重）"""
    now = datetime.now().isoformat()
    contact = f"{msg.channel}:{msg.external_user_id}"
    lead = {
        "id": hashlib.md5(f"{msg.channel}:{contact}".encode("utf-8")).hexdigest()[:8],
        "source": f"social-{msg.channel}",
        "contact": contact,
        "company": msg.handle or "",
        "country": "",
        "intent": intent,
        "stage": "new",
        "summary": (msg.text or "")[:80],
        "raw_text": msg.text,
        "collected_at": now,
        "updated_at": now,
    }
    db.upsert_lead(lead)
    return lead["id"]


def _template_reply(msg, intent):
    """离线回复模板：只搭结构，真实参数留占位符由人工补——不编造 MOQ/交期"""
    who = msg.handle or "there"
    body = {
        "quote": "Thanks for your interest in our custom cabinetry.\n\n"
                 "To prepare an accurate quote, could you share:\n"
                 "1. Project type (residential / commercial) and quantity\n"
                 "2. Cabinet style and material preference\n"
                 "3. Destination port\n\n"
                 "For reference, our MOQ is [MOQ] and standard lead time is [LEAD_TIME].\n"
                 "Once we have your specs, we can send a formal quote within [SLA].",
        "sample": "Sure, we can arrange samples.\n\n"
                  "Please confirm the door style and finish you'd like, plus your courier "
                  "account (DHL/FedEx/UPS) or delivery address.\n"
                  "Sample cost is [SAMPLE_COST], refundable against your first order.",
        "partner": "Thank you for reaching out about partnership.\n\n"
                   "Could you tell us:\n"
                   "1. Your market and current product range\n"
                   "2. Estimated annual volume\n"
                   "3. Whether you handle installation locally\n\n"
                   "We'll then share our partner terms and tiered pricing.",
        "cert": "We hold [CERTS] certifications for our panels and hardware.\n\n"
                "Please let me know your target market and I'll send the relevant "
                "test reports and compliance documents.",
        "catalog": "Glad to send you our catalog.\n\n"
                   "Which product line are you most interested in "
                   "(kitchen cabinets / wardrobes / bathroom vanities / whole-house)?\n"
                   "I'll share the matching catalog plus recent project photos.",
    }.get(intent,
          "Hi — thanks for getting in touch!\n\n"
          "Could you share a bit more about your project "
          "(product type, quantity, destination)? "
          "I'll get back with the details you need.")
    return f"Hi {who},\n\n{body}\n\nBest regards,\n[Your Name]\n[Company]"


def _llm_reply(msg, intent):
    """调项目2的销售Agent起草（需 DeepSeek key）；失败返回 None 由调用方降级"""
    try:
        root = BASE.parent
        for cand in (root / "quanwu-ai-agent", root / "P2-Agents"):
            if (cand / "agents" / "sales_agent.py").exists():
                sys.path.insert(0, str(cand))
                from agents.sales_agent import draft_reply
                return draft_reply({
                    "contact": msg.handle or "there",
                    "intent": intent,
                    "summary": (msg.text or "")[:200],
                })
    except Exception:
        return None
    return None


def draft(msg, intent, use_llm=False):
    """起草回复，返回 (文本, 来源)。来源会写进数据库，UI 显示时不混淆真假"""
    if use_llm:
        text = _llm_reply(msg, intent)
        if text:
            return text, "llm"
    return _template_reply(msg, intent), "template"


def ingest(msg, use_llm=False, auto_send=None):
    """入站一条私信：落库 → 分类 → 转线索 → 起草 → （可选）自动发送

    返回消息 dict，含 status 字段：
      pending_review 待人工确认（默认）
      sent           已自动发出（auto_send 命中时）
      ignored        空文本被丢弃（由调用方判断）
    """
    init_social_db()
    now = datetime.now().isoformat()
    intent = classify_intent(msg.text)
    lead_id = to_lead(msg, intent)
    text, source = draft(msg, intent, use_llm=use_llm)

    mid = _mid(msg.channel, msg.external_user_id, msg.text)
    status = "pending_review"
    sent_at = None

    auto = AUTO_SEND if auto_send is None else auto_send
    if msg.channel in auto:
        res = get_channel(msg.channel).send(msg.external_user_id, text)
        status = "sent" if res.ok else "send_failed"
        sent_at = now if res.ok else None

    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO social_messages "
            "(id, channel, external_user_id, handle, direction, text, intent, lead_id,"
            " reply_draft, draft_source, status, received_at, sent_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (mid, msg.channel, msg.external_user_id, msg.handle, "inbound",
             msg.text, intent, lead_id, text, source, status,
             msg.received_at, sent_at, now),
        )
    return {"id": mid, "channel": msg.channel, "intent": intent,
            "lead_id": lead_id, "status": status, "draft_source": source}


def ingest_payload(channel_name, payload, **kw):
    """webhook 入口：平台原始 payload → 批量 ingest"""
    ch = get_channel(channel_name)
    return [ingest(m, **kw) for m in ch.parse_inbound(payload)]


# ══════════════════════ 人工审核 ══════════════════════
def list_messages(status=None, channel=None, limit=100):
    init_social_db()
    sql = "SELECT * FROM social_messages WHERE 1=1"
    args = []
    if status:
        sql += " AND status = ?"
        args.append(status)
    if channel:
        sql += " AND channel = ?"
        args.append(channel)
    sql += " ORDER BY received_at DESC LIMIT ?"
    args.append(limit)
    conn = _conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def approve(msg_id, edited_text=None):
    """人工确认并发出。edited_text 允许人工改后再发"""
    init_social_db()
    conn = _conn()
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM social_messages WHERE id = ?", (msg_id,)).fetchone()
    if not row:
        conn.close()
        return {"ok": False, "error": "消息不存在"}
    row = dict(row)
    text = edited_text or row["reply_draft"]
    res = get_channel(row["channel"]).send(row["external_user_id"], text)
    now = datetime.now().isoformat()
    if res.ok:
        conn.execute("UPDATE social_messages SET status='sent', sent_at=?, updated_at=? "
                     "WHERE id=?", (now, now, msg_id))
        conn.execute("UPDATE leads SET stage='contacted', updated_at=? WHERE id=?",
                     (now, row["lead_id"]))
    else:
        conn.execute("UPDATE social_messages SET status='send_failed', updated_at=? "
                     "WHERE id=?", (now, msg_id))
    conn.commit()
    conn.close()
    return {"ok": res.ok, "message_id": res.message_id, "error": res.error}


def reject(msg_id, reason=""):
    """标记为无效（广告/骚扰/无意向），不发送"""
    with _conn() as conn:
        conn.execute("UPDATE social_messages SET status='ignored', updated_at=? WHERE id=?",
                     (datetime.now().isoformat(), msg_id))
    return {"ok": True, "reason": reason}


# ══════════════════════ 统计 ══════════════════════
def stats():
    """私信运营看板：渠道分布 / 意图分布 / 处理漏斗 / 平均响应时长"""
    init_social_db()
    conn = _conn()
    q = lambda s: conn.execute(s).fetchone()[0]

    by_channel = dict(conn.execute(
        "SELECT channel, COUNT(*) FROM social_messages GROUP BY channel").fetchall())
    by_intent = dict(conn.execute(
        "SELECT intent, COUNT(*) FROM social_messages GROUP BY intent").fetchall())
    by_status = dict(conn.execute(
        "SELECT status, COUNT(*) FROM social_messages GROUP BY status").fetchall())

    # 平均响应时长：收到 → 发出（分钟）
    rows = conn.execute(
        "SELECT received_at, sent_at FROM social_messages "
        "WHERE status='sent' AND sent_at IS NOT NULL").fetchall()
    spans = []
    for r, s in rows:
        try:
            spans.append((datetime.fromisoformat(s) - datetime.fromisoformat(r)).total_seconds() / 60)
        except Exception:
            pass
    conn.close()

    total = sum(by_channel.values()) or 1
    sent = by_status.get("sent", 0)
    return {
        "total": sum(by_channel.values()),
        "by_channel": by_channel,
        "by_intent": by_intent,
        "by_status": by_status,
        "reply_rate": round(sent / total * 100, 1),
        "avg_response_min": round(sum(spans) / len(spans), 1) if spans else None,
    }


# ══════════════════════ 演示 ══════════════════════
DEMO_MESSAGES = [
    ("instagram", "ig_88231", "@oak_interiors",
     "Hi, we are a contractor in Melbourne. What is your MOQ for custom wardrobes and can you send a quote?"),
    ("whatsapp", "8613800001122", "David Chen",
     "Do you have CARB P2 certification? We need it for the US market."),
    ("tiktok", "tt_772019", "@renovate_diy",
     "love the sliding door video!! where can i get one"),
    ("youtube", "UC_x9s8dd", "Builder Mike",
     "How much per square meter for kitchen cabinets wholesale? Looking for a supplier."),
    ("aggregator", "lead_4491", "Sofia Rossi",
     "We are a distributor in Italy interested in your whole-house customization. Can we partner?"),
]


def demo(use_llm=False):
    """跑通全流程：模拟 5 个平台各来一条咨询"""
    db.init_db()
    init_social_db()
    print("=" * 64)
    print("社媒私信接入 · 全流程演示")
    print("=" * 64)

    print("\n[1] 各平台私信进入系统")
    print("-" * 64)
    for ch, uid, handle, text in DEMO_MESSAGES:
        r = ingest(InboundMessage(channel=ch, external_user_id=uid,
                                  handle=handle, text=text), use_llm=use_llm)
        label = PLATFORM_LABEL.get(ch, ch)
        print(f"  {label:<12} {handle:<16} → 意图={r['intent']:<9} 线索={r['lead_id']}")

    print("\n[2] 待人工确认队列（AI 已起草好，人一键放行）")
    print("-" * 64)
    for m in list_messages(status="pending_review"):
        label = PLATFORM_LABEL.get(m["channel"], m["channel"])
        print(f"\n  ▸ {label} · {m['handle']} · 意图={m['intent']} · 草稿来源={m['draft_source']}")
        print(f"    客户说：{m['text'][:70]}")
        first = (m["reply_draft"] or "").split("\n")[0]
        print(f"    拟回复：{first}")

    print("\n[3] 运营统计看板")
    print("-" * 64)
    s = stats()
    print(f"  总私信数    {s['total']}")
    for k, v in s["by_channel"].items():
        print(f"    {PLATFORM_LABEL.get(k, k):<14} {v}")
    print(f"  意图分布    {s['by_intent']}")
    print(f"  处理状态    {s['by_status']}")
    print(f"  回复率      {s['reply_rate']}%")
    print(f"  平均响应    {s['avg_response_min']} 分钟" if s["avg_response_min"] else "  平均响应    —")

    print("\n[4] 线索已汇入 CRM（与主动采集共用一张表）")
    print("-" * 64)
    for l in db.get_leads():
        if l["source"].startswith("social-"):
            print(f"  {l['id']}  {l['source']:<18} {l['contact']:<22} intent={l['intent']}")
    print("\n完成。真实接入需配各平台 token（见 ENV 说明）；无 token 时 send 会明确报错而非假装成功。\n")


if __name__ == "__main__":
    demo(use_llm="--llm" in sys.argv)
