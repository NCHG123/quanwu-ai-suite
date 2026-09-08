# -*- coding: utf-8 -*-
"""mcp_server.py — FastMCP 封装采集+CRM 为 Agent 可调工具"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.mcpserver import MCPServer
import config
import db
import collector
import crm

mcp = MCPServer("overseas-lead-hub")
db.init_db()


@mcp.tool()
def search_leads(query: str, limit: int = 20) -> list[dict]:
    """采集海外 B 端线索并入库，返回采集到的线索列表。"""
    n = collector.collect(query, limit)
    return crm.query()


@mcp.tool()
def query_crm(stage: str = None, country: str = None) -> list[dict]:
    """按阶段/国家查询 CRM 线索。"""
    return crm.query(stage=stage, country=country)


@mcp.tool()
def add_lead(lead: dict) -> bool:
    """写入一条线索（带 source+contact 去重）。lead 需含 source/contact/company/country/text 等字段。"""
    parsed = collector.parse(lead)
    return db.upsert_lead(parsed)


@mcp.tool()
def export_csv(path: str = "leads_export.csv") -> int:
    """导出全部线索为 CSV，返回行数。"""
    return crm.export(path)


if __name__ == "__main__":
    mcp.run()
