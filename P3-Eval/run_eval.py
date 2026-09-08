# -*- coding: utf-8 -*-
"""run_eval.py — 主入口：跑全部用例，输出 8 指标 + 报告 JSON"""
import json
import os
import sys
from datetime import datetime

PROJECT1_ROOT = r"C:\Users\Administrator\quanwu-ai"
PROJECT1_DOCS = PROJECT1_ROOT + r"\docs"
sys.path.insert(0, PROJECT1_ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import retriever
from evaluators import retrieval_eval, answer_eval, agent_eval


def estimate_cost(q, a):
    """粗略估算单次调用成本（美元）。token 按 4 字符≈1 token 估，DeepSeek 大致价"""
    in_tok = max(1, len(q) // 4)
    out_tok = max(1, len(a) // 4)
    return in_tok * 0.27 / 1e6 + out_tok * 1.10 / 1e6


def main():
    with open("eval_dataset.json", encoding="utf-8") as f:
        dataset = json.load(f)

    chunks, embs = retriever.build_index(PROJECT1_DOCS)

    # 1. 检索
    ret_results = [retrieval_eval.check_retrieval(c, chunks, embs) for c in dataset["retrieval_cases"]]
    recall = sum(1 for r in ret_results if r["ok"]) / len(ret_results)
    contains = [r for r in ret_results if r["is_contains"]]
    mrr = sum((1.0 / r["rank"] if r["rank"] else 0.0) for r in contains) / len(contains) if contains else 0.0

    # 2. 答案 + 语言
    a_cases = dataset["answer_cases"]
    l_cases = dataset["language_cases"]
    a_results = [answer_eval.check_answer(c) for c in a_cases]
    l_results = [answer_eval.check_answer(c) for c in l_cases]
    answer_accuracy = sum(1 for r in a_results if r["ok"]) / len(a_results)
    public_leak = [r for r in a_results if r["leak_checked"]]
    leak_rate = sum(1 for r in public_leak if r["leaked"]) / len(public_leak) if public_leak else 0.0
    lang_correct = sum(1 for r in l_results if r["ok"]) / len(l_results)
    latencies = [r["latency_ms"] for r in a_results + l_results if r["latency_ms"] is not None]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    costs = [estimate_cost(c["question"], r["answer"]) for c, r in zip(a_cases + l_cases, a_results + l_results)]
    avg_cost = sum(costs) / len(costs) if costs else 0.0

    # 3. 意图 + S1
    intent_correct, intent_results = agent_eval.eval_intent(dataset["intent_cases"])
    intent_accuracy = intent_correct / len(dataset["intent_cases"])
    s1 = agent_eval.eval_agent_case(dataset["agent_cases"][0]) if dataset.get("agent_cases") else None

    metrics = {
        "retrieval_recall@3": round(recall, 3),
        "mrr": round(mrr, 3),
        "answer_accuracy": round(answer_accuracy, 3),
        "internal_leak_rate": round(leak_rate, 3),
        "reply_lang_correct": round(lang_correct, 3),
        "intent_accuracy": round(intent_accuracy, 3),
        "avg_latency_ms": round(avg_latency, 1),
        "avg_cost_usd": round(avg_cost, 6),
    }

    print("==== 项目3 评测报告（8 指标）====")
    for k, v in metrics.items():
        print(f"{k} = {v}")
    if s1:
        print(f"\nS1（销售Agent MOQ）: {'pass' if s1['ok'] else 'fail'} | 含参数: {s1['all_present']} | 含confirming: {s1['confirming']}")

    # diff baseline（回归检测）
    baseline_path = os.path.join("reports", "baseline.json")
    if os.path.exists(baseline_path):
        with open(baseline_path, encoding="utf-8") as f:
            base_metrics = json.load(f)["metrics"]
        up_good = ["retrieval_recall@3", "mrr", "answer_accuracy", "reply_lang_correct", "intent_accuracy"]
        down_good = ["internal_leak_rate"]
        regressions = []
        print("\n==== diff vs baseline ====")
        for k, v in metrics.items():
            bv = base_metrics.get(k)
            if bv is None:
                print(f"{k}: {v} (baseline 无此指标)")
                continue
            delta = round(v - bv, 6)
            reg = (k in up_good and v < bv) or (k in down_good and v > bv)
            if reg:
                regressions.append(k)
            flag = " ⚠️ regression" if reg else ""
            print(f"{k}: {bv} -> {v} ({'+' if delta >= 0 else ''}{delta}){flag}")
        print(f"\nregression 数 = {len(regressions)}" + ("（无回归 ✅）" if not regressions else f"（回归项: {regressions}）"))

    os.makedirs("reports", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("reports", f"run_{ts}.json")
    report = {"timestamp": ts, "metrics": metrics, "s1": s1,
              "cases": {"retrieval": ret_results, "answer": a_results,
                        "language": l_results, "intent": intent_results}}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n报告已写入: {path}")


if __name__ == "__main__":
    main()
