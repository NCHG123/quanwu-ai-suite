# -*- coding: utf-8 -*-
"""agent_eval.py — 意图分类准确率 + 销售Agent MOQ链路评测（S1）"""
import json
import sys

PROJECT2_ROOT = r"C:\Users\Administrator\quanwu-ai-agent"
sys.path.insert(0, PROJECT2_ROOT)

from agents.ops_agent import classify_lead
from agents.sales_agent import draft_reply


def eval_intent(cases):
    correct = 0
    results = []
    for case in cases:
        r = classify_lead(case["text"])
        actual = r.get("intent", "none")
        ok = (actual == case["expected_intent"])
        if ok:
            correct += 1
        results.append({"text": case["text"], "expected": case["expected_intent"],
                        "actual": actual, "ok": ok})
    return correct, results


def eval_agent_case(case):
    """跑 S1：走销售Agent draft_reply，检查 MOQ 是否直接答出（非 confirming）"""
    lead = case["lead"]
    reply = draft_reply(lead)
    must = case["expected_must_contain"]
    all_present = all(k in reply for k in must)
    reply_lower = reply.lower()
    confirming = ("confirming with colleagues" in reply_lower) or ("confirming with my colleagues" in reply_lower)
    ok = all_present and (not confirming if case.get("expected_not_confirming") else True)
    return {"id": case["id"], "ok": ok, "all_present": all_present,
            "confirming": confirming, "reply": reply}


def run():
    with open("eval_dataset.json", encoding="utf-8") as f:
        dataset = json.load(f)
    correct, results = eval_intent(dataset["intent_cases"])
    print("=== 意图分类评测 (intent_cases) ===")
    for r in results:
        print(f"{'pass' if r['ok'] else 'fail'} | 预期: {r['expected']} | 实际: {r['actual']} | {r['text'][:40]}")
    print(f"intent_accuracy = {correct}/{len(results)} = {correct / len(results):.2f}")

    print()
    print("=== 销售Agent MOQ链路 (S1) ===")
    if dataset.get("agent_cases"):
        r = eval_agent_case(dataset["agent_cases"][0])
        print(f"S1 | {'pass' if r['ok'] else 'fail'} | 含参数: {r['all_present']} | 含confirming: {r['confirming']}")


if __name__ == "__main__":
    run()
