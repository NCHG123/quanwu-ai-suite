# P4-Collect · 线索采集与 CRM（MCP 工具化）

把「采集 → 去重 → 入库 → 导出」做成幂等、可调度的流水线，并以 MCP 工具形式对外暴露。

## 跑起来

```bash
python scheduler.py      # 定时采集（APScheduler）
python mcp_server.py     # 以 MCP 工具形式提供服务
python test_mcp.py       # 测试 MCP 工具调用
```

## 关键文件

| 文件 | 职责 |
|---|---|
| `db.py` | SQLite 建表与连接，`UNIQUE(source, contact)` 去重 |
| `collector.py` | 采集编排，调用可插拔数据源 |
| `crm.py` | CRM 写入逻辑 |
| `mcp_server.py` | 4 个 MCP 工具定义 |
| `scheduler.py` | 定时任务调度 |

## 两个值得说的实现细节

**1. 去重交给数据库约束，不靠代码判断**

```python
UNIQUE(source, contact)
INSERT OR IGNORE ...
```

用代码先 `SELECT` 再 `INSERT` 会有竞态（两个进程同时查到"不存在"）。
交给数据库唯一索引，天然幂等——重复采集不会产生重复数据。

**2. SQLite 并发：必须设 busy_timeout**

```python
conn.execute("PRAGMA busy_timeout=3000")
```

多进程共享同一个 SQLite 文件时，默认会立刻抛 `database is locked`。
设 3 秒等待后，短锁冲突自动重试。

## 关于 MCP

MCP（Model Context Protocol）是 Anthropic 提出的开放协议，可以理解为
**AI 应用的 USB-C**：一次实现，所有支持 MCP 的客户端都能调用。

实现时有个容易忽略的点：**docstring 是功能的一部分**。
LLM 靠函数文档判断「什么时候该调这个工具」，写得含糊会导致工具永远不被调用。
