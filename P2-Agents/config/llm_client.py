# -*- coding: utf-8 -*-
"""llm_client.py — 本地 LLM 调用（内容生成用），区别于 rag_client 走 HTTP"""
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# 读项目根目录的 .env（无论从哪个目录运行）
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SYSTEM_PROMPT = "你是全屋定制工厂的海外B2B营销文案"


def complete(prompt, lang="en", temperature=0.7):
    """调用 DeepSeek 生成文本，返回回答文本"""
    lang_name = "中文" if lang == "zh" else "英文"
    system = f"{SYSTEM_PROMPT}。请用{lang_name}输出。"
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content
