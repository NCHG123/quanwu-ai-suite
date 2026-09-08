# -*- coding: utf-8 -*-
"""entry_external.py — 对外客服入口（权限 public，只读公开资料）。
模拟官网聊天挂件 / 销售Agent接待海外B端客户。"""
from retriever import build_index, search
from llm import answer

chunks, embs = build_index()
print("=== 对外客服入口（只读公开资料）=== q 退出")

while True:
    q = input("\n客户问题：").strip()
    if q.lower() == "q":
        break
    if not q:
        continue
    results = search(q, chunks, embs, clearance="public")
    print("\n" + answer(q, results, lang="en") + "\n")
