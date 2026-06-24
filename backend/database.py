from __future__ import annotations

import sqlite3
from pathlib import Path

from config import DATABASE_PATH


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT DEFAULT '',
    file_name TEXT NOT NULL,
    total_chapters INTEGER DEFAULT 0,
    total_sections INTEGER DEFAULT 0,
    cover_emoji TEXT DEFAULT '📖',
    description TEXT DEFAULT '',
    status TEXT DEFAULT 'processing',
    error_message TEXT DEFAULT '',
    raw_text TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chapters (
    id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    chapter_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    raw_text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sections (
    id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    section_index INTEGER NOT NULL,
    section_in_chapter INTEGER NOT NULL,
    raw_text TEXT NOT NULL,
    content_json TEXT,
    status TEXT DEFAULT 'pending',
    error_message TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reading_progress (
    book_id TEXT PRIMARY KEY REFERENCES books(id) ON DELETE CASCADE,
    current_section_index INTEGER DEFAULT 0,
    current_position TEXT DEFAULT 'start',
    last_read_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS quiz_results (
    id TEXT PRIMARY KEY,
    section_id TEXT NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    quiz_type TEXT NOT NULL,
    question_index INTEGER NOT NULL,
    user_answer INTEGER NOT NULL,
    is_correct INTEGER NOT NULL,
    answered_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS insight_cards (
    id TEXT PRIMARY KEY,
    section_id TEXT NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    next_review_at TEXT,
    ease_factor REAL DEFAULT 2.5,
    interval_days INTEGER DEFAULT 0,
    repetitions INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chapters_book ON chapters(book_id, chapter_index);
CREATE INDEX IF NOT EXISTS idx_sections_book ON sections(book_id, section_index);
CREATE INDEX IF NOT EXISTS idx_sections_chapter ON sections(chapter_id, section_in_chapter);
CREATE INDEX IF NOT EXISTS idx_quiz_section ON quiz_results(section_id);
CREATE INDEX IF NOT EXISTS idx_insight_book ON insight_cards(book_id);
CREATE INDEX IF NOT EXISTS idx_insight_review ON insight_cards(next_review_at);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)

