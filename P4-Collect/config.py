# -*- coding: utf-8 -*-
"""config.py — 项目4配置"""
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "leads.db"
SEARCH_PROVIDER = "mock"
SCHEDULE_INTERVAL_SEC = 60
