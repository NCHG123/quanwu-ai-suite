# -*- coding: utf-8 -*-
"""retriever.py — 知识库引擎：加载/切块/向量化/双权限检索。
对外入口与对内入口共用本文件。"""
import os
import re
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from openai import OpenAI

BASE = Path(__file__).resolve().parent
DOCS_DIR = BASE / "docs"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
TOP_K = 5

load_dotenv(BASE / ".env")

_llm_client = None


def _get_llm_client():
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"),
                             base_url="https://api.deepseek.com")
    return _llm_client


def translate_query_if_cn(q):
    """含中文的 query 用 DeepSeek 翻成英文；纯英文原样返回"""
    if not re.search(r"[一-鿿]", q):
        return q
    resp = _get_llm_client().chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "把下面的中文问题翻译成英文，只输出翻译结果，不要任何解释。"},
            {"role": "user", "content": q},
        ],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()


_model = None

def _get_model():
    """模型只加载一次，全局复用"""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def _audience(filename: str, text: str = "") -> str:
    """文件名含 internal，或内容含 INTERNAL 标记（INTERNAL-ONLY / AUDIENCE LEVEL: INTERNAL）= 内部"""
    if "internal" in filename.lower():
        return "internal"
    tl = text.lower()
    if "internal-only" in tl or "audience level: internal" in tl:
        return "internal"
    return "public"

def build_index(docs_dir=None, min_len=50):
    """读文档 → 带章节标题切块 → 打权限标签 → 向量化。返回 (chunks, embs)"""
    chunks = []
    d = Path(docs_dir) if docs_dir else DOCS_DIR
    for file in sorted(d.glob("*.md")):
        text = file.read_text(encoding="utf-8")
        aud = _audience(file.name, text)
        heading = ""
        for para in text.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            if para.startswith("#"):
                heading = para
                continue
            if len(para) > min_len:
                text_field = f"[{heading}] {para}" if heading else para
                chunks.append({
                    "file": file.name,
                    "audience": aud,
                    "text": text_field,
                })
    embs = _get_model().encode([c["text"] for c in chunks], show_progress_bar=False)
    n_internal = sum(1 for c in chunks if c["audience"] == "internal")
    print(f"[index] 共 {len(chunks)} 块（internal {n_internal} 块）")
    return chunks, embs

def search(question, chunks, embs, clearance="public", top_k=TOP_K):
    """检索。clearance="internal" 可看全部；clearance="public" 只搜公开块。"""
    question = translate_query_if_cn(question)
    allowed = [i for i, c in enumerate(chunks)
               if clearance == "internal" or c["audience"] == "public"]
    if not allowed:
        return []
    q_vec = _get_model().encode([question])
    scores = embs[allowed] @ q_vec.T
    order = np.argsort(scores, axis=0)[::-1][:top_k].flatten()
    out = []
    for pos in order:
        gi = allowed[pos]
        out.append({**chunks[gi], "score": float(scores[pos][0])})
    return out
