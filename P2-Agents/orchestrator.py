# -*- coding: utf-8 -*-
"""orchestrator.py — 端到端编排：内容→运营→销售 三段顺序执行"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.content_agent import run as content_run
from agents.ops_agent import run as ops_run
from agents.sales_agent import run as sales_run
import state.leads as leads_state


def reset_crm():
    """把 leads.json 重置为空，保证每次跑都是干净闭环"""
    with open(leads_state.LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump({"leads": []}, f, ensure_ascii=False, indent=2)


def main():
    print("==== 项目2 端到端获客闭环 ====")
    reset_crm()

    print("\n[1/3 内容Agent 产出获客帖]")
    content_run()

    print("\n[2/3 运营Agent 识别线索]")
    ops_run()

    print("\n[3/3 销售Agent 接待线索]")
    sales_run()

    leads = leads_state.load_leads()
    contacted = sum(1 for l in leads if l["stage"] == "contacted")
    print("\n==== 闭环结果 ====")
    print(f"内容产出 3 帖 / 识别线索 {len(leads)} 条 / 接待 {contacted} 条 / 最终阶段分布: {{contacted: {contacted}}}")


if __name__ == "__main__":
    main()
