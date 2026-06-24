from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, HTTPException

from database import get_connection
from models import QuizSubmitRequest


router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.post("/submit")
def submit_quiz(payload: QuizSubmitRequest):
    with get_connection() as conn:
        section = conn.execute(
            """
            SELECT id, content_json, status
            FROM sections
            WHERE id = ?
            """,
            (payload.section_id,),
        ).fetchone()
        if not section:
            raise HTTPException(status_code=404, detail="小节不存在")
        if section["status"] != "ready" or not section["content_json"]:
            raise HTTPException(status_code=400, detail="小节尚未处理完成")

        content = json.loads(section["content_json"])
        question = _get_question(content, payload.quiz_type, payload.question_index)
        if payload.user_answer >= len(question["options"]):
            raise HTTPException(status_code=400, detail="选项不存在")

        correct_answer = int(question["correct"])
        is_correct = payload.user_answer == correct_answer
        conn.execute(
            """
            INSERT INTO quiz_results (
                id, section_id, quiz_type, question_index, user_answer, is_correct
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                f"quiz_{uuid.uuid4().hex}",
                payload.section_id,
                payload.quiz_type,
                payload.question_index,
                payload.user_answer,
                1 if is_correct else 0,
            ),
        )

    return {
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "explanation": question["explanation"],
    }


def _get_question(content: dict, quiz_type: str, question_index: int) -> dict:
    if quiz_type == "inline":
        if question_index != 0:
            raise HTTPException(status_code=400, detail="内嵌测验只有一道题")
        return content["inline_quiz"]

    questions = content.get("section_quiz", [])
    if question_index >= len(questions):
        raise HTTPException(status_code=400, detail="题目不存在")
    return questions[question_index]

