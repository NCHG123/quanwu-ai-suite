# -*- coding: utf-8 -*-
"""test_mcp.py — 验证 4 个 MCP 工具可调通（降级方案：直接调函数）"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mcp_server  # 导入会触发 db.init_db()


def main():
    print("=== 工具1 query_crm ===")
    leads = mcp_server.query_crm()
    print(f"query_crm() -> {len(leads)} 条线索")
    if leads:
        print(f"  首条: {leads[0].get('source')} | {leads[0].get('contact')} | {leads[0].get('country')}")

    print("\n=== 工具2 search_leads ===")
    results = mcp_server.search_leads("cabinet buyer UAE", 20)
    print(f"search_leads('cabinet buyer UAE', 20) -> {len(results)} 条（触发采集+入库）")

    print("\n=== 工具3 add_lead ===")
    ok = mcp_server.add_lead({"source": "Web", "contact": "test@x.com", "company": "Test Co", "country": "UK", "text": "want quote for 50 kitchens"})
    print(f"add_lead(test@x.com) -> {ok}")
    uk = mcp_server.query_crm(country="UK")
    print(f"query_crm(country='UK') -> {len(uk)} 条（含新增 Test Co）")

    print("\n=== 工具4 export_csv ===")
    n = mcp_server.export_csv("test_export.csv")
    print(f"export_csv('test_export.csv') -> {n} 行")

    print("\n=== 汇总 ===")
    print(f"库内总数: {len(mcp_server.query_crm())}")


if __name__ == "__main__":
    main()
