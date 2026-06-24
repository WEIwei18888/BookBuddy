from __future__ import annotations

import json
import re
import time
from pathlib import Path

from openai import OpenAI

from config import AI_MODE, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from models import SectionContent
from prompts.book_info import BOOK_INFO_SYSTEM, BOOK_INFO_USER
from prompts.generate_section import SECTION_SYSTEM, SECTION_USER
from prompts.split_chapters import CHAPTER_SPLIT_SYSTEM, CHAPTER_SPLIT_USER


def call_deepseek(
    system_prompt: str,
    user_prompt: str,
    expect_json: bool = True,
    max_retries: int = 3,
    temperature: float = 0.7,
) -> dict | str:
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY is required when AI_MODE=deepseek")

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3 if attempt > 0 else temperature,
                "max_tokens": 4096,
            }
            if expect_json:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            if not expect_json:
                return content

            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            return json.loads(cleaned)
        except Exception as exc:
            last_error = exc
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
                continue
    raise RuntimeError(f"DeepSeek 调用失败：{last_error}")


def extract_book_info(file_name: str, full_text: str) -> dict:
    if AI_MODE != "deepseek":
        title = Path(file_name).stem.replace("_", " ").replace("-", " ").strip() or "未命名书籍"
        return {
            "title": title,
            "author": "",
            "cover_emoji": "📘",
            "description": "把这本书拆成一段轻松、有节奏的阅读旅程。",
        }

    result = call_deepseek(
        BOOK_INFO_SYSTEM,
        BOOK_INFO_USER.format(file_name=file_name, first_3000_chars=full_text[:3000]),
        expect_json=True,
    )
    return {
        "title": str(result.get("title") or Path(file_name).stem),
        "author": str(result.get("author") or ""),
        "cover_emoji": str(result.get("cover_emoji") or "📖"),
        "description": str(result.get("description") or ""),
    }


def extract_chapters(full_text: str) -> list[dict]:
    if AI_MODE != "deepseek":
        return _mock_extract_chapters(full_text)

    result = call_deepseek(
        CHAPTER_SPLIT_SYSTEM,
        CHAPTER_SPLIT_USER.format(full_text=full_text[:120_000]),
        expect_json=True,
    )
    chapters = result.get("chapters", []) if isinstance(result, dict) else []
    return [
        {
            "title": str(ch.get("title") or f"第 {index + 1} 章"),
            "first_sentence": str(ch.get("first_sentence") or ""),
        }
        for index, ch in enumerate(chapters)
        if isinstance(ch, dict)
    ]


def generate_section_content(
    book_title: str,
    chapter_title: str,
    section_number: int,
    total_sections: int,
    is_last_section: bool,
    previous_recap: str,
    section_text: str,
) -> SectionContent:
    if AI_MODE != "deepseek":
        return _mock_section_content(
            book_title,
            chapter_title,
            section_number,
            total_sections,
            is_last_section,
            previous_recap,
            section_text,
        )

    payload = call_deepseek(
        SECTION_SYSTEM,
        SECTION_USER.format(
            book_title=book_title,
            chapter_title=chapter_title,
            section_number=section_number,
            total_sections=total_sections,
            is_last_section="是" if is_last_section else "否",
            previous_recap=previous_recap or "无",
            section_text=section_text,
        ),
        expect_json=True,
        temperature=0.7,
    )
    return SectionContent.model_validate(payload)


def _mock_extract_chapters(full_text: str) -> list[dict]:
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    pattern = re.compile(r"^(第[一二三四五六七八九十百千万\d]+[章节篇部].{0,40}|Chapter\s+\d+.{0,40}|\d+[.、]\s*.{1,40})$")
    chapters = []
    for index, line in enumerate(lines):
        if pattern.match(line):
            first_sentence = _first_sentence_from_lines(lines[index + 1 :]) or line
            chapters.append({"title": line[:80], "first_sentence": first_sentence})

    if chapters:
        return chapters[:80]

    approx_size = 6000
    chapters = []
    for start in range(0, len(full_text), approx_size):
        chunk = full_text[start : start + approx_size].strip()
        if not chunk:
            continue
        chapters.append(
            {
                "title": f"第 {len(chapters) + 1} 章",
                "first_sentence": _first_sentence(chunk),
            }
        )
    return chapters or [{"title": "正文", "first_sentence": _first_sentence(full_text)}]


def _mock_section_content(
    book_title: str,
    chapter_title: str,
    section_number: int,
    total_sections: int,
    is_last_section: bool,
    previous_recap: str,
    section_text: str,
) -> SectionContent:
    sentences = _sentences(section_text)
    lead = sentences[0] if sentences else section_text[:90]
    second = sentences[1] if len(sentences) > 1 else lead
    third = sentences[2] if len(sentences) > 2 else second
    keyword = _keyword_from_text(section_text)
    previous_hint = f"接着上节的脉络，" if previous_recap else ""
    bridge = (
        "这已经是最后一节了，可以回头看看哪些观点最值得带走。"
        if is_last_section
        else "下一节会继续把这个线索往前推，看看它在更具体的场景里会变成什么。"
    )
    payload = {
        "hook": f"{previous_hint}这一节最值得留意的问题是：{keyword}为什么会影响我们理解这本书？",
        "content_cards": [
            {
                "type": "concept",
                "content": f"先抓住核心：{lead} 这句话可以当成本节的入口，它提示我们不要只看表面结论。",
                "emoji": "🧠",
            },
            {
                "type": "example",
                "content": f"可以把它想成一次日常选择：你不是先拥有完整答案，再开始行动；很多时候是边看见线索，边修正判断。",
                "emoji": "💡",
            },
            {
                "type": "comparison",
                "content": f"很多人读到这里会急着找一个确定答案，但作者更像是在提醒我们：真正重要的是看清问题如何形成。",
                "emoji": "⚖️",
            },
            {
                "type": "quote",
                "content": second[:180],
                "emoji": "📖",
            },
            {
                "type": "concept",
                "content": f"换句话说，{keyword}不是孤立知识点，而是一条连接前后内容的线索。理解它，后面的观点会顺很多。",
                "emoji": "🧩",
            },
            {
                "type": "highlight",
                "content": f"本节最重要的收获：读书时不要只记结论，要记住作者为什么会走到这个结论。",
                "emoji": "⭐",
            },
        ],
        "inline_quiz": {
            "position": 3,
            "question": "根据刚才的内容，读这一节时最应该关注什么？",
            "options": ["只背下原文句子", "理解观点背后的推理线索", "跳过例子直接看结尾"],
            "correct": 1,
            "explanation": "这一节的价值在于把观点和推理连起来，而不是机械记忆。",
        },
        "section_quiz": [
            {
                "question": "这一节的核心阅读方式更接近哪一种？",
                "options": ["寻找唯一标准答案", "抓住作者的推理路径", "只看故事是否精彩", "只记录陌生词"],
                "correct": 1,
                "explanation": "理解推理路径能帮助你把本节内容迁移到新的场景。",
            },
            {
                "question": "如果你想把本节内容用在生活里，最合适的做法是？",
                "options": ["把关键词写下来就结束", "找一个自己的例子验证这个观点", "只保存截图", "等读完全书再回想"],
                "correct": 1,
                "explanation": "自己的例子会让抽象观点变得可记、可用。",
            },
        ],
        "reflection": f"回想最近一次你改变看法的经历：当时是哪个线索让你开始重新判断？",
        "insight_cards": [
            {
                "front": keyword[:10] or "核心线索",
                "back": f"它指向本节的中心问题：如何从零散内容里看见作者真正想推进的观点。",
            }
        ],
        "bridge": bridge,
        "recap": f"这一节围绕「{keyword}」展开。关键不是记住每句话，而是看清作者如何通过例子和判断把观点一步步搭起来。",
    }
    return SectionContent.model_validate(payload)


def _first_sentence_from_lines(lines: list[str]) -> str:
    for line in lines:
        sentence = _first_sentence(line)
        if sentence:
            return sentence
    return ""


def _first_sentence(text: str) -> str:
    sentences = _sentences(text)
    return sentences[0] if sentences else text[:80].strip()


def _sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.strip())
    parts = re.split(r"(?<=[。！？!?；;])", normalized)
    return [part.strip() for part in parts if len(part.strip()) >= 8]


def _keyword_from_text(text: str) -> str:
    candidates = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,12}", text)
    stop_words = {"但是", "所以", "因为", "如果", "我们", "他们", "一个", "这种", "这个", "就是"}
    for candidate in candidates:
        if candidate not in stop_words:
            return candidate
    return "核心观点"

