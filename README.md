# 全屋定制出海 · AI 获客数字员工平台

> 一条海外线索从「社媒出现」到「AI 写好英文接待话术」的全自动链路，人工只需点确认。

面向**定制衣柜 / 全屋定制厂商出海**场景的 AI Agent 系统。5 个子系统覆盖
`RAG 知识库 → 多 Agent 协作 → 自动化评测 → 采集与 CRM → 平台整合与部署` 全链路。

不是低代码平台拖拽配置：**Agent 编排循环手写、评测体系自建、Docker 实跑部署**。

---

## 一、架构总览

```
                    ┌─────────────────────────────────────┐
                    │   P5 平台整合层  (FastAPI :8500)     │
                    │  统一 UI / 跨服务编排 / CSV 导出      │
                    └──────────────┬──────────────────────┘
                                   │ HTTP
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼────────┐      ┌──────────▼─────────┐      ┌────────▼────────┐
│ P1 企业 RAG     │◄─────┤ P2 多 Agent 获客矩阵 │      │ P4 采集与 CRM    │
│ 知识库 (:8000)  │ 检索  │      (:8001)       │      │  SQLite + MCP   │
│ 权限过滤+防幻觉 │      │ 内容/运营/销售三Agent│      └────────┬────────┘
└────────┬───────┘      └──────────┬──────────┘               │
         │                          │ 黑板模式共享 leads.json   │
         │      ┌───────────────────┴─────────────────────────┘
         │      │
┌────────▼──────▼─────────┐
│ P3 质量评测体系           │  8 项指标 / 正反用例 / 回归检测
└─────────────────────────┘
```

| 子系统 | 端口 | 技术要点 | 实测结果 |
|---|---|---|---|
| **P1-RAG** 企业级知识库 | 8000 | 多语言向量化、结构感知切块、**检索前权限过滤**、跨语言查询、DeepSeek 生成 | 17 篇文档建索引；recall@3 = 1.0；中文提问命中英文文档；内部资料泄露率 0 |
| **P2-Agents** 获客矩阵 | 8001 | 手写三 Agent 编排、**黑板模式**共享状态、意图路由检索、异步任务 + 进度轮询 | 3 平台营销帖 + 11 条线索识别 + 11 封英文话术，端到端 60–90 秒 |
| **P3-Eval** 质量评测 | — | 8 项量化指标、正向+反向用例、baseline 回归检测、成本与延迟监控 | 17 个用例全绿，0 回归 |
| **P4-Collect** 采集与 CRM | — | SQLite 唯一索引去重、策略模式可插拔数据源、定时任务、**4 个 MCP 工具** | 14 条线索去重入库，幂等采集 |
| **P5-Platform** 平台部署 | 8500 | FastAPI + 原生单页应用、跨服务 HTTP 编排、Docker 容器化 | Docker Desktop + WSL2 实跑通过，支持 CSV 导出 |

---

## 二、五分钟跑起来

### 0. 准备

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # 然后填入你的 DEEPSEEK_API_KEY
```

> 首次启动会自动下载 BGE-M3 向量模型（约 1.2GB）。国内网络建议先设：
> `export HF_ENDPOINT=https://hf-mirror.com`（Windows: `set HF_ENDPOINT=https://hf-mirror.com`）

### 1. 起 RAG 知识库（P1）

```bash
cd P1-RAG
uvicorn api:app --port 8000
```

验证：打开 <http://127.0.0.1:8000/demo> —— 左下角是调试面板，右下角是模拟官网挂件。

### 2. 起获客矩阵（P2）

```bash
cd P2-Agents
python service.py
```

### 3. 起整合平台（P5）

```bash
cd P5-Platform
uvicorn app:app --port 8500
```

验证：打开 <http://127.0.0.1:8500> —— 点「运行获客闭环」，会看到进度条 0% → 100%。

### 4. 跑质量评测（P3，需 P1 在跑）

```bash
cd P3-Eval
python run_eval.py
```

### 5. 跑采集与 CRM（P4）

```bash
cd P4-Collect
python scheduler.py      # 定时采集，线索自动去重入库
python mcp_server.py     # 以 MCP 工具形式对外提供能力
```

### 一键 Docker（仅 P5）

```bash
cd P5-Platform
docker build -t quanwu-platform .
docker run -p 8500:8500 -e ACQUIRE_API_URL=http://host.docker.internal:8001 quanwu-platform
```

---

## 三、关键设计决策

| 决策 | 怎么做 | 为什么 |
|---|---|---|
| **防幻觉** | 所有 Agent 生成前**先查 RAG 拿事实**，prompt 明令不得编造 | 外贸场景编一个 MOQ 或认证，客户会直接投诉 |
| **权限隔离** | 切块时打 `audience` 标签，**检索阶段就过滤**候选集 | 内部文档根本不进 prompt，是架构级防护，不是靠 prompt 求 LLM |
| **Agent 协作** | **黑板模式**（共享 JSON 状态），Agent 之间不互相调用 | 可单独重跑某一个、可中途插入新 Agent、失败时状态不丢 |
| **长任务体验** | 闭环 85 秒 → 改「立即返回 task_id + 前台 2 秒轮询进度」 | 浏览器不再假死，用户实时看到进度 |
| **质量可验证** | prompt 里规定的「不知道」话术，在评测里**反向 grep 判 fail** | 把主观的话术质量变成可自动判定的布尔值 |

### 8 项评测指标

`recall@3` / `MRR` / `答案准确率` / `泄露率` / `语言正确率` / `意图准确率` / `延迟` / `成本`
—— 质量 6 项 + 成本性能 2 项。企业上线不能只看准不准，还要看贵不贵、快不快。

### temperature 为什么要分开设

| Agent | temperature | 原因 |
|---|---|---|
| 内容 Agent（写营销帖） | 0.7 | 需要创意和表达多样 |
| 运营 Agent（识别线索意图） | 0 | 要稳定可复现的判断 |

---

## 四、目录结构

```
quanwu-ai-suite/
├── P1-RAG/            # 知识库：api.py / retriever.py / llm.py / docs(17篇) / widget.js
├── P2-Agents/         # 获客矩阵：orchestrator.py / service.py / agents(3) / crawlers(5)
├── P3-Eval/           # 评测：run_eval.py / eval_dataset.json / evaluators(3)
├── P4-Collect/        # 采集CRM：db.py / collector.py / mcp_server.py / scheduler.py
├── P5-Platform/       # 平台：app.py / Dockerfile / integrations(3)
├── .env.example       # 环境变量模板（.env 已被 gitignore）
└── requirements.txt   # 统一依赖
```

**网站聊天挂件**：客户官网一行代码即可接入，访客提问走 RAG 回答，留资直接进 CRM：

```html
<script src="http://你的域名:8000/widget.js"
        data-lead="http://你的域名:8001/api/inbox"
        data-color="#1a5f7a"
        data-lang="en"></script>
```

支持品牌色配置、中英双语、表单化留资（姓名 / 邮箱 / 需求）。

---

## 五、已知局限（不藏着）

诚实说明边界，这些也是后续的优化方向：

1. **检索评测样本量小**：recall@3 = 1.0 基于 5 条用例，所以配了 MRR 和反向用例一起看，样本量不足以支撑强结论。
2. **销售 Agent 串行调用**：11 条线索 = 11 次 LLM 串行调用，端到端 60–90 秒。优化方向是批量合并 prompt 或并发，可降到 15 秒左右。当前串行是为了便于调试与限流。
3. **数据源依赖第三方 API**：Apollo / Hunter 客户端已实现（填 key 即用），未填 key 时走种子数据兜底，UI 会明确标注数据来源，不冒充真实抓取结果。
4. **未做过模型训练**：本项目的能力边界是 LLM 应用工程（调用 / 编排 / 评测 / 部署），向量模型使用开源的 BGE-M3。

---

## 六、技术栈

Python ｜ FastAPI ｜ SentenceTransformers (BGE-M3) ｜ DeepSeek API ｜ SQLite ｜
MCP (Model Context Protocol) ｜ APScheduler ｜ Docker ｜ NumPy ｜ Requests

---

## 七、说明

- `.env` 已在 `.gitignore` 中排除，**不会**上传任何 API Key
- 首次运行会自动创建 `leads.db` 与各类运行产物，同样已排除
- 各子系统可独立运行，也可组合成完整闭环
