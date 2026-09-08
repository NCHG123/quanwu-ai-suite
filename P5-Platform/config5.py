# -*- coding: utf-8 -*-
"""config5.py — 项目5配置（环境变量化，兼容本地直跑与容器部署）"""
import os

# 项目1 RAG API：本地直跑用 127.0.0.1，容器内用 host.docker.internal 连宿主机
RAG_API_URL = os.environ.get("RAG_API_URL", "http://127.0.0.1:8000/ask")

# 项目4 采集库：本地为绝对路径，容器内由挂载点 /data/leads.db 注入
LEADS_DB_PATH = os.environ.get("LEADS_DB_PATH", r"C:\Users\Administrator\quanwu-ai-collect\leads.db")
