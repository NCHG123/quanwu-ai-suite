# -*- coding: utf-8 -*-
"""crm.py — CRM 业务层：阶段流转、查询、导出（复用 db.py）"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db


def query(stage=None, country=None):
    """查线索，支持按 stage / country 过滤"""
    return db.get_leads(stage=stage, country=country)


def advance_stage(lead_id, stage):
    """推进线索阶段（new→contacted→won→lost），返回是否成功"""
    exists = any(l["id"] == lead_id for l in query())
    if exists:
        db.update_stage(lead_id, stage)
    return exists


def export(path="leads_export.csv"):
    """导出 CSV，返回导出行数"""
    return db.export_csv(path)


def stats():
    """统计各 stage 数量分布"""
    dist = {}
    for l in query():
        s = l.get("stage", "new")
        dist[s] = dist.get(s, 0) + 1
    return dist
