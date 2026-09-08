# -*- coding: utf-8 -*-
"""冒烟测试：验证 rag_ask（连项目1 API）和 save_lead（写 leads.json）可用"""
import json
from config import rag_client
from state import leads

# 1. 测 rag_ask（连项目1的 RAG API）
print("=== 测试 rag_ask ===")
answer, sources = rag_client.rag_ask("What is your MOQ?")
print("answer:", answer)
print("sources:", sources)

# 2. 测 save_lead
print()
print("=== 测试 save_lead ===")
lead = leads.save_lead({
    "source": "Instagram comment",
    "contact": "@builder_tx",
    "intent": "quote",
    "stage": "new",
    "summary": "问美式厨房柜 MOQ",
})
print("已保存线索:", lead)

# 3. 确认 leads.json 内容
print()
print("=== leads.json 当前内容 ===")
print(json.dumps(leads.load_leads(), ensure_ascii=False, indent=2))
