# -*- coding: utf-8 -*-
"""crm_writer.py — 写回项目4采集库（阶段推进），与 crm_store 对称"""
import sqlite3
from config5 import LEADS_DB_PATH

VALID_STAGES = {"new", "contacted", "won", "lost"}


def advance_stage(lead_id, stage):
    if stage not in VALID_STAGES:
        return {"ok": False, "error": f"invalid stage: {stage}"}
    conn = sqlite3.connect(f"file:{LEADS_DB_PATH}?mode=rw", uri=True)
    try:
        conn.execute("PRAGMA busy_timeout=3000")  # 等采集写入释放锁，防 SQLITE_BUSY
        cur = conn.execute(
            "UPDATE leads SET stage=?, updated_at=datetime('now') WHERE id=?",
            (stage, lead_id),
        )
        conn.commit()
        return {"ok": cur.rowcount > 0, "lead_id": lead_id, "stage": stage}
    finally:
        conn.close()
