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


---

## 社媒私信接入（2026-09-09 新增）

把企业社媒账号收到的咨询统一接住、分类、起草、人工放行、统计。



### 文件

| 文件 | 作用 |
|---|---|
| `channels/base.py` | 渠道抽象层 + 合规红线声明 |
| `channels/meta.py` | Instagram/Facebook + WhatsApp 适配器 |
| `channels/tiktok.py` | TikTok（需官方商务申请） |
| `channels/linkedin.py` | LinkedIn（需 Partner 权限） |
| `channels/youtube.py` | YouTube 公开评论（YouTube 无私信） |
| `channels/aggregator.py` | 聚合通道兜底 + Mock |
| `social.py` | 流水线：分类/转线索/起草/审核/统计 |
| `webhook_server.py` | 零依赖 webhook 服务（标准库） |
| `web_ui.html` | 人工审核台 |
| `test_social.py` | 端到端冒烟测试 |

### 与采集的关系

`collector.py` 主动出去找线索（拉），`social.py` 接住主动来询（推），
两者汇入同一张 `leads` 表，下游 Agent 无感知来源。

### 合规

只处理用户主动发给**本企业自有账号**的消息，只采集**公开可见**的企业资料。
不实现绕过登录抓取、抓取他人私信、批量群发、伪造身份。
