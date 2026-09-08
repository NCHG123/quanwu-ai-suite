# -*- coding: utf-8 -*-
"""sales_agent.py — 销售Agent：读线索→查事实→生成英文接待话术→回写CRM"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.rag_client import rag_ask
from config.llm_client import complete
from state.leads import load_leads, update_lead


def research_question(intent, summary):
    """根据意图决定要先查哪些事实"""
    if intent == "quote":
        return "What is your exact MOQ for a trial order, and what is the standard container load (40HQ)?"
    elif intent == "info":
        return ("What certifications (CARB P2 / TSCA / FSC / CE / E1) and product "
                "capabilities do you have? " + summary)
    else:
        return "What is your MOQ, production lead time, and product capabilities?"


def draft_reply(lead):
    """查事实 + 生成个性化英文接待话术"""
    q = research_question(lead["intent"], lead["summary"])
    facts, _ = rag_ask(q)  # 项目1已修英文，返回英文事实
    prompt = f"""根据下面的【事实资料】，为这位客户写一封英文接待话术。

【客户称呼】{lead['contact']}
【客户意图】{lead['intent']}
【线索摘要】{lead['summary']}

【事实资料】
{facts}

要求：
1. 用客户称呼自然开场
2. 只基于事实资料里的真实参数（MOQ、认证、交期、付款等），不得编造
3. 专业 B2B 语气，结尾引导下一步（如 share your project specs / request a formal quote）
4. 只输出话术正文，不要任何解释"""
    return complete(prompt, lang="en")


def run():
    """读新线索，逐条生成话术并回写 CRM"""
    leads = load_leads()
    pending = [l for l in leads if l["stage"] == "new"]
    for l in pending:
        reply = draft_reply(l)
        print(f"── 线索 {l['id']} {l['contact']} ──")
        print(reply)
        print()
        update_lead(l["id"], stage="contacted", draft=reply)
    print(f"共接待 {len(pending)} 条线索")


if __name__ == "__main__":
    run()
