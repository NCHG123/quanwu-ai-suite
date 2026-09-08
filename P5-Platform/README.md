# P5-Platform · 整合平台与容器化部署

把 P1–P4 串成一个可以给人用的界面，并做容器化交付。

## 跑起来

```bash
uvicorn app:app --port 8500
# 或
docker build -t quanwu-platform .
docker run -p 8500:8500 quanwu-platform
```

打开 <http://127.0.0.1:8500>

## 它做什么

- **统一入口**：一个界面操作 RAG 问答、获客闭环、线索查看
- **跨服务编排**：通过 HTTP 调用 :8000 / :8001，自身不重复实现业务逻辑
- **异步进度展示**：转发 P2 的 task_id，前端轮询显示进度条
- **CSV 导出**：线索一键导出（带 UTF-8 BOM，Excel 打开不乱码）
- **抓取面板**：展示当前数据源与采集结果，标注数据真伪

## 容器化的两个原则

**1. 配置走环境变量（12-factor）**

```bash
docker run -e RAG_API_URL=http://host.docker.internal:8000/ask \
           -e ACQUIRE_API_URL=http://host.docker.internal:8001 ...
```

同一个镜像，本地和容器都能跑，不需要为不同环境打不同镜像。

**2. 业务数据走挂载卷，不进镜像**

数据库、索引、运行产物都不打进镜像——镜像只装代码和依赖。
这样重新部署不会丢失数据，镜像也能保持干净。

## 国内网络适配

`Dockerfile` 已处理：

- 基础镜像走可切换的国内镜像源（`--build-arg BASE_REGISTRY=...`）
- pip 走清华 / 阿里源

```bash
docker build --build-arg BASE_REGISTRY=docker.m.daocloud.io -t quanwu-platform .
```
