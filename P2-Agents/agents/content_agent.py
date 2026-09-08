# -*- coding: utf-8 -*-
"""content_agent.py — 内容Agent：查事实 + 按平台生成营销帖"""
import sys
from pathlib import Path

# 把项目根目录加入 sys.path，使 config 可导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.rag_client import rag_ask
from config.llm_client import complete


# 三个平台风格
PLATFORM_STYLES = {
    "Instagram": "视觉生活方式短文案，轻松口语化，结尾加 3-5 个 hashtag",
    "LinkedIn": "专业 B2B 风格，数据驱动，面向海外开发商/装修公司，强调整装能力",
    "Facebook": "社区信任向，结尾抛一个问题引导评论互动",
}

# 三个角度 → 要查的事实（问题）
ANGLE_QUERIES = {
    "quality": "What board materials and hardware brands do you use for your cabinets?",
    "compliance": "What certifications do you have for the US and EU markets?",
    "capability": "What product lines can you supply (kitchen, wardrobe, vanity, solid wood)?",
}

# 角度 → 对应平台
ANGLE_PLATFORM = {
    "quality": "Instagram",
    "compliance": "LinkedIn",
    "capability": "Facebook",
}


def research(angle):
    """调 rag_ask 查事实，返回 (answer, sources)"""
    question = ANGLE_QUERIES[angle]
    return rag_ask(question)


def generate_post(platform, angle, facts):
    """调 complete 生成该平台英文帖"""
    style = PLATFORM_STYLES[platform]
    prompt = f"""根据下面的【事实资料】，为 {platform} 平台写一条英文营销帖。

【平台风格】{style}
【内容角度】{angle}

【事实资料】
{facts}

要求：
1. 只输出帖子正文，不要任何解释、标题或前缀
2. 必须严格基于事实资料，不得编造任何参数（认证、材料、规格、数字等）
3. 用英文输出"""
    return complete(prompt, lang="en", temperature=0.7)


def run_return():
    """三个角度 × 对应平台，各生成 1 条帖子，返回结构化列表"""
    posts = []
    for angle, platform in ANGLE_PLATFORM.items():
        answer, sources = research(angle)
        post = generate_post(platform, angle, answer)
        posts.append({"angle": angle, "platform": platform, "sources": sources, "post": post})
    return posts


def run():
    """CLI 版：打印三帖（服务版用 run_return 拿结构化数据）"""
    for p in run_return():
        print("=" * 60)
        print(f"角度：{p['angle']}   →   平台：{p['platform']}")
        print("=" * 60)
        print(f"[事实来源] {', '.join(p['sources'])}")
        print()
        print(p["post"])
        print()


if __name__ == "__main__":
    run()
