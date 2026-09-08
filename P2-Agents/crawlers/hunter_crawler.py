# -*- coding: utf-8 -*-
"""crawlers/hunter_crawler.py — Hunter.io 按域名挖邮箱

端点：GET https://api.hunter.io/v2/domain-search?domain=...&api_key=...
返回 emails 列表 → 映射成 RawLead（一个邮箱一条）。
需要环境变量 HUNTER_API_KEY（hunter.io 控制台申请）。
"""
import os
import json
import urllib.request
import urllib.error
import urllib.parse
from typing import List
from .base import BaseCrawler, RawLead


class HunterCrawler(BaseCrawler):
    name = "hunter"

    def is_enabled(self) -> bool:
        return bool(os.getenv("HUNTER_API_KEY", "").strip())

    def status(self) -> dict:
        s = super().status()
        s["needs_key"] = "HUNTER_API_KEY"
        return s

    def fetch(self, query: str, limit: int = 5) -> List[RawLead]:
        api_key = os.getenv("HUNTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("HUNTER_API_KEY 未配置")

        # query 这里被当作域名（如 houzz.com）或公司名（当 company）
        q = query.strip()
        domain = q if "." in q else ""
        company = "" if domain else q
        params = {
            "domain": domain,
            "company": company,
            "limit": str(min(int(limit), 10)),
            "api_key": api_key,
        }
        url = "https://api.hunter.io/v2/domain-search?" + urllib.parse.urlencode({k: v for k, v in params.items() if v})
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Hunter API HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')[:200]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Hunter API 连接失败: {e.reason}")

        data = payload.get("data") or {}
        org = data.get("organization") or ""
        dom = data.get("domain") or domain
        emails = data.get("emails") or []
        leads: List[RawLead] = []
        for e in emails[:limit]:
            fn = (e.get("first_name") or "").strip()
            ln = (e.get("last_name") or "").strip()
            name = f"{fn} {ln}".strip() or e.get("value", "contact")
            pos = e.get("position") or ""
            contact = f"{name} ({pos} @ {org})".strip()
            value = e.get("value") or ""
            confidence = e.get("confidence")
            text_parts = [f"Found via Hunter: {pos or 'contact'} at {org or dom}."]
            if value:
                text_parts.append(f"Email {value} (confidence {confidence}%).")
            text_parts.append("Sourcing custom wardrobe / closet for residential project.")
            leads.append(RawLead(
                source="Hunter.io",
                contact=contact,
                text=" ".join(text_parts)[:400],
                company=org,
                country=(data.get("country") or ""),
                url=f"https://{dom}" if dom else "",
                meta={"email": value, "confidence": confidence, "hunter_id": e.get("_id")},
            ))
        return leads
