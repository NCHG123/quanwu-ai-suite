# -*- coding: utf-8 -*-
"""api.py — 对外 RAG 接口（权限固定 public）+ 网站挂件分发"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import retriever
import llm

BASE = Path(__file__).resolve().parent

app = FastAPI(title="全屋定制 RAG 对外接口")

# 挂件会被嵌到客户自己的域名下，必须允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# 启动时构建索引（模块级，只建一次）
chunks, embs = retriever.build_index()


class AskReq(BaseModel):
    question: str


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(req: AskReq):
    results = retriever.search(req.question, chunks, embs, clearance="public")
    answer = llm.answer(req.question, results, lang="en")
    return {
        "answer": answer,
        "sources": [c["file"] for c in results],
        "scores": [c["score"] for c in results],
    }


@app.get("/widget.js")
def widget():
    """给客户网站嵌入的聊天挂件。客户只需：
       <script src="http://你的域名:8000/widget.js"
               data-lead="http://你的域名:8001/api/inbox"></script>
    """
    return FileResponse(BASE / "widget.js", media_type="application/javascript")


@app.get("/demo", response_class=FileResponse)
def demo():
    """模拟企业官网，验证挂件嵌入效果"""
    return FileResponse(BASE / "demo.html", media_type="text/html; charset=utf-8")
