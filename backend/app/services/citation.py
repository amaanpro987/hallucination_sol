"""
Citation Grounding
==================
From the best evidence chunk, extract the minimal supporting/contradicting
snippet and return precise offsets for UI highlighting.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.services.retriever import RetrievedEvidence
from app.utils.text_utils import split_sentences


@dataclass
class CitationSpan:
    doc_id: str
    doc_name: str
    page: int
    paragraph_id: int
    snippet: str
    highlight_offsets: list[int]    # [start, end] within the paragraph
    retrieval_score: float
    nli: dict


def _best_overlap_span(claim: str, evidence_text: str, window: int = 3) -> tuple[str, int, int]:
    """
    Slide a window of `window` sentences over the evidence and return the
    sub-span with highest token overlap to the claim.
    """
    ev_sents = split_sentences(evidence_text)
    if not ev_sents:
        return evidence_text, 0, len(evidence_text)

    claim_tokens = set(re.findall(r'\w+', claim.lower()))
    best_score = -1.0
    best_span = evidence_text
    best_start = 0
    best_end = len(evidence_text)

    for i in range(len(ev_sents)):
        span = " ".join(ev_sents[i: i + window])
        span_tokens = set(re.findall(r'\w+', span.lower()))
        if not span_tokens:
            continue
        overlap = len(claim_tokens & span_tokens) / len(claim_tokens | span_tokens)
        if overlap > best_score:
            best_score = overlap
            best_span = span
            best_start = evidence_text.find(span[:30])
            if best_start == -1:
                best_start = 0
            best_end = best_start + len(span)

    return best_span, best_start, best_end


def ground_citation(claim_text: str,
                    evidence: RetrievedEvidence,
                    nli_scores: dict) -> CitationSpan:
    """
    Given one evidence passage, extract the minimal snippet that covers the
    claim and return structured citation with offsets.
    """
    snippet, start, end = _best_overlap_span(claim_text, evidence.text)
    return CitationSpan(
        doc_id=evidence.doc_id,
        doc_name=evidence.doc_name,
        page=evidence.page,
        paragraph_id=evidence.paragraph_id,
        snippet=snippet,
        highlight_offsets=[start, end],
        retrieval_score=evidence.score,
        nli=nli_scores,
    )
