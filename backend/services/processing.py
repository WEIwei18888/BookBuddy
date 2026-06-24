from __future__ import annotations

import json
import re
import uuid

from database import get_connection
from models import SectionContent
from services.ai_service import extract_book_info, extract_chapters, generate_section_content


def process_book(book_id: str) -> None:
    try:
        with get_connection() as conn:
            book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
            if not book:
                return
            conn.execute(
                "UPDATE books SET status = 'processing', error_message = '' WHERE id = ?",
                (book_id,),
            )

        info = extract_book_info(book["file_name"], book["raw_text"])
        chapters_info = extract_chapters(book["raw_text"])
        chapter_texts = split_text_by_chapters(book["raw_text"], chapters_info)
        if not chapter_texts:
            chapter_texts = [{"title": "正文", "text": book["raw_text"]}]

        with get_connection() as conn:
            conn.execute("DELETE FROM chapters WHERE book_id = ?", (book_id,))
            section_index = 0
            total_chapters = len(chapter_texts)
            for chapter_index, chapter in enumerate(chapter_texts):
                chapter_id = f"chapter_{uuid.uuid4().hex}"
                conn.execute(
                    """
                    INSERT INTO chapters (id, book_id, chapter_index, title, raw_text)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (chapter_id, book_id, chapter_index, chapter["title"], chapter["text"]),
                )
                sections = split_chapter_into_sections(chapter["text"])
                for section_in_chapter, section_text in enumerate(sections):
                    conn.execute(
                        """
                        INSERT INTO sections (
                            id, book_id, chapter_id, section_index, section_in_chapter,
                            raw_text, content_json, status, error_message
                        )
                        VALUES (?, ?, ?, ?, ?, ?, NULL, 'pending', '')
                        """,
                        (
                            f"section_{uuid.uuid4().hex}",
                            book_id,
                            chapter_id,
                            section_index,
                            section_in_chapter,
                            section_text,
                        ),
                    )
                    section_index += 1

            conn.execute(
                """
                UPDATE books
                SET title = ?, author = ?, cover_emoji = ?, description = ?,
                    total_chapters = ?, total_sections = ?, status = 'processing',
                    error_message = ''
                WHERE id = ?
                """,
                (
                    info["title"],
                    info["author"],
                    info["cover_emoji"],
                    info["description"],
                    total_chapters,
                    section_index,
                    book_id,
                ),
            )
            conn.execute(
                """
                INSERT INTO reading_progress (book_id, current_section_index, current_position)
                VALUES (?, 0, 'start')
                ON CONFLICT(book_id) DO NOTHING
                """,
                (book_id,),
            )

        for index in range(min(3, section_index)):
            process_section(book_id, index)

        with get_connection() as conn:
            conn.execute(
                "UPDATE books SET status = 'ready', error_message = '' WHERE id = ?",
                (book_id,),
            )
    except Exception as exc:
        with get_connection() as conn:
            conn.execute(
                "UPDATE books SET status = 'error', error_message = ? WHERE id = ?",
                (str(exc), book_id),
            )


def process_section_and_preload(book_id: str, section_index: int) -> None:
    process_section(book_id, section_index)
    with get_connection() as conn:
        next_section = conn.execute(
            """
            SELECT status FROM sections
            WHERE book_id = ? AND section_index = ?
            """,
            (book_id, section_index + 1),
        ).fetchone()
    if next_section and next_section["status"] == "pending":
        process_section(book_id, section_index + 1)


def process_section(book_id: str, section_index: int) -> None:
    try:
        with get_connection() as conn:
            section = conn.execute(
                """
                SELECT s.*, c.title AS chapter_title, b.title AS book_title, b.total_sections
                FROM sections s
                JOIN chapters c ON c.id = s.chapter_id
                JOIN books b ON b.id = s.book_id
                WHERE s.book_id = ? AND s.section_index = ?
                """,
                (book_id, section_index),
            ).fetchone()
            if not section or section["status"] == "ready":
                return
            conn.execute(
                """
                UPDATE sections
                SET status = 'processing', error_message = ''
                WHERE book_id = ? AND section_index = ?
                """,
                (book_id, section_index),
            )

            previous = conn.execute(
                """
                SELECT content_json FROM sections
                WHERE book_id = ? AND section_index = ? AND status = 'ready'
                """,
                (book_id, section_index - 1),
            ).fetchone()
        previous_recap = ""
        if previous and previous["content_json"]:
            try:
                previous_recap = json.loads(previous["content_json"]).get("recap", "")
            except json.JSONDecodeError:
                previous_recap = ""

        content = generate_section_content(
            book_title=section["book_title"],
            chapter_title=section["chapter_title"],
            section_number=section_index + 1,
            total_sections=section["total_sections"],
            is_last_section=section_index + 1 >= section["total_sections"],
            previous_recap=previous_recap,
            section_text=section["raw_text"],
        )
        save_section_content(section["id"], book_id, content)
    except Exception as exc:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE sections
                SET status = 'error', error_message = ?
                WHERE book_id = ? AND section_index = ?
                """,
                (str(exc), book_id, section_index),
            )


def save_section_content(section_id: str, book_id: str, content: SectionContent) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM insight_cards WHERE section_id = ?", (section_id,))
        for card in content.insight_cards:
            conn.execute(
                """
                INSERT INTO insight_cards (id, section_id, book_id, front, back)
                VALUES (?, ?, ?, ?, ?)
                """,
                (f"insight_{uuid.uuid4().hex}", section_id, book_id, card.front, card.back),
            )
        conn.execute(
            """
            UPDATE sections
            SET content_json = ?, status = 'ready', error_message = ''
            WHERE id = ?
            """,
            (content.model_dump_json(), section_id),
        )


def split_text_by_chapters(full_text: str, chapters_info: list[dict]) -> list[dict]:
    positions = []
    seen_starts = set()
    for chapter in chapters_info:
        first_sentence = str(chapter.get("first_sentence") or "").strip()
        title = str(chapter.get("title") or "未命名章节").strip()
        if not first_sentence:
            continue
        pos = full_text.find(first_sentence)
        if pos == -1:
            pos = full_text.find(first_sentence[:15])
        if pos != -1 and pos not in seen_starts:
            seen_starts.add(pos)
            positions.append({"title": title, "start": pos})

    positions.sort(key=lambda item: item["start"])
    if not positions:
        return []

    chapter_texts = []
    for index, position in enumerate(positions):
        start = position["start"]
        end = positions[index + 1]["start"] if index + 1 < len(positions) else len(full_text)
        text = full_text[start:end].strip()
        if text:
            chapter_texts.append({"title": position["title"], "text": text})
    return chapter_texts


def split_chapter_into_sections(
    chapter_text: str,
    min_chars: int = 800,
    max_chars: int = 1500,
) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n", chapter_text) if p.strip()]
    if not paragraphs:
        return [chapter_text.strip()] if chapter_text.strip() else []

    sections = []
    current_section = []
    current_length = 0
    for paragraph in paragraphs:
        paragraph_length = len(paragraph)
        if current_length + paragraph_length > max_chars and current_length >= min_chars:
            sections.append("\n\n".join(current_section))
            current_section = [paragraph]
            current_length = paragraph_length
        else:
            current_section.append(paragraph)
            current_length += paragraph_length

    if current_section:
        last_text = "\n\n".join(current_section)
        if current_length < min_chars // 2 and sections:
            sections[-1] += "\n\n" + last_text
        else:
            sections.append(last_text)

    return sections

