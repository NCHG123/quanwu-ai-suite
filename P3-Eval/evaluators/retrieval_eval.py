# -*- coding: utf-8 -*-
"""retrieval_eval.py — 检索评测：本地跑 retriever.search，算 recall@3 / MRR / 权限 / 跨语言"""
import json
import sys

PROJECT1_ROOT = r"C:\Users\Administrator\quanwu-ai"
PROJECT1_DOCS = PROJECT1_ROOT + r"\docs"
sys.path.insert(0, PROJECT1_ROOT)

import retriever


def check_retrieval(case, chunks, embs):
    """对单个检索 case 判 pass/fail，返回结果 dict"""
    results = retriever.search(case["question"], chunks, embs,
                               clearance=case["clearance"], top_k=3)
    srcs = [r["file"] for r in results]
    top_score = results[0]["score"] if results else 0.0
    is_contains = "expect_source_contains" in case
    ok = False
    rank = None
    if is_contains:
        target = case["expect_source_contains"]
        targets = target if isinstance(target, list) else [target]
        ok = any(t in s for t in targets for s in srcs)
        for i, s in enumerate(srcs):
            if any(t in s for t in targets):
                rank = i + 1
                break
    else:
        target = case["expect_source_NOT_contains"]
        ok = all(target not in s for s in srcs)
    return {"id": case["id"], "ok": ok, "srcs": srcs, "top_score": top_score,
            "rank": rank, "is_contains": is_contains}


def run():
    with open("eval_dataset.json", encoding="utf-8") as f:
        dataset = json.load(f)
    chunks, embs = retriever.build_index(PROJECT1_DOCS)
    cases = dataset["retrieval_cases"]
    results = [check_retrieval(c, chunks, embs) for c in cases]
    passed = sum(1 for r in results if r["ok"])
    print("=== 检索评测 (R1~R5) ===")
    for r in results:
        print(f"{r['id']} | {'pass' if r['ok'] else 'fail'} | 来源: {r['srcs']} | 最高分: {r['top_score']:.3f}")
    recall = passed / len(results) if results else 0
    contains = [r for r in results if r["is_contains"]]
    mrr = sum((1.0 / r["rank"] if r["rank"] else 0.0) for r in contains) / len(contains) if contains else 0.0
    print(f"\nretrieval_recall@3 = {passed}/{len(results)} = {recall:.2f}")
    print(f"MRR = {mrr:.3f}")


if __name__ == "__main__":
    run()
