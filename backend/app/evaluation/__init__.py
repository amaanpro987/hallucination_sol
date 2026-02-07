"""Evaluation module for hallucination detection."""

from app.evaluation.metrics import calculate_metrics, EvaluationMetrics, format_confusion_matrix
from app.evaluation.halueval import load_halueval_dataset, load_synthetic_dataset, HaluEvalSample
from app.evaluation.evaluator import run_evaluation, analyze_errors

__all__ = [
    "calculate_metrics",
    "EvaluationMetrics",
    "format_confusion_matrix",
    "load_halueval_dataset",
    "load_synthetic_dataset",
    "HaluEvalSample",
    "run_evaluation",
    "analyze_errors",
]
