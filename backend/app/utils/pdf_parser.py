"""
PDF + text parsing utilities.
Extracts text with page numbers, paragraph boundaries, and character offsets.
"""
from __future__ import annotations

import re
from pathlib import Path
from dataclasses import dataclass, field

import fitz  # PyMuPDF


@dataclass
class Paragraph:
    page: int
    paragraph_id: int
    text: str
    char_start: int
    char_end: int


@dataclass
class ParsedDocument:
    filename: str
    num_pages: int
    paragraphs: list[Paragraph] = field(default_factory=list)
    full_text: str = ""


# ── Helpers ─────────────────────────────────────────────────
_PARA_SPLIT = re.compile(r"\n{2,}")


def _split_paragraphs(text: str) -> list[str]:
    """Split text on double-newline boundaries, drop blanks."""
    parts = _PARA_SPLIT.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


# ── PDF Parser ──────────────────────────────────────────────
def parse_pdf(filepath: str | Path) -> ParsedDocument:
    """Extract text from PDF preserving page + paragraph structure."""
    filepath = Path(filepath)
    doc = fitz.open(str(filepath))
    paragraphs: list[Paragraph] = []
    full_parts: list[str] = []
    global_offset = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text("text")
        full_parts.append(page_text)

        for para_idx, para_text in enumerate(_split_paragraphs(page_text)):
            start = global_offset
            end = start + len(para_text)
            paragraphs.append(
                Paragraph(
                    page=page_num + 1,           # 1-indexed
                    paragraph_id=para_idx,
                    text=para_text,
                    char_start=start,
                    char_end=end,
                )
            )
            global_offset = end + 1              # +1 for separator

    full_text = "\n".join(full_parts)
    return ParsedDocument(
        filename=filepath.name,
        num_pages=len(doc),
        paragraphs=paragraphs,
        full_text=full_text,
    )


# ── Plain-text parser ──────────────────────────────────────
def parse_text(filepath: str | Path) -> ParsedDocument:
    """Parse a plain-text file into paragraphs."""
    filepath = Path(filepath)
    raw = filepath.read_text(encoding="utf-8", errors="replace")
    paragraphs: list[Paragraph] = []
    offset = 0
    for idx, para_text in enumerate(_split_paragraphs(raw)):
        start = offset
        end = start + len(para_text)
        paragraphs.append(
            Paragraph(page=1, paragraph_id=idx, text=para_text,
                      char_start=start, char_end=end)
        )
        offset = end + 1

    return ParsedDocument(
        filename=filepath.name,
        num_pages=1,
        paragraphs=paragraphs,
        full_text=raw,
    )


def parse_file(filepath: str | Path) -> ParsedDocument:
    """Auto-dispatch on extension."""
    filepath = Path(filepath)
    if filepath.suffix.lower() == ".pdf":
        return parse_pdf(filepath)
    return parse_text(filepath)
