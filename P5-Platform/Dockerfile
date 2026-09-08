# 项目5 全屋定制 AI 数字员工平台 — 镜像构建
# 适配国内网络：基础镜像走国内镜像源，pip 走清华源，不依赖 daemon 镜像配置
# 切换镜像源：docker build --build-arg BASE_REGISTRY=docker.m.daocloud.io -t quanwu-platform .

ARG BASE_REGISTRY=docker.1panel.live
FROM ${BASE_REGISTRY}/library/python:3.13-slim

# 国内 pip 加速
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV PIP_TRUSTED_HOST=mirrors.aliyun.com

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8500
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8500"]
