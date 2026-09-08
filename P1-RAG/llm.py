# -*- coding: utf-8 -*-
"""llm.py — DeepSeek 生成回答。两个入口共用。"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"),
                         base_url="https://api.deepseek.com")
    return _client

def answer(question, results, lang="en"):
    lang_name = "中文" if lang == "zh" else "英文"
    context = "\n\n".join(f"[{c['file']}] (score {c['score']:.2f})\n{c['text']}"
                          for c in results)
    prompt = f"""你是全屋定制工厂的海外业务助理。只根据下面的资料回答问题。
规则：
1. 资料里没有的信息，回答"这个我需要和同事确认后答复您"，绝不编造
2. 数字、型号、认证名称必须与原文一致
3. 回答末尾列出用到的来源文件名
4. 用{lang_name}回答用户。
【资料】
{context}
【问题】{question}"""
    resp = _get_client().chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return resp.choices[0].message.content
