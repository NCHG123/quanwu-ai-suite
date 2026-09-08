# -*- coding: utf-8 -*-
"""collector.py — 采集：SearchProvider 抽象 + MockProvider + 解析清洗 + 批量入库"""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db
from config import BASE

SEED_PATH = BASE / "data" / "seed_leads.json"


class SearchProvider:
    """搜索 provider 抽象：真实 API 与 Mock 实现互换，业务代码不感知来源"""
    def search(self, query, limit=20):
        raise NotImplementedError


class MockProvider(SearchProvider):
    """读 seed_leads.json 模拟搜索结果（国内可跑，零网络依赖）"""
    def search(self, query, limit=20):
        with open(SEED_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data[:limit]


def classify_intent(text):
    t = text.lower()
    if any(k in t for k in ("quote", "price", "moq", "order")):
        return "quote"
    if any(k in t for k in ("certification", "compliance")):
        return "info"
    if any(k in t for k in ("partner", "distributor", "agent")):
        return "partner"
    return "none"


def parse(raw):
    """把原始 dict 抽成 leads 表结构字段"""
    source = raw.get("source", "")
    contact = raw.get("contact", "")
    text = raw.get("text", "")
    now = datetime.now().isoformat()
    return {
        "id": hashlib.md5(f"{source}:{contact}".encode("utf-8")).hexdigest()[:8],
        "source": source,
        "contact": contact,
        "company": raw.get("company", ""),
        "country": raw.get("country", ""),
        "intent": classify_intent(text),
        "stage": "new",
        "summary": text[:80],
        "raw_text": text,
        "collected_at": now,
        "updated_at": now,
    }


def collect(query, limit=20):
    """search → parse → upsert（唯一索引去重），返回新增条数"""
    provider = MockProvider()
    raws = provider.search(query, limit)
    new_count = 0
    for r in raws:
        lead = parse(r)
        if db.upsert_lead(lead):
            new_count += 1
    return new_count
