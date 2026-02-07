"""
Text utility helpers – sentence splitting, number extraction, etc.
"""
from __future__ import annotations

import re
from typing import List

# ── Sentence splitter (rule-based, good enough for demo) ───
_SENT_RE = re.compile(
    r'(?<=[.!?])\s+(?=[A-Z])'      # split after .!? followed by uppercase
)


def split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    sents = _SENT_RE.split(text.strip())
    return [s.strip() for s in sents if s.strip()]


# ── Number extractor ────────────────────────────────────────
_NUM_RE = re.compile(
    r'(?:(?:[$€£¥])\s?)?'                   # optional currency
    r'-?\d+(?:[,\d]*)?(?:\.\d+)?'           # number with proper decimal handling
    r'(?:\s?%|(?:\s?(?:mg|kg|ml|g|lb|oz|cm|mm|m|km|ft|in|million|billion|thousand))\b)?',  # unit
    re.IGNORECASE,
)


def extract_numbers(text: str) -> list[str]:
    """Return all numeric tokens (with optional units) found in text."""
    return _NUM_RE.findall(text)


# ── Date extractor (simple) ─────────────────────────────────
_DATE_RE = re.compile(
    r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|'
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+\d{1,2}[\s,]+\d{4}|'
    r'\d{4})\b',
    re.IGNORECASE,
)


def extract_dates(text: str) -> list[str]:
    return _DATE_RE.findall(text)


# ── Normalise a numeric string to float ─────────────────────
def normalise_number(s: str) -> float | None:
    """Try to convert a numeric string to float, handling multipliers like million/billion."""
    original = s
    
    # Check for multipliers
    multiplier = 1.0
    if re.search(r'\bmillion\b', s, re.I):
        multiplier = 1_000_000
    elif re.search(r'\bbillion\b', s, re.I):
        multiplier = 1_000_000_000
    elif re.search(r'\bthousand\b', s, re.I):
        multiplier = 1_000
    
    # Remove currency, units, and multipliers
    cleaned = re.sub(r'[,$€£¥%]', '', s).strip()
    cleaned = re.sub(r'\s*(mg|kg|ml|g|lb|oz|cm|mm|m|km|ft|in|million|billion|thousand)\s*', '', cleaned, flags=re.I).strip()
    
    try:
        return float(cleaned) * multiplier
    except ValueError:
        return None
