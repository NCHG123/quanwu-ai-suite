# -*- coding: utf-8 -*-
"""crm_store.py — 直读项目4采集库（跨项目只读），平台不持有数据"""
import sqlite3
from config5 import LEADS_DB_PATH


def _conn():
    # mode=ro：只读连接，不影响采集系统写入，避免锁冲突
    return sqlite3.connect(f"file:{LEADS_DB_PATH}?mode=ro", uri=True)


def get_leads(stage=None, country=None):
    sql = "SELECT * FROM leads WHERE 1=1"
    params = []
    if stage:
        sql += " AND stage = ?"
        params.append(stage)
    if country:
        sql += " AND country = ?"
        params.append(country)
    conn = _conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def stats():
    dist = {}
    for l in get_leads():
        s = l.get("stage", "new")
        dist[s] = dist.get(s, 0) + 1
    return dist
