# -*- coding: utf-8 -*-
"""ops_agent.py — 运营Agent：从社媒消息里识别线索（信号识别）"""
import sys
import json
import re
from pathlib import Path

# 项目根目录加入 sys.path，使 config/state 可导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.llm_client import complete
from state.leads import load_leads, save_lead

BASE = Path(__file__).resolve().parent.parent
INBOX_FILE = BASE / "data" / "inbox.json"


def fetch_inbox():
    """读 data/inbox.json，返回消息列表（含 id/source/platform/contact/text）"""
    with open(INBOX_FILE, encoding="utf-8") as f:
        data = json.load(f)
    messages = []
    for i, m in enumerate(data["messages"]):
        source = m["source"]
        platform = source.split(" ")[0]  # "Instagram comment" -> "Instagram"
        messages.append({
            "id": "M%03d" % (i + 1),
            "source": source,
            "platform": platform,
            "contact": m["contact"],
            "text": m["text"],
        })
    return messages


def classify_lead(text):
    """调 LLM 判断消息意图，返回 {"intent":..., "summary":...}"""
    prompt = f"""判断下面这条海外B端客户的社媒消息的意图，并给一句英文摘要。

消息内容：
{text}

意图类别（只选一个）：
- quote：询价（想要报价、价格）
- info：了解产品、认证、MOQ等信息
- complaint：投诉
- spam：垃圾广告、引流
- none：闲聊、纯夸赞、无意向

只输出一个 JSON 对象，不要任何其他文字，格式：
{{"intent":"<类别>","summary":"<一句英文摘要>"}}"""
    raw = complete(prompt, lang="en", temperature=0)
    m = re.search(r'\{.*\}', raw, re.DOTALL)  # 处理可能的 ```json 包裹
    if m:
        raw = m.group(0)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"intent": "none", "summary": "分类失败"}


def run():
    """遍历 inbox，识别意图，把 quote/info 存进 leads.json"""
    messages = fetch_inbox()
    saved_count = 0
    print("=== 运营Agent：识别社媒消息意图 ===")
    for msg in messages:
        result = classify_lead(msg["text"])
        intent = result.get("intent", "none")
        summary = result.get("summary", "")
        should_save = intent in ("quote", "info")
        if should_save:
            save_lead({
                "source": msg["source"],
                "contact": msg["contact"],
                "intent": intent,
                "stage": "new",
                "summary": summary,
            })
            saved_count += 1
        mark = "入库" if should_save else "跳过"
        print(f"{msg['contact']} | {intent} | {mark} | {summary}")

    print()
    print(f"本次识别线索 {saved_count} 条")
    print()
    print("=== 当前 leads.json ===")
    print(json.dumps(load_leads(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run()
