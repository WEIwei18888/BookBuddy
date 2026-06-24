from __future__ import annotations

from fastapi import APIRouter, HTTPException

from database import get_connection
from models import ProgressUpdate


router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/{book_id}")
def get_progress(book_id: str):
    with get_connection() as conn:
        book = conn.execute("SELECT id FROM books WHERE id = ?", (book_id,)).fetchone()
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

    if not progress:
        return {
            "current_section_index": 0,
            "current_position": "start",
            "last_read_at": None,
        }
    return dict(progress)


@router.put("/{book_id}")
def update_progress(book_id: str, payload: ProgressUpdate):
    with get_connection() as conn:
        book = conn.execute(
            "SELECT total_sections FROM books WHERE id = ?",
            (book_id,),
        ).fetchone()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        if book["total_sections"] and payload.section_index >= book["total_sections"]:
            raise HTTPException(status_code=400, detail="小节序号超出范围")

        conn.execute(
            """
            INSERT INTO reading_progress (book_id, current_section_index, current_position, last_read_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(book_id) DO UPDATE SET
                current_section_index = excluded.current_section_index,
                current_position = excluded.current_position,
                last_read_at = datetime('now')
            """,
            (book_id, payload.section_index, payload.position),
        )
    return {"success": True}

