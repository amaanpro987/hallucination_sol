"""
Trust Score Computation
=======================
Computes per-run trust scores: overall, faithfulness, groundedness.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings

settings = get_settings()


@dataclass
class TrustScore:
    overall: float                # 0-100
    faithfulness: float           # 0-100
    groundedness: float           # 0-100
    supported_count: int
    contradicted_count: int
    unverifiable_count: int
    high_risk_contradictions: int


def compute_trust_score(
    labels: list[str],
    weights: list[float],
    claim_types: list[str],
) -> TrustScore:
    """
    labels:      list of SUPPORTED / CONTRADICTED / UNVERIFIABLE
    weights:     parallel list of risk weights
    claim_types: parallel list of claim type strings
    """
    supported = sum(1 for l in labels if l == "SUPPORTED")
    contradicted = sum(1 for l in labels if l == "CONTRADICTED")
    unverifiable = sum(1 for l in labels if l == "UNVERIFIABLE")
    total = len(labels)

    if total == 0:
        return TrustScore(100.0, 100.0, 100.0, 0, 0, 0, 0)

    # High-risk contradictions
    high_risk_types = {"numeric_date", "negation", "causal"}
    hr_contradictions = sum(
        1 for l, ct in zip(labels, claim_types)
        if l == "CONTRADICTED" and ct in high_risk_types
    )

    # Weighted score
    score_map = {
        "SUPPORTED": 1.0,
        "UNVERIFIABLE": settings.UNVERIFIABLE_SCORE,
        "CONTRADICTED": 0.0,
    }

    weighted_sum = sum(w * score_map.get(l, 0.5) for w, l in zip(weights, labels))
    weight_total = sum(weights)

    raw_score = (weighted_sum / weight_total * 100) if weight_total else 100.0

    # Critical penalties
    penalty = hr_contradictions * settings.CRITICAL_PENALTY
    overall = max(0.0, raw_score - penalty)

    # Faithfulness = Supported / (Supported + Contradicted)
    if supported + contradicted > 0:
        faithfulness = supported / (supported + contradicted) * 100
    else:
        faithfulness = 100.0

    # Groundedness = Supported / (Supported + Unverifiable)
    if supported + unverifiable > 0:
        groundedness = supported / (supported + unverifiable) * 100
    else:
        groundedness = 100.0

    return TrustScore(
        overall=round(overall, 1),
        faithfulness=round(faithfulness, 1),
        groundedness=round(groundedness, 1),
        supported_count=supported,
        contradicted_count=contradicted,
        unverifiable_count=unverifiable,
        high_risk_contradictions=hr_contradictions,
    )
