"""
Claim Decomposer
=================
Split LLM output → sentences → atomic claims.
Tag each claim with type and risk weight.
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field

from app.config import get_settings
from app.utils.text_utils import split_sentences, extract_numbers, extract_dates

log = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class Claim:
    sentence_id: int
    claim_id: str
    claim_text: str
    claim_type: str        # numeric_date | entity_relation | negation | causal | definition | general
    risk_weight: float


# ── Claim-type detection heuristics ─────────────────────────
_NEGATION_WORDS = re.compile(
    r'\b(no|not|never|none|neither|nor|doesn\'t|don\'t|didn\'t|isn\'t|wasn\'t|aren\'t|without|absence)\b',
    re.IGNORECASE,
)
_CAUSAL = re.compile(r'\b(because|caused|due to|leads? to|results? in|therefore|hence)\b', re.I)
_DEFINITION = re.compile(r'\b(defined as|means|refers to|is called|states? that|recommends?|guideline)\b', re.I)
_COMPARATIVE = re.compile(r'\b(more than|less than|greater|fewer|higher|lower|compared to|versus|vs\.?)\b', re.I)


def _classify_claim(text: str) -> tuple[str, float]:
    """Return (claim_type, risk_weight)."""
    nums = extract_numbers(text)
    dates = extract_dates(text)

    if nums or dates:
        return "numeric_date", settings.WEIGHT_NUMERIC
    if _NEGATION_WORDS.search(text):
        return "negation", settings.WEIGHT_NEGATION
    if _CAUSAL.search(text):
        return "causal", settings.WEIGHT_ENTITY
    if _DEFINITION.search(text):
        return "definition", settings.WEIGHT_ENTITY
    if _COMPARATIVE.search(text):
        return "comparative", settings.WEIGHT_ENTITY
    return "general", settings.WEIGHT_DEFAULT


# ── Simple conjunction splitter ─────────────────────────────
_CONJ = re.compile(r'\s*[,;]\s*(?:and|but|or|however|while|whereas|although)\s+', re.I)
_LIST_ITEM = re.compile(r'(?:^|\n)\s*(?:\d+[.)]\s*|[-•]\s*)')


def _split_conjunctions(sentence: str) -> list[str]:
    """Split a sentence on conjunctions / list items into sub-claims."""
    parts = _CONJ.split(sentence)
    result: list[str] = []
    for part in parts:
        sub = _LIST_ITEM.split(part)
        result.extend(s.strip() for s in sub if s.strip() and len(s.strip()) > 10)
    if not result:
        return [sentence]
    return result


# ── Public API ──────────────────────────────────────────────
def decompose_claims(text: str) -> list[Claim]:
    """
    Full pipeline:
        text → sentences → atomic claims → typed + weighted
    """
    sentences = split_sentences(text)
    claims: list[Claim] = []

    for s_idx, sentence in enumerate(sentences):
        sub_claims = _split_conjunctions(sentence)
        for c_idx, raw_claim in enumerate(sub_claims):
            ctype, weight = _classify_claim(raw_claim)
            claims.append(Claim(
                sentence_id=s_idx,
                claim_id=f"{s_idx}.{c_idx}",
                claim_text=raw_claim,
                claim_type=ctype,
                risk_weight=weight,
            ))

    log.info("Decomposed %d sentences → %d atomic claims", len(sentences), len(claims))
    return claims
