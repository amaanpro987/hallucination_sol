"""
Orchestrator — ties the full verification pipeline together.
Called by the /verify endpoint.

Pipeline:
  1. Claim decomposition
  2. For each claim → evidence retrieval
  3. For each claim+evidence → verification (deterministic + NLI)
  4. Citation grounding
  5. Correction generation (for Red)
  6. Trust score
"""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import VerificationRun, ClaimResult, async_session
from app.services.claim_decomposer import decompose_claims
from app.services.retriever import retrieve_evidence
from app.services.verifier import verify_claim
from app.services.citation import ground_citation
from app.services.correction import generate_correction
from app.services.trust_score import compute_trust_score

log = logging.getLogger(__name__)


async def run_verification(run_id: str):
    """Execute full pipeline for a verification run."""
    start_time = time.time()
    perf_metrics = {}
    
    async with async_session() as db:
        run: VerificationRun = await db.get(VerificationRun, run_id)
        if not run:
            log.error("Run %s not found", run_id)
            return

        run.status = "running"
        await db.commit()

        try:
            # 1. Claim decomposition
            t0 = time.time()
            claims = await asyncio.to_thread(decompose_claims, run.llm_output)
            perf_metrics["decomposition_sec"] = round(time.time() - t0, 3)

            all_labels: list[str] = []
            all_weights: list[float] = []
            all_types: list[str] = []
            
            retrieval_times = []
            verification_times = []
            citation_times = []
            correction_times = []

            for claim in claims:
                # 2. Evidence retrieval
                t0 = time.time()
                evidences = await asyncio.to_thread(
                    retrieve_evidence, claim.claim_text
                )
                retrieval_times.append(time.time() - t0)

                # 3. Verification
                t0 = time.time()
                vresult = await asyncio.to_thread(
                    verify_claim, claim.claim_text, claim.claim_type, evidences
                )
                verification_times.append(time.time() - t0)

                # 4. Citation grounding
                t0 = time.time()
                ev_dicts = []
                for ev in evidences[:3]:
                    cit = ground_citation(claim.claim_text, ev, vresult.nli_scores)
                    ev_dicts.append({
                        "doc_id": cit.doc_id,
                        "doc_name": cit.doc_name,
                        "page": cit.page,
                        "paragraph_id": cit.paragraph_id,
                        "snippet": cit.snippet,
                        "highlight_offsets": cit.highlight_offsets,
                        "retrieval_score": round(cit.retrieval_score, 3),
                        "nli": cit.nli,
                    })
                citation_times.append(time.time() - t0)

                # 5. Correction for Red
                t0 = time.time()
                correction = None
                if vresult.label == "CONTRADICTED" and evidences:
                    corrected_text, explanation = await asyncio.to_thread(
                        generate_correction,
                        claim.claim_text, claim.claim_type, evidences[0]
                    )
                    correction = corrected_text
                    vresult.rationale = explanation
                correction_times.append(time.time() - t0)

                # Save claim result
                cr = ClaimResult(
                    run_id=run_id,
                    sentence_id=claim.sentence_id,
                    claim_id=claim.claim_id,
                    claim_text=claim.claim_text,
                    claim_type=claim.claim_type,
                    risk_weight=claim.risk_weight,
                    label=vresult.label,
                    confidence=round(vresult.confidence, 3),
                    rationale=vresult.rationale,
                    evidence=ev_dicts,
                    suggested_correction=correction,
                )
                db.add(cr)

                all_labels.append(vresult.label)
                all_weights.append(claim.risk_weight)
                all_types.append(claim.claim_type)

            # 6. Trust score
            t0 = time.time()
            trust = compute_trust_score(all_labels, all_weights, all_types)
            perf_metrics["trust_score_sec"] = round(time.time() - t0, 3)
            
            # Aggregate timing stats
            perf_metrics["avg_retrieval_sec"] = round(sum(retrieval_times) / len(retrieval_times), 3) if retrieval_times else 0
            perf_metrics["avg_verification_sec"] = round(sum(verification_times) / len(verification_times), 3) if verification_times else 0
            perf_metrics["avg_citation_sec"] = round(sum(citation_times) / len(citation_times), 3) if citation_times else 0
            perf_metrics["avg_correction_sec"] = round(sum(correction_times) / len(correction_times), 3) if correction_times else 0
            perf_metrics["total_retrieval_sec"] = round(sum(retrieval_times), 3)
            perf_metrics["total_verification_sec"] = round(sum(verification_times), 3)
            perf_metrics["total_sec"] = round(time.time() - start_time, 3)
            perf_metrics["claims_count"] = len(claims)
            
            run.trust_score = trust.overall
            run.faithfulness = trust.faithfulness
            run.groundedness = trust.groundedness
            run.performance_metrics = perf_metrics
            run.status = "done"
            run.finished_at = dt.datetime.utcnow()
            await db.commit()

            log.info(
                "Run %s done — %d claims, trust=%.1f, faith=%.1f, ground=%.1f, time=%.2fs",
                run_id, len(claims), trust.overall, trust.faithfulness, trust.groundedness,
                perf_metrics["total_sec"],
            )

        except Exception as exc:
            log.exception("Verification run %s failed", run_id)
            run.status = "failed"
            run.performance_metrics = perf_metrics
            await db.commit()
