"""
Batch Evaluator
===============
Run evaluation on HaluEval dataset and calculate metrics.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import asdict

from app.evaluation.halueval import load_halueval_dataset, load_synthetic_dataset, HaluEvalSample
from app.evaluation.metrics import calculate_metrics, EvaluationMetrics, format_confusion_matrix
from app.services.claim_decomposer import decompose_claims
from app.services.retriever import retrieve_evidence
from app.services.verifier import verify_claim
from app.services.ingestion import _build_indexes

log = logging.getLogger(__name__)


async def run_evaluation(
    dataset_path: Optional[str] = None,
    use_synthetic: bool = False,
    max_samples: Optional[int] = None,
    halueval_samples: Optional[List[HaluEvalSample]] = None,
) -> dict:
    """
    Run full evaluation on HaluEval dataset.
    
    Args:
        dataset_path: Path to HaluEval JSONL file
        use_synthetic: Use synthetic dataset if True
        max_samples: Maximum samples to evaluate
        halueval_samples: Pre-loaded HaluEval samples (bypasses loading)
        
    Returns:
        Dictionary with evaluation results
    """
    log.info("Starting evaluation...")
    
    # Load dataset
    if halueval_samples:
        samples = halueval_samples
        log.info("Using pre-loaded dataset with %d samples", len(samples))
    elif use_synthetic or not dataset_path:
        samples = load_synthetic_dataset()
        log.info("Using synthetic dataset with %d samples", len(samples))
    else:
        samples = load_halueval_dataset(dataset_path, max_samples=max_samples)
    
    if max_samples:
        samples = samples[:max_samples]
    
    # Prepare knowledge base (ingest source texts)
    log.info("Preparing knowledge base from %d samples...", len(samples))
    chunks = []
    for idx, sample in enumerate(samples):
        chunks.append({
            "doc_id": f"eval_doc_{idx}",
            "doc_name": f"Sample {sample.id}",
            "page": 1,
            "paragraph_id": 1,
            "text": sample.knowledge,
            "char_start": 0,
            "char_end": len(sample.knowledge),
        })
    
    # Build indexes for retrieval
    await asyncio.to_thread(_build_indexes, chunks)
    log.info("Knowledge base indexed")
    
    # Run verification on each sample
    predictions = []
    ground_truth = []
    results_details = []
    
    for idx, sample in enumerate(samples):
        if idx % 10 == 0:
            log.info(f"Processing sample {idx + 1}/{len(samples)}")
        
        try:
            # Decompose response into claims
            claims = await asyncio.to_thread(decompose_claims, sample.response)
            
            # Predict label based on worst claim (most conservative)
            worst_label = "SUPPORTED"
            claim_results = []
            
            for claim in claims:
                # Retrieve evidence
                evidences = await asyncio.to_thread(retrieve_evidence, claim.claim_text)
                
                # Verify
                vresult = await asyncio.to_thread(
                    verify_claim, claim.claim_text, claim.claim_type, evidences
                )
                
                claim_results.append({
                    "claim_text": claim.claim_text,
                    "claim_type": claim.claim_type,
                    "label": vresult.label,
                    "confidence": vresult.confidence,
                })
                
                # Update worst label (CONTRADICTED > UNVERIFIABLE > SUPPORTED)
                if vresult.label == "CONTRADICTED":
                    worst_label = "CONTRADICTED"
                elif vresult.label == "UNVERIFIABLE" and worst_label != "CONTRADICTED":
                    worst_label = "UNVERIFIABLE"
            
            predicted_label = worst_label
            true_label = sample.to_verification_label()
            
            predictions.append(predicted_label)
            ground_truth.append(true_label)
            
            results_details.append({
                "id": sample.id,
                "task": sample.task,
                "knowledge": sample.knowledge[:100] + "...",
                "response": sample.response[:100] + "...",
                "true_label": true_label,
                "predicted_label": predicted_label,
                "num_claims": len(claims),
                "claim_results": claim_results,
            })
            
        except Exception as e:
            log.error(f"Error processing sample {sample.id}: {e}")
            # Default to UNVERIFIABLE on error
            predictions.append("UNVERIFIABLE")
            ground_truth.append(sample.to_verification_label())
    
    # Calculate metrics
    metrics = calculate_metrics(predictions, ground_truth)
    
    # Format results
    results = {
        "summary": {
            "total_samples": metrics.total_samples,
            "accuracy": metrics.accuracy,
            "precision": metrics.precision,
            "recall": metrics.recall,
            "f1_score": metrics.f1_score,
        },
        "binary_classification": {
            "description": "Treating CONTRADICTED as positive (hallucination detection)",
            "true_positives": metrics.true_positives,
            "false_positives": metrics.false_positives,
            "true_negatives": metrics.true_negatives,
            "false_negatives": metrics.false_negatives,
            "precision": metrics.contradicted_precision,
            "recall": metrics.contradicted_recall,
            "f1_score": metrics.contradicted_f1,
        },
        "per_class_metrics": {
            "SUPPORTED": {
                "precision": metrics.supported_precision,
                "recall": metrics.supported_recall,
                "f1_score": metrics.supported_f1,
            },
            "CONTRADICTED": {
                "precision": metrics.contradicted_precision,
                "recall": metrics.contradicted_recall,
                "f1_score": metrics.contradicted_f1,
            },
            "UNVERIFIABLE": {
                "precision": metrics.unverifiable_precision,
                "recall": metrics.unverifiable_recall,
                "f1_score": metrics.unverifiable_f1,
            },
        },
        "confusion_matrix": metrics.confusion_matrix,
        "confusion_matrix_text": format_confusion_matrix(metrics.confusion_matrix),
        "sample_results": results_details[:20],  # First 20 for preview
    }
    
    log.info("Evaluation complete - F1: %.4f, Precision: %.4f, Recall: %.4f",
             metrics.f1_score, metrics.precision, metrics.recall)
    
    return results


def analyze_errors(results: dict) -> dict:
    """
    Analyze error patterns from evaluation results.
    
    Args:
        results: Results from run_evaluation
        
    Returns:
        Dictionary with error analysis
    """
    sample_results = results.get("sample_results", [])
    
    false_negatives = []  # Missed hallucinations (most critical)
    false_positives = []  # False alarms
    
    for sample in sample_results:
        true_label = sample["true_label"]
        pred_label = sample["predicted_label"]
        
        if true_label == "CONTRADICTED" and pred_label != "CONTRADICTED":
            false_negatives.append(sample)
        elif true_label != "CONTRADICTED" and pred_label == "CONTRADICTED":
            false_positives.append(sample)
    
    analysis = {
        "false_negatives": {
            "count": len(false_negatives),
            "description": "Missed hallucinations (CRITICAL)",
            "samples": false_negatives[:5],  # Top 5
        },
        "false_positives": {
            "count": len(false_positives),
            "description": "False alarms",
            "samples": false_positives[:5],
        },
        "recommendations": [],
    }
    
    # Generate recommendations
    fn_rate = len(false_negatives) / max(1, results["summary"]["total_samples"])
    if fn_rate > 0.1:
        analysis["recommendations"].append(
            "High false negative rate (>10%) - Consider lowering NLI contradiction threshold"
        )
    
    fp_rate = len(false_positives) / max(1, results["summary"]["total_samples"])
    if fp_rate > 0.2:
        analysis["recommendations"].append(
            "High false positive rate (>20%) - Consider raising NLI contradiction threshold"
        )
    
    return analysis
