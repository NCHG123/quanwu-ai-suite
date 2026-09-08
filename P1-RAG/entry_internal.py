# -*- coding: utf-8 -*-
"""entry_internal.py — 内部业务员入口（权限 internal，可看全部）。
模拟工厂业务员查价格/折扣/成本等内部信息。"""
from retriever import build_index, search
from llm import answer

chunks, embs = build_index()
print("=== 内部业务员入口（可检索全部资料）=== q 退出")

while True:
    q = input("\n业务员提问：").strip()
    if q.lower() == "q":
        break
    if not q:
        continue
    results = search(q, chunks, embs, clearance="internal")
    print("\n" + answer(q, results, lang="zh") + "\n")
