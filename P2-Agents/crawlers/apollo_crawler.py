# -*- coding: utf-8 -*-
"""crawlers/apollo_crawler.py — Apollo.io 真实 B2B 线索抓取

端点：POST https://api.apollo.io/v1/mixed_people/search
返回 people 列表 → 映射成 RawLead。
需要环境变量 APOLLO_API_KEY（apollo.io 控制台申请）。
"""
import os
import json
import urllib.request
import urllib.error
from typing import List
from .base import BaseCrawler, RawLead


class ApolloCrawler(BaseCrawler):
    name = "apollo"

    def is_enabled(self) -> bool:
        return bool(os.getenv("APOLLO_API_KEY", "").strip())

    def status(self) -> dict:
        s = super().status()
        s["needs_key"] = "APOLLO_API_KEY"
        return s

    def fetch(self, query: str, limit: int = 5) -> List[RawLead]:
        api_key = os.getenv("APOLLO_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("APOLLO_API_KEY 未配置")

        body = {
            "api_key": api_key,
            "q_keywords": query,
            "person_titles": ["owner", "founder", "ceo", "procurement", "buyer", "general contractor"],
            "page": 1,
            "per_page": min(int(limit), 25),
        }
        req = urllib.request.Request(
            "https://api.apollo.io/v1/mixed_people/search",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Apollo API HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')[:200]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Apollo API 连接失败: {e.reason}")

        people = payload.get("people") or payload.get("contacts") or []
        leads: List[RawLead] = []
        for p in people[:limit]:
            first = (p.get("first_name") or "").strip()
            last = (p.get("last_name") or "").strip()
            name = f"{first} {last}".strip() or "Anonymous"
            title = (p.get("title") or "").strip()
            org = p.get("organization") or {}
            org_name = org.get("name") or "Unknown Co"
            domain = org.get("primary_domain") or org.get("website_url") or ""
            country = (p.get("country") or org.get("country") or "").strip()
            email = (p.get("email") or "").strip()
            contact = f"{name} ({title} @ {org_name})".replace(" () ", " ").strip()
            text_parts = [
                f"Found via Apollo: {title} at {org_name}, {country}.".strip(),
            ]
            if email:
                text_parts.append(f"Direct email: {email}.")
            text_parts.append(
                f"Reaching out to explore custom wardrobe / closet opportunities for our export catalogue."
            )
            leads.append(RawLead(
                source="Apollo.io",
                contact=contact,
                text=" ".join(text_parts)[:400],
                company=org_name,
                country=country,
                url=f"https://{domain}" if domain else "",
                meta={"email": email, "title": title, "apollo_id": p.get("id")},
            ))
        return leads
