from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile

from config import (
    MAX_EXTRACTED_TEXT_CHARS,
    MAX_UPLOAD_SIZE_BYTES,
    MIN_EXTRACTED_TEXT_CHARS,
)
from database import get_connection
from services.pdf_service import extract_text_from_pdf
from services.processing import process_book


router = APIRouter(prefix="/api/books", tags=["books"])


@router.post("/upload")
async def upload_book(file: UploadFile, background_tasks: BackgroundTasks):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持上传 PDF 文件")

    file_name = Path(file.filename).name
    size = 0
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_path = temp_file.name
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(status_code=400, detail="文件大小不能超过 50MB")
                temp_file.write(chunk)

        raw_text = extract_text_from_pdf(temp_path)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"PDF 解析失败：{exc}") from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
        await file.close()

    if len(raw_text) < MIN_EXTRACTED_TEXT_CHARS:
        raise HTTPException(status_code=400, detail="这本 PDF 可能是扫描版或图片版，暂不支持")
    if len(raw_text) > MAX_EXTRACTED_TEXT_CHARS:
        raise HTTPException(status_code=400, detail="这本书太长了，建议分册上传")

    book_id = f"book_{uuid.uuid4().hex}"
    title = Path(file_name).stem or "未命名书籍"
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO books (id, title, file_name, raw_text, status)
            VALUES (?, ?, ?, ?, 'processing')
            """,
            (book_id, title, file_name, raw_text),
        )

    background_tasks.add_task(process_book, book_id)
    return {"book_id": book_id, "title": title, "status": "processing"}


@router.get("")
def list_books():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT b.id, b.title, b.author, b.cover_emoji, b.description,
                   b.status, b.error_message, b.total_sections, b.created_at,
                   COALESCE(p.current_section_index, 0) AS current_section_index,
                   COALESCE(p.current_position, 'start') AS current_position,
                   p.last_read_at
            FROM books b
            LEFT JOIN reading_progress p ON p.book_id = b.id
            ORDER BY b.created_at DESC
            """
        ).fetchall()
    return [_book_summary(row) for row in rows]


@router.get("/{book_id}")
def get_book(book_id: str):
    with get_connection() as conn:
        book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")

        progress = conn.execute(
            """
            SELECT current_section_index, current_position, last_read_at
            FROM reading_progress
            WHERE book_id = ?
            """,
            (book_id,),
        ).fetchone()
        chapters = conn.execute(
            """
            SELECT id, title, chapter_index
            FROM chapters
            WHERE book_id = ?
            ORDER BY chapter_index
            """,
            (book_id,),
        ).fetchall()
        sections = conn.execute(
            """
            SELECT id, chapter_id, section_index, section_in_chapter, status
            FROM sections
            WHERE book_id = ?
            ORDER BY section_index
            """,
            (book_id,),
        ).fetchall()

    sections_by_chapter: dict[str, list[dict]] = {}
    for section in sections:
        sections_by_chapter.setdefault(section["chapter_id"], []).append(
            {
                "id": section["id"],
                "section_index": section["section_index"],
                "section_in_chapter": section["section_in_chapter"],
                "status": section["status"],
            }
        )

    progress_payload = _progress_payload(progress)
    payload = dict(book)
    payload["raw_text"] = ""
    payload["progress"] = progress_payload
    payload["read_sections"] = _read_sections(
        book["total_sections"],
        progress_payload["current_section_index"],
        progress_payload["current_position"],
    )
    payload["chapters"] = [
        {
            "id": chapter["id"],
            "title": chapter["title"],
            "chapter_index": chapter["chapter_index"],
            "section_count": len(sections_by_chapter.get(chapter["id"], [])),
            "sections": sections_by_chapter.get(chapter["id"], []),
        }
        for chapter in chapters
    ]
    return payload


@router.delete("/{book_id}")
def delete_book(book_id: str):
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="书籍不存在")
    return {"success": True}


def _book_summary(row) -> dict:
    read_sections = _read_sections(
        row["total_sections"],
        row["current_section_index"],
        row["current_position"],
    )
    return {
        "id": row["id"],
        "title": row["title"],
        "author": row["author"],
        "cover_emoji": row["cover_emoji"],
        "description": row["description"],
        "status": row["status"],
        "error_message": row["error_message"],
        "total_sections": row["total_sections"],
        "read_sections": read_sections,
        "last_read_at": row["last_read_at"],
        "created_at": row["created_at"],
    }


def _progress_payload(progress) -> dict:
    if not progress:
        return {
            "current_section_index": 0,
            "current_position": "start",
            "last_read_at": None,
        }
    return {
        "current_section_index": progress["current_section_index"],
        "current_position": progress["current_position"],
        "last_read_at": progress["last_read_at"],
    }


def _read_sections(total_sections: int, current_section_index: int, position: str) -> int:
    if total_sections <= 0:
        return 0
    completed = current_section_index + (1 if position == "complete" else 0)
    if position != "complete":
        completed = current_section_index
    return max(0, min(total_sections, completed))

