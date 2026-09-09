# -*- coding: utf-8 -*-
"""test_social.py — 社媒私信模块端到端冒烟测试

用真实平台的 payload 样本测适配器，用临时数据库测流水线，不污染 leads.db。

运行：
    python test_social.py
"""
import os
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

# 先切到临时库，再 import 业务模块
_TMP = tempfile.mkdtemp(prefix="social_test_")
_TEST_DB = os.path.join(_TMP, "test.db")

import config                      # noqa: E402
config.DB_PATH = _TEST_DB
import db                          # noqa: E402
db.DB_PATH = _TEST_DB
import social                      # noqa: E402
from channels import get_channel   # noqa: E402

social.DB_PATH = _TEST_DB
db.init_db()
social.init_social_db()

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail and not cond else ""))


# ═══════════ 1. 各平台 payload 解析（真实格式样本）═══════════
print("\n[1] 平台 payload 解析")

META_PAYLOAD = {
    "object": "instagram",
    "entry": [{"messaging": [
        {"sender": {"id": "ig_123"}, "recipient": {"id": "page_1"},
         "message": {"mid": "m1", "text": "What is your MOQ for wardrobes?"}}]}],
}
msgs = get_channel("instagram").parse_inbound(META_PAYLOAD)
check("Instagram 解析", len(msgs) == 1 and msgs[0].external_user_id == "ig_123"
      and msgs[0].text.startswith("What is your MOQ"))
check("Instagram 渠道标记正确", msgs and msgs[0].channel == "instagram")

WA_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [{"changes": [{"value": {"messages": [
        {"from": "8613800000000", "type": "text",
         "text": {"body": "Do you have FSC certification?"}}]}}]}],
}
msgs = get_channel("whatsapp").parse_inbound(WA_PAYLOAD)
check("WhatsApp 解析", len(msgs) == 1 and msgs[0].text.startswith("Do you have FSC"))

YT_PAYLOAD = {"items": [{"snippet": {"topLevelComment": {"snippet": {
    "authorDisplayName": "Builder Mike",
    "authorChannelId": {"value": "UC_abc"},
    "textDisplay": "How much per square meter wholesale?"}}}}]}
msgs = get_channel("youtube").parse_inbound(YT_PAYLOAD)
check("YouTube 评论解析", len(msgs) == 1 and msgs[0].handle == "Builder Mike")

TT_PAYLOAD = {"data": [{"sender": {"open_id": "tt_9", "nickname": "@diy"},
                        "message": {"text": "where can I buy this door"}}]}
msgs = get_channel("tiktok").parse_inbound(TT_PAYLOAD)
check("TikTok 解析", len(msgs) == 1 and msgs[0].handle == "@diy")

AGG_PAYLOAD = {"data": {"user_id": "lead_1", "username": "Sofia",
                        "text": "We are a distributor in Italy"}}
msgs = get_channel("aggregator").parse_inbound(AGG_PAYLOAD)
check("聚合通道解析", len(msgs) == 1 and msgs[0].external_user_id == "lead_1")

# ═══════════ 2. 意图分类 ═══════════
print("\n[2] 意图分类")
for text, want in [
    ("What is your MOQ and price?", "quote"),
    ("Do you have CARB P2 certification?", "cert"),
    ("Can you send a sample door?", "sample"),
    ("We are a distributor interested in partnership", "partner"),
    ("Please send your catalog", "catalog"),
    ("love your video!", "general"),
]:
    got = social.classify_intent(text)
    check(f"分类 {want}", got == want, f"实得 {got}")

# ═══════════ 3. 流水线：入站 → 转线索 → 起草 ═══════════
print("\n[3] 流水线")
from channels import InboundMessage  # noqa: E402

m = InboundMessage(channel="mock", external_user_id="u1",
                   handle="@buyer", text="I need a quote for 200 wardrobes")
r = social.ingest(m)
check("入站返回待确认", r["status"] == "pending_review")
check("已生成线索", bool(r["lead_id"]))
check("意图识别为 quote", r["intent"] == "quote")

leads = [l for l in db.get_leads() if l["source"] == "social-mock"]
check("线索已入 CRM", len(leads) == 1 and leads[0]["intent"] == "quote")

draft = social.list_messages(status="pending_review")[0]["reply_draft"]
check("草稿已生成", bool(draft) and len(draft) > 30)
check("草稿不编造参数（用占位符）", "[MOQ]" in draft or "[LEAD_TIME]" in draft or "[SLA]" in draft)

# 重复入站应去重
n_before = len(db.get_leads())
social.ingest(InboundMessage(channel="mock", external_user_id="u1", handle="@buyer",
                             text="I need a quote for 200 wardrobes"))
check("重复消息不重复建线索", len(db.get_leads()) == n_before)

# ═══════════ 4. 审核：放行 / 忽略 ═══════════
print("\n[4] 人工审核")
rows = social.list_messages(status="pending_review")
target = [x for x in rows if x["channel"] == "mock"][0]

res = social.approve(target["id"])
check("放行成功（mock 通道）", res["ok"] is True, res.get("error"))
after = [x for x in social.list_messages() if x["id"] == target["id"]][0]
check("状态变为 sent", after["status"] == "sent")
check("已记录发送时间", bool(after["sent_at"]))
ld = [l for l in db.get_leads() if l["id"] == target["lead_id"]][0]
check("线索阶段推进为 contacted", ld["stage"] == "contacted")

# 改后发送
m2 = InboundMessage(channel="mock", external_user_id="u2", handle="@b2",
                    text="need catalog please")
r2 = social.ingest(m2)
social.approve(r2["id"], edited_text="人工改写后的内容")
row2 = [x for x in social.list_messages() if x["id"] == r2["id"]][0]
check("编辑后可发送", row2["status"] == "sent")

# 忽略
m3 = InboundMessage(channel="mock", external_user_id="u3", handle="@spam",
                    text="buy followers cheap")
r3 = social.ingest(m3)
social.reject(r3["id"], reason="广告")
row3 = [x for x in social.list_messages() if x["id"] == r3["id"]][0]
check("忽略生效", row3["status"] == "ignored")

# ═══════════ 5. 无 token 时必须明确报错，不能假装成功 ═══════════
print("\n[5] 未配 token 的行为")
m4 = InboundMessage(channel="instagram", external_user_id="ig_x", handle="@x",
                    text="price please")
r4 = social.ingest(m4)
res4 = social.approve(r4["id"])
check("Instagram 未配 token 时报错", res4["ok"] is False and "META_PAGE_TOKEN" in res4.get("error", ""))
row4 = [x for x in social.list_messages() if x["id"] == r4["id"]][0]
check("失败状态记为 send_failed", row4["status"] == "send_failed")

# ═══════════ 6. 统计 ═══════════
print("\n[6] 统计看板")
s = social.stats()
# 共入站 5 次，其中 1 条重复被去重 → 实际 4 条
check("总数为去重后的入站条数", s["total"] == 4, f"实得 {s['total']}")
check("按渠道分组存在", "mock" in s["by_channel"] and "instagram" in s["by_channel"])
check("按状态分组存在", "sent" in s["by_status"] and "ignored" in s["by_status"])
check("回复率为 0-100 的数值", 0 <= s["reply_rate"] <= 100)
check("平均响应时长已计算", s["avg_response_min"] is not None)

# ═══════════ 汇总 ═══════════
print("\n" + "=" * 52)
print(f"  通过 {len(PASS)} 项，失败 {len(FAIL)} 项")
if FAIL:
    print("  失败项：" + "、".join(FAIL))
print("=" * 52 + "\n")
sys.exit(1 if FAIL else 0)
