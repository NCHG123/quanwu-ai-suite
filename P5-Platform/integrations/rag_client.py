# -*- coding: utf-8 -*-
"""rag_client.py — 调用项目1 RAG API"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
import config5


def ask(question: str) -> dict:
    """向项目1 RAG API 提问，返回 {answer, sources, scores}"""
    resp = requests.post(config5.RAG_API_URL, json={"question": question}, timeout=30)
    resp.raise_for_status()
    return resp.json()
