# -*- coding: utf-8 -*-
"""rag_client.py — 封装对项目1 RAG API 的调用（Agent 可调用的工具）"""
import requests

RAG_URL = "http://127.0.0.1:8000/ask"


def rag_ask(question):
    """向 RAG API 提问，返回 (answer, sources)"""
    resp = requests.post(RAG_URL, json={"question": question}, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["answer"], data["sources"]
