# P2-Agents · 多 Agent 获客矩阵

三个 Agent 分工协作，把「发布内容 → 收集线索 → 起草话术」串成自动链路。

## 跑起来

```bash
python service.py          # 监听 :8001
python orchestrator.py     # 命令行跑一次完整闭环
python smoke_test.py       # 冒烟测试
```

## 三个 Agent

| Agent | 干什么 | temperature |
|---|---|---|
| **内容 Agent** | 生成 3 个平台的营销帖 | 0.7（要创意） |
| **运营 Agent** | 从互动里识别线索与意向等级 | 0（要稳定） |
| **销售 Agent** | 按客户类型起草个性化英文话术 | 0.3 |

## 为什么用黑板模式

```
state/leads.py  ──►  leads.json（共享黑板）
                      │
   内容 Agent 写帖 ──►│
   运营 Agent 读帖 ──►│── 写线索
   销售 Agent 读线索 ─►│── 写话术
```

Agent 之间**不互相调用**，只读写共享状态。好处：
- 可以单独重跑某一个 Agent（比如只重跑销售）
- 可以随时插入新 Agent，不用改现有代码
- 中途失败状态不丢，从黑板继续

> 什么情况下该换 Supervisor 模式？当需要**循环 / 协商 / 回退**（比如销售发现线索质量不行，
> 打回给运营重新筛）时。当前是单向数据流，黑板足够且最好调试。

## 可插拔数据源

`crawlers/` 用策略模式统一接口：

| 爬虫 | 状态 |
|---|---|
| `apollo_crawler.py` | 真实 API，填 key 即用 |
| `hunter_crawler.py` | 真实 API，填 key 即用 |
| `seed_crawler.py` | 种子数据兜底（`data/lead_seed.json`，20 条） |

UI 会明确标注数据来源，**不冒充真实抓取结果**。

## 长任务的体验处理

完整闭环约 85 秒，同步接口会让浏览器假死。改成：

```
POST /api/acquire/run  →  立即返回 task_id (202)
GET  /api/acquire/task/<id>  →  每 2 秒轮询，返回 progress / step / eta
GET  /api/acquire/task/<id>/result  →  完成后取结果
```

用户能实时看到 `0% → 15% → 45% → 70% → 100%`。
