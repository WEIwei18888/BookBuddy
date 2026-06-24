from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response

from database import get_connection
from services.processing import process_section_and_preload


router = APIRouter(prefix="/api/books/{book_id}/sections", tags=["sections"])


@router.get("/{section_index}")
def get_section(
    book_id: str,
    section_index: int,
    background_tasks: BackgroundTasks,
    response: Response,
    force: bool = False,
):
    if section_index < 0:
        raise HTTPException(status_code=404, detail="小节不存在")

    with get_connection() as conn:
        book = conn.execute(
            "SELECT id, status, total_sections FROM books WHERE id = ?",
            (book_id,),
        ).fetchone()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")

        row = _fetch_section(conn, book_id, section_index)
        if not row:
            if book["status"] == "processing":
                response.status_code = 202
                return {"status": "processing"}
            raise HTTPException(status_code=404, detail="小节不存在")

        if force:
            conn.execute(
                """
                UPDATE sections
                SET status = 'processing', content_json = NULL, error_message = ''
                WHERE book_id = ? AND section_index = ?
                """,
                (book_id, section_index),
            )
            background_tasks.add_task(process_section_and_preload, book_id, section_index)
            response.status_code = 202
            return {"status": "processing"}

        if row["status"] == "ready" and row["content_json"]:
            content = json.loads(row["content_json"])
            return {
                "id": row["id"],
                "section_index": row["section_index"],
                "total_sections": row["total_sections"],
                "chapter_title": row["chapter_title"],
                "content_json": content,
                "status": row["status"],
                "has_next": row["section_index"] + 1 < row["total_sections"],
                "has_prev": row["section_index"] > 0,
            }

        if row["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail={"status": "error", "message": row["error_message"] or "这一节处理失败"},
            )

        if row["status"] == "pending":
            conn.execute(
                """
                UPDATE sections
                SET status = 'processing', error_message = ''
                WHERE book_id = ? AND section_index = ?
                """,
                (book_id, section_index),
            )
            background_tasks.add_task(process_section_and_preload, book_id, section_index)

    response.status_code = 202
    return {"status": "processing"}


@router.get("/{section_index}/status")
def get_section_status(book_id: str, section_index: int):
    with get_connection() as conn:
        book = conn.execute("SELECT status FROM books WHERE id = ?", (book_id,)).fetchone()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        row = conn.execute(
            """
            SELECT status, error_message
            FROM sections
            WHERE book_id = ? AND section_index = ?
            """,
            (book_id, section_index),
        ).fetchone()

    if not row and book["status"] == "processing":
        return {"status": "processing"}
    if not row:
        raise HTTPException(status_code=404, detail="小节不存在")
    return {"status": row["status"], "message": row["error_message"]}


def _fetch_section(conn, book_id: str, section_index: int):
    return conn.execute(
        """
        SELECT s.*, c.title AS chapter_title, b.total_sections
        FROM sections s
        JOIN chapters c ON c.id = s.chapter_id
        JOIN books b ON b.id = s.book_id
        WHERE s.book_id = ? AND s.section_index = ?
        """,
        (book_id, section_index),
    ).fetchone()

