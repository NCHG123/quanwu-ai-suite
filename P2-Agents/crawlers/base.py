# -*- coding: utf-8 -*-
"""crawlers/base.py — 爬虫基类与统一接口

所有爬虫返回统一的 RawLead 结构，让 service.py 不需要关心数据来源。
"""
from __future__ import annotations
import os
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any

BASE = Path(__file__).resolve().parent.parent


@dataclass
class RawLead:
    """爬虫抓到的原始线索，service.py 把它转成 inbox 消息格式"""
    source: str             # e.g. "Apollo.io", "Hunter.io", "Curated Seed"
    contact: str            # e.g. "John Smith (VP Procurement @ Acme)"
    text: str               # 模拟的社交媒体短消息（≤200 词）
    company: str = ""
    country: str = ""
    url: str = ""
    meta: Dict[str, Any] = None

    def to_inbox(self) -> Dict[str, Any]:
        """转成现有 inbox.json 的消息结构"""
        return {
            "source": self.source,
            "contact": self.contact,
            "text": self.text,
        }


class BaseCrawler:
    """所有爬虫继承这个，统一接口"""

    #: 爬虫唯一名（用于 env 配置与 UI 展示）
    name: str = "base"

    def is_enabled(self) -> bool:
        """该爬虫当前是否可用（按环境变量判断）"""
        return False

    def fetch(self, query: str, limit: int = 5) -> List[RawLead]:
        """抓取线索。返回 RawLead 列表（≤limit 条）。失败抛异常。"""
        raise NotImplementedError

    def status(self) -> Dict[str, Any]:
        """UI 展示用：name / enabled / 提示"""
        return {"name": self.name, "enabled": self.is_enabled()}


def get_enabled_crawlers() -> List[BaseCrawler]:
    """根据 .env 的 CRAWLERS 顺序返回启用的爬虫实例"""
    # 延迟导入避免循环
    from .apollo_crawler import ApolloCrawler
    from .hunter_crawler import HunterCrawler
    from .seed_crawler import SeedCrawler

    available = {
        "apollo": ApolloCrawler(),
        "hunter": HunterCrawler(),
        "seed": SeedCrawler(),
    }
    raw = os.getenv("CRAWLERS", "seed").strip()
    order = [s.strip().lower() for s in raw.split(",") if s.strip()]
    # 永远把 seed 放最后（兜底）；用户配置的顺序决定优先
    ordered_names = [n for n in order if n in available and n != "seed"]
    if "seed" in available and ("seed" in order or not ordered_names):
        ordered_names.append("seed")
    return [available[n] for n in ordered_names]


def all_crawler_status() -> List[Dict[str, Any]]:
    """UI 面板展示用：列出所有爬虫 + 是否启用"""
    from .apollo_crawler import ApolloCrawler
    from .hunter_crawler import HunterCrawler
    from .seed_crawler import SeedCrawler
    out = []
    for c in [ApolloCrawler(), HunterCrawler(), SeedCrawler()]:
        st = c.status()
        st["description"] = {
            "apollo": "Apollo.io B2B 联系人搜索（需 APOLLO_API_KEY）",
            "hunter": "Hunter.io 按域名挖邮箱（需 HUNTER_API_KEY）",
            "seed":   "精选种子线索（无需 key，开箱即用）",
        }.get(c.name, "")
        out.append(st)
    return out
