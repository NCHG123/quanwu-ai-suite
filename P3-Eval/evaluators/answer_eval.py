# -*- coding: utf-8 -*-
"""answer_eval.py — 答案评测：public 走 HTTP，internal 走本地，检查参数/泄漏/语言"""
import json
import re
import sys
import time

import requests

PROJECT1_ROOT = r"C:\Users\Administrator\quanwu-ai"
PROJECT1_DOCS = PROJECT1_ROOT + r"\docs"
sys.path.insert(0, PROJECT1_ROOT)

import retriever
import llm

SENSITIVE = ["discount ladder", "-2%", "-3%", "-4%", "-5%", "-8%", "15-pricing"]

chunks, embs = retriever.build_index(PROJECT1_DOCS)


def ask_http(q):
    t0 = time.time()
    resp = requests.post("http://127.0.0.1:8000/ask", json={"question": q}, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["answer"], (time.time() - t0) * 1000


def ask_internal(q):
    results = retriever.search(q, chunks, embs, clearance="internal", top_k=3)
    return llm.answer(q, results, lang="zh")


def has_chinese(s):
    return bool(re.search(r"[\u4e00-\u9fff]", s))


def check_leak(answer):
    a = answer.lower()
    return any(s.lower() in a for s in SENSITIVE)


def check_answer(case):
    """对单个 answer/language case 判 pass/fail，返回结果 dict"""
    cid = case["id"]
    if cid.startswith("A"):
        answer, latency = ask_http(case["question"])
        must = case.get("must_contain", [])
        missing = [k for k in must if k not in answer]
        leaked = False
        leak_checked = bool(case.get("must_not_leak_internal"))
        if leak_checked:
            leaked = check_leak(answer)
        ok = (not missing) and (not leaked)
        return {"id": cid, "ok": ok, "missing": missing, "leaked": leaked,
                "leak_checked": leak_checked, "latency_ms": latency, "answer": answer}
    else:  # L case
        expect_lang = case["expect_lang"]
        if expect_lang == "en":
            answer, latency = ask_http(case["question"])
            actual = "en" if not has_chinese(answer) else "zh"
        else:
            answer = ask_internal(case["question"])
            actual = "zh" if has_chinese(answer) else "en"
            latency = None
        ok = (actual == expect_lang)
        return {"id": cid, "ok": ok, "missing": [], "leaked": False,
                "leak_checked": False, "latency_ms": latency,
                "actual_lang": actual, "answer": answer}


def run():
    with open("eval_dataset.json", encoding="utf-8") as f:
        dataset = json.load(f)
    cases = dataset["answer_cases"] + dataset["language_cases"]
    results = [check_answer(c) for c in cases]
    passed = sum(1 for r in results if r["ok"])
    print("=== 答案/语言评测 (A1~A4, L1~L2) ===")
    for case, r in zip(cases, results):
        if r["id"].startswith("A"):
            print(f"{r['id']} | {'pass' if r['ok'] else 'fail'} | 缺参数: {r['missing'] if r['missing'] else '无'} | 泄漏: {r['leaked']}")
        else:
            print(f"{r['id']} | {'pass' if r['ok'] else 'fail'} | 期望: {case['expect_lang']} | 实际: {r['actual_lang']}")
    print(f"\nanswer/language pass = {passed}/{len(results)}")


if __name__ == "__main__":
    run()
