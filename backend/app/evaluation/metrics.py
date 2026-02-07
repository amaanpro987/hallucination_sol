"""
Evaluation Metrics
==================
Calculate F1-Score, Precision, Recall, and Confusion Matrix for hallucination detection.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class EvaluationMetrics:
    """Evaluation metrics for hallucination detection."""
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    confusion_matrix: dict
    total_samples: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    
    # Per-class metrics
    supported_precision: float
    supported_recall: float
    supported_f1: float
    contradicted_precision: float
    contradicted_recall: float
    contradicted_f1: float
    unverifiable_precision: float
    unverifiable_recall: float
    unverifiable_f1: float


def calculate_metrics(
    predictions: List[str],
    ground_truth: List[str]
) -> EvaluationMetrics:
    """
    Calculate evaluation metrics for hallucination detection.
    
    Args:
        predictions: List of predicted labels (SUPPORTED, CONTRADICTED, UNVERIFIABLE)
        ground_truth: List of ground truth labels
        
    Returns:
        EvaluationMetrics with all computed metrics
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truth must have same length")
    
    total = len(predictions)
    if total == 0:
        return _empty_metrics()
    
    # Initialize confusion matrix
    labels = ["SUPPORTED", "CONTRADICTED", "UNVERIFIABLE"]
    confusion = {label: {pred: 0 for pred in labels} for label in labels}
    
    # Build confusion matrix
    for pred, truth in zip(predictions, ground_truth):
        if truth in confusion and pred in confusion[truth]:
            confusion[truth][pred] += 1
    
    # Calculate per-class metrics
    class_metrics = {}
    for label in labels:
        tp = confusion[label][label]
        fp = sum(confusion[other][label] for other in labels if other != label)
        fn = sum(confusion[label][other] for other in labels if other != label)
        tn = sum(
            confusion[other1][other2]
            for other1 in labels if other1 != label
            for other2 in labels if other2 != label
        )
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        class_metrics[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        }
    
    # Overall metrics (macro-averaged)
    macro_precision = sum(m["precision"] for m in class_metrics.values()) / len(labels)
    macro_recall = sum(m["recall"] for m in class_metrics.values()) / len(labels)
    macro_f1 = sum(m["f1"] for m in class_metrics.values()) / len(labels)
    
    # Overall accuracy
    correct = sum(1 for p, t in zip(predictions, ground_truth) if p == t)
    accuracy = correct / total
    
    # Binary metrics (treating CONTRADICTED as positive, others as negative)
    # This is most critical for hallucination detection
    binary_tp = confusion["CONTRADICTED"]["CONTRADICTED"]
    binary_fp = sum(confusion[other]["CONTRADICTED"] for other in labels if other != "CONTRADICTED")
    binary_fn = sum(confusion["CONTRADICTED"][other] for other in labels if other != "CONTRADICTED")
    binary_tn = sum(
        confusion[other1][other2]
        for other1 in labels if other1 != "CONTRADICTED"
        for other2 in labels if other2 != "CONTRADICTED"
    )
    
    return EvaluationMetrics(
        precision=round(macro_precision, 4),
        recall=round(macro_recall, 4),
        f1_score=round(macro_f1, 4),
        accuracy=round(accuracy, 4),
        confusion_matrix=confusion,
        total_samples=total,
        true_positives=binary_tp,
        false_positives=binary_fp,
        true_negatives=binary_tn,
        false_negatives=binary_fn,
        supported_precision=class_metrics["SUPPORTED"]["precision"],
        supported_recall=class_metrics["SUPPORTED"]["recall"],
        supported_f1=class_metrics["SUPPORTED"]["f1"],
        contradicted_precision=class_metrics["CONTRADICTED"]["precision"],
        contradicted_recall=class_metrics["CONTRADICTED"]["recall"],
        contradicted_f1=class_metrics["CONTRADICTED"]["f1"],
        unverifiable_precision=class_metrics["UNVERIFIABLE"]["precision"],
        unverifiable_recall=class_metrics["UNVERIFIABLE"]["recall"],
        unverifiable_f1=class_metrics["UNVERIFIABLE"]["f1"],
    )


def _empty_metrics() -> EvaluationMetrics:
    """Return empty metrics for edge cases."""
    return EvaluationMetrics(
        precision=0.0,
        recall=0.0,
        f1_score=0.0,
        accuracy=0.0,
        confusion_matrix={},
        total_samples=0,
        true_positives=0,
        false_positives=0,
        true_negatives=0,
        false_negatives=0,
        supported_precision=0.0,
        supported_recall=0.0,
        supported_f1=0.0,
        contradicted_precision=0.0,
        contradicted_recall=0.0,
        contradicted_f1=0.0,
        unverifiable_precision=0.0,
        unverifiable_recall=0.0,
        unverifiable_f1=0.0,
    )


def format_confusion_matrix(confusion_matrix: dict) -> str:
    """
    Format confusion matrix as ASCII table.
    
    Args:
        confusion_matrix: Dictionary mapping true labels to predicted labels
        
    Returns:
        Formatted string representation
    """
    labels = ["SUPPORTED", "CONTRADICTED", "UNVERIFIABLE"]
    
    # Calculate column widths
    label_width = max(len(label) for label in labels)
    
    # Header
    lines = []
    header = " " * (label_width + 2) + "Predicted"
    lines.append(header)
    lines.append(" " * (label_width + 2) + "  ".join(f"{label[:3]:>6}" for label in labels))
    lines.append("-" * (label_width + 2 + len(labels) * 8))
    
    # Rows
    for true_label in labels:
        row_vals = [confusion_matrix.get(true_label, {}).get(pred, 0) for pred in labels]
        row_str = f"{true_label[:3]:<{label_width}}  " + "  ".join(f"{val:>6}" for val in row_vals)
        lines.append(row_str)
    
    return "\n".join(lines)
