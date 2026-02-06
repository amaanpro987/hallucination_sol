"""
Verifier (two-layer)
====================
Layer 1 – Deterministic: numeric / date comparison
Layer 2 – NLI: entailment / contradiction / neutral
Falls back to lightweight keyword-overlap heuristic when models unavailable.
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass

from app.config import get_settings
from app.utils.text_utils import extract_numbers, extract_dates, normalise_number
from app.services.retriever import RetrievedEvidence

log = logging.getLogger(__name__)
settings = get_settings()

_nli_model = None
_nli_available = None


def _check_nli():
    global _nli_available
    if _nli_available is not None:
        return _nli_available
    try:
        import sentence_transformers  # noqa: F401
        _nli_available = True
    except ImportError:
        _nli_available = False
        log.warning("sentence_transformers not available — using lightweight verification")
    return _nli_available


def _get_nli():
    global _nli_model
    if _nli_model is None:
        from sentence_transformers import CrossEncoder
        _nli_model = CrossEncoder(settings.NLI_MODEL, device='cpu', max_length=512)
    return _nli_model


# label mapping for deberta-v3-nli: 0=contradiction, 1=entailment, 2=neutral
_LABEL_MAP = {0: "contradiction", 1: "entailment", 2: "neutral"}


@dataclass
class VerificationResult:
    label: str                  # SUPPORTED | CONTRADICTED | UNVERIFIABLE
    confidence: float
    rationale: str
    nli_scores: dict            # per-evidence NLI details
    deterministic_hit: bool = False


# ── Layer 1: Deterministic numeric/date checks ──────────────
def _deterministic_check(claim_text: str, evidence_text: str) -> str | None:
    """
    Return 'SUPPORTED' / 'CONTRADICTED' / None (fallthrough).
    Only fires when both claim and evidence contain numbers/dates.
    """
    claim_nums = [normalise_number(n) for n in extract_numbers(claim_text)]
    claim_nums = [n for n in claim_nums if n is not None]
    ev_nums = [normalise_number(n) for n in extract_numbers(evidence_text)]
    ev_nums = [n for n in ev_nums if n is not None]

    if claim_nums and ev_nums:
        for cn in claim_nums:
            matched = False
            for en in ev_nums:
                if en == 0 and cn == 0:
                    matched = True
                    break
                if en != 0 and abs(cn - en) / abs(en) <= settings.NUMERIC_TOLERANCE:
                    matched = True
                    break
            if not matched:
                return "CONTRADICTED"
        return "SUPPORTED"

    # Date quick-check (exact string match)
    claim_dates = extract_dates(claim_text)
    ev_dates = extract_dates(evidence_text)
    if claim_dates and ev_dates:
        for cd in claim_dates:
            if cd not in ev_dates:
                return "CONTRADICTED"
        return "SUPPORTED"

    return None  # fall through to NLI


# ── Layer 2a: Lightweight heuristic NLI ─────────────────────
_NEGATION_WORDS = re.compile(
    r'\b(no|not|never|none|neither|nor|doesn\'t|don\'t|didn\'t|isn\'t|wasn\'t|aren\'t|weren\'t|without|absence|cannot|can\'t|won\'t|shouldn\'t)\b',
    re.IGNORECASE,
)


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r'\w+', text.lower()))


def _has_negation(text: str) -> bool:
    return bool(_NEGATION_WORDS.search(text))


def _lightweight_verify(claim_text: str, evidences: list[RetrievedEvidence]) -> tuple[str, float, dict]:
    """
    Lightweight verification using token-overlap + negation detection.
    No ML models needed.
    """
    if not evidences:
        return "UNVERIFIABLE", 0.0, {}

    claim_tokens = _tokenize(claim_text)
    claim_negated = _has_negation(claim_text)
    best_label = "UNVERIFIABLE"
    best_conf = 0.0
    details = {}

    for ev in evidences:
        ev_tokens = _tokenize(ev.text)
        ev_negated = _has_negation(ev.text)

        # Token overlap (Jaccard-like)
        if not claim_tokens or not ev_tokens:
            overlap = 0.0
        else:
            overlap = len(claim_tokens & ev_tokens) / len(claim_tokens | ev_tokens)

        # Semantic heuristics
        # If good overlap but mismatched negation → contradiction
        # If good overlap and matching negation → support
        # If low overlap → unverifiable

        entail_score = 0.0
        contra_score = 0.0
        neutral_score = 0.0

        if overlap >= 0.3:
            if claim_negated != ev_negated:
                contra_score = min(0.9, overlap + 0.3)
                entail_score = max(0.0, 0.5 - contra_score)
            else:
                entail_score = min(0.95, overlap + 0.2)
                contra_score = max(0.0, 0.3 - overlap)
            neutral_score = max(0.0, 1.0 - entail_score - contra_score)
        else:
            neutral_score = 0.6
            entail_score = overlap * 0.5
            contra_score = 0.1

        ev_key = f"{ev.doc_id}_p{ev.page}_para{ev.paragraph_id}"
        details[ev_key] = {
            "entail": round(entail_score, 3),
            "contradict": round(contra_score, 3),
            "neutral": round(neutral_score, 3),
        }

        if contra_score > best_conf and contra_score >= 0.5:
            best_label = "CONTRADICTED"
            best_conf = contra_score
        elif entail_score > best_conf and entail_score >= 0.4:
            best_label = "SUPPORTED"
            best_conf = entail_score

    if best_label == "UNVERIFIABLE":
        best_conf = max(0.3, best_conf)

    return best_label, best_conf, details


# ── Layer 2b: NLI-based verification ────────────────────────
def _nli_verify(claim_text: str, evidences: list[RetrievedEvidence]) -> tuple[str, float, dict]:
    """
    Run NLI model on (evidence, claim) pairs.
    Returns (label, confidence, detail_dict).
    """
    if not evidences:
        return "UNVERIFIABLE", 0.0, {}

    nli = _get_nli()
    pairs = [(ev.text, claim_text) for ev in evidences]
    raw_scores = nli.predict(pairs, apply_softmax=True)   # shape (N, 3)

    best_entail = 0.0
    best_contra = 0.0
    details = {}

    for i, ev in enumerate(evidences):
        scores = raw_scores[i]
        e_score = float(scores[1])   # entailment
        c_score = float(scores[0])   # contradiction
        n_score = float(scores[2])   # neutral
        details[ev.doc_id + f"_p{ev.page}_para{ev.paragraph_id}"] = {
            "entail": round(e_score, 3),
            "contradict": round(c_score, 3),
            "neutral": round(n_score, 3),
        }
        best_entail = max(best_entail, e_score)
        best_contra = max(best_contra, c_score)

    if best_contra >= settings.NLI_CONTRADICT_THRESHOLD:
        return "CONTRADICTED", best_contra, details
    if best_entail >= settings.NLI_ENTAIL_THRESHOLD:
        return "SUPPORTED", best_entail, details
    return "UNVERIFIABLE", max(best_entail, best_contra), details


# ── Public API ──────────────────────────────────────────────
def verify_claim(claim_text: str, claim_type: str,
                 evidences: list[RetrievedEvidence]) -> VerificationResult:
    """
    Two-layer verification for a single atomic claim.
    """
    # Layer 1: deterministic (for numeric/date claims)
    if claim_type in ("numeric_date",) and evidences:
        for ev in evidences:
            det = _deterministic_check(claim_text, ev.text)
            if det is not None:
                rationale = (
                    f"Deterministic check: claim numbers vs evidence "
                    f"(Doc {ev.doc_name}, p.{ev.page}, ¶{ev.paragraph_id})."
                )
                return VerificationResult(
                    label=det,
                    confidence=0.95,
                    rationale=rationale,
                    nli_scores={},
                    deterministic_hit=True,
                )

    # Layer 2: NLI (model-based or lightweight)
    # Try model first, but timeout/fall back quickly if download hangs
    use_lightweight = False
    if _check_nli():
        try:
            import signal
            import concurrent.futures
            
            def _try_nli():
                return _nli_verify(claim_text, evidences)
            
            # Try NLI with 10s timeout
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_try_nli)
                try:
                    label, conf, details = future.result(timeout=10)
                except concurrent.futures.TimeoutError:
                    log.warning("NLI model timeout, using lightweight fallback")
                    use_lightweight = True
        except Exception as e:
            log.warning("NLI model failed (%s), falling back to lightweight", e)
            use_lightweight = True
    else:
        use_lightweight = True

    if use_lightweight:
        label, conf, details = _lightweight_verify(claim_text, evidences)

    if label == "CONTRADICTED":
        best_ev = evidences[0] if evidences else None
        rationale = (
            f"Contradiction detected (conf {conf:.2f}). "
            + (f"Evidence: {best_ev.doc_name} p.{best_ev.page} ¶{best_ev.paragraph_id}."
               if best_ev else "")
        )
    elif label == "SUPPORTED":
        best_ev = evidences[0] if evidences else None
        rationale = (
            f"Supported by evidence (conf {conf:.2f}). "
            + (f"Evidence: {best_ev.doc_name} p.{best_ev.page} ¶{best_ev.paragraph_id}."
               if best_ev else "")
        )
    else:
        rationale = f"No strong entailment or contradiction found (conf {conf:.2f}). Marked unverifiable."

    return VerificationResult(
        label=label,
        confidence=conf,
        rationale=rationale,
        nli_scores=details,
    )
