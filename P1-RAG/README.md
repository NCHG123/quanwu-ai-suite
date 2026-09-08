# P1-RAG · 企业级知识库问答

对外提供 `/ask` 接口，对内做权限隔离，是整个系统的**事实来源**——所有 Agent 生成内容前都要先查它。

## 跑起来

```bash
uvicorn api:app --port 8000
```

验证：打开 <http://127.0.0.1:8000/demo>

## 关键文件

| 文件 | 职责 |
|---|---|
| `retriever.py` | 切块、向量化、检索、**权限过滤** |
| `llm.py` | 调用 DeepSeek 生成答案，含防幻觉约束 |
| `api.py` | FastAPI 接口：`/ask`、`/widget.js`、`/demo` |
| `entry_external.py` / `entry_internal.py` | 对客 / 内部两套检索入口（不同 audience 标签） |
| `docs/` | 17 篇知识库语料（产品、材质、认证、物流、商务条款、内部定价…） |
| `widget.js` | 9.7KB 纯 JS 网站挂件，一行代码嵌入客户官网 |

## 两个核心设计

**1. 权限过滤在检索前做，不是生成后检查**

```python
# retriever.py：切块时打 audience 标签，检索时先过滤候选集
allowed = [i for i, c in enumerate(chunks) if c["audience"] in permit]
```

内部文档（如成本价、内部定价逻辑）根本不会进入 prompt。这是架构级防护，
不依赖「请 LLM 不要泄露」这类随时可能被绕过的 prompt 约束。

**2. 防幻觉：给 LLM 一条「合法的不知道话术」**

`llm.py` 在 prompt 里明确规定：查不到就回复固定话术。而这条话术在 P3 评测里
会被**反向 grep** —— 如果在本该答出来的问题上出现，直接判 fail。
prompt 设计与评测标准是配套的，不是各写各的。
