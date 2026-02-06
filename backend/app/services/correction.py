"""
Correction Engine
=================
For CONTRADICTED claims, generate a corrected statement constrained to evidence.
"""
from __future__ import annotations

import re
from app.services.retriever import RetrievedEvidence
from app.utils.text_utils import extract_numbers, extract_dates


def generate_correction(claim_text: str,
                        claim_type: str,
                        evidence: RetrievedEvidence) -> tuple[str, str]:
    """
    Return (corrected_claim, explanation).
    Uses template-based correction for numeric/date; simple evidence-quote otherwise.
    """
    ev_text = evidence.text

    # ── Template-based for numeric/date claims ──────────────
    if claim_type == "numeric_date":
        claim_nums = extract_numbers(claim_text)
        ev_nums = extract_numbers(ev_text)
        if claim_nums and ev_nums:
            corrected = claim_text
            for cn in claim_nums:
                if cn not in ev_nums and ev_nums:
                    corrected = corrected.replace(cn, ev_nums[0], 1)
            explanation = (
                f"Claim states '{claim_nums[0]}' but source says '{ev_nums[0]}' "
                f"({evidence.doc_name}, p.{evidence.page}, ¶{evidence.paragraph_id})."
            )
            return corrected, explanation

        claim_dates = extract_dates(claim_text)
        ev_dates = extract_dates(ev_text)
        if claim_dates and ev_dates:
            corrected = claim_text
            for cd in claim_dates:
                if cd not in ev_dates and ev_dates:
                    corrected = corrected.replace(cd, ev_dates[0], 1)
            explanation = (
                f"Claim states '{claim_dates[0]}' but source says '{ev_dates[0]}' "
                f"({evidence.doc_name}, p.{evidence.page}, ¶{evidence.paragraph_id})."
            )
            return corrected, explanation

    # ── General: quote evidence as the correction ───────────
    # Trim evidence to ~1 sentence that best matches claim
    ev_sents = re.split(r'(?<=[.!?])\s+', ev_text.strip())
    if ev_sents:
        # pick sentence with most token overlap
        claim_tokens = set(re.findall(r'\w+', claim_text.lower()))
        best = max(ev_sents, key=lambda s: len(claim_tokens & set(re.findall(r'\w+', s.lower()))))
        corrected = best.strip()
    else:
        corrected = ev_text[:200]

    explanation = (
        f"According to {evidence.doc_name} (p.{evidence.page}, ¶{evidence.paragraph_id}): "
        f'"{corrected}"'
    )
    return corrected, explanation
