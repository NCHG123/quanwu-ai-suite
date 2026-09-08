# -*- coding: utf-8 -*-
"""scheduler.py — APScheduler 定时调度：按间隔自动采集入库"""
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
import db
import collector
from apscheduler.schedulers.background import BackgroundScheduler


def job():
    print(f"[调度触发] {datetime.now().strftime('%H:%M:%S')} 开始采集...")
    n = collector.collect("custom cabinetry leads", 20)
    print(f"  本次新增 {n} 条，库内总数 {len(db.get_leads())}")


def main():
    db.init_db()
    sched = BackgroundScheduler()
    sched.add_job(job, 'interval', seconds=config.SCHEDULE_INTERVAL_SEC)
    sched.start()
    print(f"调度器已启动，每 {config.SCHEDULE_INTERVAL_SEC} 秒采集一次。按 Ctrl+C 退出。")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sched.shutdown()
        print("调度器已停止")


if __name__ == "__main__":
    main()
