from __future__ import annotations

import re
from collections import Counter

import fitz


def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    try:
        pages = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                pages.append(text)
    finally:
        doc.close()

    if len(pages) > 5:
        first_lines = [p.split("\n")[0].strip() for p in pages if p.strip()]
        last_lines = [p.strip().split("\n")[-1].strip() for p in pages if p.strip()]
        header_candidates = {
            line
            for line, count in Counter(first_lines).items()
            if line and count > len(pages) * 0.5
        }
        footer_candidates = {
            line
            for line, count in Counter(last_lines).items()
            if line and count > len(pages) * 0.5
        }

        cleaned_pages = []
        for page_text in pages:
            lines = page_text.split("\n")
            if lines and lines[0].strip() in header_candidates:
                lines = lines[1:]
            if lines and lines[-1].strip() in footer_candidates:
                lines = lines[:-1]
            cleaned_pages.append("\n".join(lines))
        pages = cleaned_pages

    full_text = "\n".join(pages)
    full_text = re.sub(r"\n\s*[-—]?\s*\d+\s*[-—]?\s*\n", "\n", full_text)
    full_text = re.sub(r"\n\s*第\s*\d+\s*页\s*\n", "\n", full_text)
    full_text = re.sub(r"([^\n。！？；：])\n([^\n\s])", r"\1\2", full_text)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)
    full_text = re.sub(r"[ \t]{2,}", " ", full_text)
    return full_text.strip()

