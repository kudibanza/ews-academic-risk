"""
Metric functions for imbalanced, cost-sensitive classification.
"""
import numpy as np
from sklearn.metrics import (
    average_precision_score,  # PR-AUC
    fbeta_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_metrics(y_true, y_proba, threshold: float = 0.5) -> dict:
    """
    Compute primary and secondary metrics at a given decision threshold.
    y_proba: predicted probability of the positive class.
    """
    y_pred = (np.asarray(y_proba) >= threshold).astype(int)
    return {
        "pr_auc": float(average_precision_score(y_true, y_proba)),
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "f2": float(fbeta_score(y_true, y_pred, beta=2, zero_division=0)),
    }


PRIMARY_METRICS = ["pr_auc", "recall", "f2"]
SECONDARY_METRICS = ["precision", "roc_auc"]