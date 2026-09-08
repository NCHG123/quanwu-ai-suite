# -*- coding: utf-8 -*-
"""leads.py — leads.json 读写（CRM 雏形）"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS_FILE = os.path.join(BASE, "leads.json")


def load_leads():
    """读取 leads.json，返回 leads 列表（文件不存在则返回空列表）"""
    if not os.path.exists(LEADS_FILE):
        return []
    with open(LEADS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("leads", [])


def _write(data):
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_lead(lead):
    """新增一条线索，自动生成 id，返回该 lead"""
    leads = load_leads()
    next_id = "L%03d" % (len(leads) + 1)
    lead = {"id": next_id, **lead}
    leads.append(lead)
    _write({"leads": leads})
    return lead


def update_lead(lead_id, **fields):
    """按 id 更新线索字段，返回更新后的 lead（找不到返回 None）"""
    leads = load_leads()
    for lead in leads:
        if lead["id"] == lead_id:
            lead.update(fields)
            _write({"leads": leads})
            return lead
    return None
