# -*- coding: utf-8 -*-
"""crawlers/seed_crawler.py — 精选种子线索（兜底，开箱即用）

读取 data/lead_seed.json 中的预编译海外买家画像，按 query 关键词粗筛。
UI 明确标注来源为「Curated Seed（精选种子）」，非爬虫抓取。
"""
import os
import json
import re
from typing import List
from pathlib import Path
from .base import BaseCrawler, RawLead, BASE


class SeedCrawler(BaseCrawler):
    name = "seed"

    def is_enabled(self) -> bool:
        # 默认兜底，永远启用
        return True

    def status(self) -> dict:
        s = super().status()
        s["needs_key"] = ""
        return s

    def _load_seed(self) -> List[dict]:
        p = BASE / "data" / "lead_seed.json"
        if not p.exists():
            return []
        try:
            data = json.load(open(p, encoding="utf-8"))
            return data.get("leads", []) if isinstance(data, dict) else data
        except Exception:
            return []

    def fetch(self, query: str, limit: int = 5) -> List[RawLead]:
        seed = self._load_seed()
        if not seed:
            raise RuntimeError("data/lead_seed.json 不存在或为空")

        # query 关键词粗筛（国家 / 行业 / 关键词命中越多越靠前）
        q_tokens = [t.lower() for t in re.split(r"[\s,]+", query) if t]
        scored = []
        for entry in seed:
            hay = " ".join([
                str(entry.get("country", "")),
                str(entry.get("industry", "")),
                str(entry.get("company", "")),
                str(entry.get("text", "")),
            ]).lower()
            score = sum(1 for t in q_tokens if t in hay)
            # query 为空时给所有种子同分
            if not q_tokens:
                score = 1
            scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        picked = [e for s, e in scored if s > 0][:limit]
        if not picked:
            picked = [e for _, e in scored][:limit]

        leads: List[RawLead] = []
        for entry in picked:
            leads.append(RawLead(
                source="Curated Seed",
                contact=entry["contact"],
                text=entry["text"],
                company=entry.get("company", ""),
                country=entry.get("country", ""),
                url=entry.get("url", ""),
                meta={"industry": entry.get("industry", "")},
            ))
        return leads
