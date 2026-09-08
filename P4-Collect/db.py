# -*- coding: utf-8 -*-
"""db.py — SQLite 数据层：建表 + CRUD + 去重（source+contact 唯一索引）"""
import csv
import sqlite3
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
  id           TEXT PRIMARY KEY,
  source       TEXT NOT NULL,
  contact      TEXT NOT NULL,
  company      TEXT,
  country      TEXT,
  intent       TEXT,
  stage        TEXT DEFAULT 'new',
  summary      TEXT,
  raw_text     TEXT,
  collected_at TEXT,
  updated_at   TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_lead_uniq ON leads(source, contact);
"""

COLUMNS = ["id", "source", "contact", "company", "country", "intent",
           "stage", "summary", "raw_text", "collected_at", "updated_at"]


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """建表 + 唯一索引（source+contact 去重）"""
    with _conn() as conn:
        conn.executescript(SCHEMA)


def upsert_lead(lead):
    """INSERT OR IGNORE（source+contact 去重），返回是否新插入"""
    placeholders = ", ".join("?" * len(COLUMNS))
    with _conn() as conn:
        cur = conn.execute(
            f"INSERT OR IGNORE INTO leads ({', '.join(COLUMNS)}) VALUES ({placeholders})",
            [lead.get(c) for c in COLUMNS],
        )
        return cur.rowcount > 0


def get_leads(stage=None, country=None):
    """查询线索，返回 list[dict]"""
    sql = "SELECT * FROM leads WHERE 1=1"
    params = []
    if stage is not None:
        sql += " AND stage = ?"
        params.append(stage)
    if country is not None:
        sql += " AND country = ?"
        params.append(country)
    conn = _conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_stage(lead_id, stage):
    """更新线索阶段"""
    with _conn() as conn:
        conn.execute(
            "UPDATE leads SET stage = ?, updated_at = datetime('now') WHERE id = ?",
            (stage, lead_id),
        )


def export_csv(path):
    """导出全表为 CSV，返回导出行数"""
    leads = get_leads()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(leads)
    return len(leads)
