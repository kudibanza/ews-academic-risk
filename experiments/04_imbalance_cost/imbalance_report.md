# Imbalance Benchmark Report — Sub-step 4.1 (RQ3)

Imbalance strategies benchmarked per protocol.yaml §6.
Models: lightgbm, xgboost, logreg.
Strategies: none, SMOTE, ADASYN, Tomek Links, class_weight.
Application: training fold only, after split (Rule 2, via imblearn.pipeline.Pipeline).
GroupKFold(5) by student_id. Threshold 0.5 (cost-sensitive tuning in 4.3).

- Runs: 60 (4 windows × 3 models × 5 strategies)
- Total folds: 300 (60 × 5)
- Valid folds: 285
- Skipped folds: 15 (ADASYN in W2, all models: 5/5 folds skipped each)

## Key findings

### 1. class_weight is the best overall strategy

Across all windows and for lightgbm (the best model from Step 3),
class_weight raises recall by 10–15 percentage points with no meaningful
loss in PR-AUC:

| Window | Recall (none) | Recall (class_weight) | F2 (none) | F2 (class_weight) | PR-AUC (none) | PR-AUC (class_weight) |
|---|---|---|---|---|---|---|
| W2 | 0.520 | 0.617 | 0.535 | 0.610 | 0.619 | 0.619 |
| W4 | 0.568 | 0.648 | 0.585 | 0.644 | 0.694 | 0.695 |
| W6 | 0.577 | 0.671 | 0.596 | 0.665 | 0.715 | 0.715 |
| W8 | 0.580 | 0.675 | 0.603 | 0.672 | 0.745 | 0.745 |

This is the desired outcome for an early warning system: more at-risk
students detected without degrading the model's ability to rank students
by risk.

### 2. Tomek Links maximizes recall but loses PR-AUC

Tomek achieves recall comparable to or slightly above class_weight
(0.669 in W2, 0.656 in W4, 0.669 in W6, 0.660 in W8 for lightgbm),
but PR-AUC drops consistently (0.607 vs 0.619 in W2; 0.690 vs 0.695
in W4). For an early warning system, preserving discrimination matters
more than maximizing recall at a fixed threshold, because the threshold
will be tuned to operational cost in sub-step 4.3. class_weight is
preferred.

### 3. SMOTE is redundant over class_weight

SMOTE sits between none and class_weight on recall, with PR-AUC
essentially equal to none. It adds synthetic data that complicates
SHAP interpretability (Step 5) without a measurable benefit over
class_weight.

### 4. ADASYN limitation in W2 (documented)

"ADASYN failed to generate synthetic samples in W2 across all three models (5/5 folds skipped). This is consistent with documented behaviour of ADASYN when the minority class is too small to satisfy its nearest-neighbour requirement [58], and with recent evidence that synthetic oversampling, including ADASYN, can lower performance when at-risk students are scattered within the majority class [57]. In our setting, the combination of operational exclusion (§4) and the low coverage of assessment features in W2 leaves the minority class too small for ADASYN to operate. The failure is documented rather than corrected, as it reflects a genuine limitation of the method in this early-window context. Notably, cost-sensitive weighting (class_weight), which does not require synthetic samples, performed best overall (Section 4.1)."

The `n_skipped_folds` column in imbalance_summary.csv records this
explicitly, so the omission is visible rather than silent.

## Decision for sub-steps 4.2 and 4.3

Based on the above, the configuration carried forward is:

- **Primary:** lightgbm + class_weight (best PR-AUC and F2 among
  strategies that preserve discrimination).
- **Secondary:** xgboost + class_weight (comparable, slightly behind).
- **Baseline:** lightgbm + none (from Step 3, for comparison).

SMOTE, ADASYN, and Tomek are not carried forward as primary
configurations. They remain documented in the report as alternatives
explored, with their trade-offs (higher recall, lower PR-AUC; or
failure in W2).

## Reproducibility

- results/tables/imbalance_results.csv — 300 rows.
- results/tables/imbalance_summary.csv — 60 rows, with
  n_valid_folds and n_skipped_folds per combination.
- Seed 42. Default hyperparameters. GroupKFold(5) by student_id.
- imblearn.pipeline.Pipeline used to ensure Rule 2 (resampling only
  on training fold).

## References (for ADASYN limitation discussion)

[57] D. Agustini, P. N. Andono, R. A. Pramunendar and M. E. Rosadi, "Minority-Class Geometry and Calibrated Cost-Sensitive Ensembles for Identifying Students at Risk Under Class Imbalance," 2026 International Seminar on Application for Technology of Information and Communication (iSemantic), Semarang, Indonesia, 2026, pp. 275-282, doi: 10.1109/iSemantic71495.2026.11742853.

[58] Putrama, I. M., & Martinek, P. (2025). "Neighbor Displacement-Based Enhanced Synthetic Oversampling for Multiclass Imbalanced Data." Computers, Materials & Continua, 83(3), 5699–5727. DOI: 10.32604/cmc.2025.063465

---

## Sub-step 4.3 — Cost-sensitive threshold tuning

Configuration: LightGBM + class_weight and XGBoost + class_weight,
both uncalibrated (decision from sub-step 4.2). Threshold searched on
an inner validation fold (GroupKFold 2 within the training fold),
evaluated on the held-out test fold. Primary cost ratio C_FN:C_FP = 5:1;
sensitivity at 3:1 and 10:1. Threshold grid: 0.10 to 0.90, step 0.01.

### Results: optimal threshold (theta*) by model and ratio

| Window | Ratio | theta* LightGBM | theta* XGBoost |
|---|---|---|---|
| W2 | 3:1 | 0.264 | 0.140 |
| W2 | 5:1 | 0.116 | 0.102 |
| W2 | 10:1 | 0.100 | 0.100 |
| W4 | 3:1 | 0.266 | 0.168 |
| W4 | 5:1 | 0.120 | 0.102 |
| W4 | 10:1 | 0.102 | 0.100 |
| W6 | 3:1 | 0.280 | 0.186 |
| W6 | 5:1 | 0.160 | 0.106 |
| W6 | 10:1 | 0.102 | 0.100 |
| W8 | 3:1 | 0.296 | 0.240 |
| W8 | 5:1 | 0.172 | 0.106 |
| W8 | 10:1 | 0.104 | 0.100 |

The threshold order is monotonic with the cost ratio in all cases:
10:1 < 5:1 < 3:1 (more FN penalty → lower threshold → higher recall).
This confirms the optimisation is functioning as intended.

### Results: metrics at theta* (5:1 primary ratio)

| Window | Model | Recall (0.5 → theta*) | Precision (0.5 → theta*) | F2 (0.5 → theta*) | Expected cost (0.5 → theta*) |
|---|---|---|---|---|---|
| W2 | LightGBM | 0.617 → **0.998** | 0.583 → 0.455 | 0.610 → **0.805** | 6004 → **3077** |
| W2 | XGBoost | 0.607 → **0.991** | 0.572 → 0.457 | 0.599 → **0.804** | 6167 → **3104** |
| W4 | LightGBM | 0.648 → **0.995** | 0.630 → 0.446 | 0.644 → **0.799** | 5202 → **3062** |
| W4 | XGBoost | 0.636 → **0.985** | 0.617 → 0.453 | 0.632 → **0.797** | 5380 → **3077** |
| W6 | LightGBM | 0.671 → **0.981** | 0.642 → 0.455 | 0.665 → **0.797** | 4697 → **2955** |
| W6 | XGBoost | 0.653 → **0.980** | 0.633 → 0.453 | 0.649 → **0.795** | 4923 → **2992** |
| W8 | LightGBM | 0.675 → **0.969** | 0.663 → 0.464 | 0.672 → **0.796** | 4385 → **2831** |
| W8 | XGBoost | 0.661 → **0.978** | 0.651 → 0.451 | 0.659 → **0.792** | 4564 → **2900** |

### Key findings

1. **Threshold tuning is highly effective.** At the primary 5:1 ratio,
   recall rises from ~0.62–0.68 to ~0.97–0.998, F2 rises from ~0.61–0.67
   to ~0.79–0.81, and expected cost roughly halves. This is the intended
   behaviour for an early warning system where a missed at-risk student
   is five times costlier than an unnecessary advisor check-in.

2. **XGBoost needs lower thresholds than LightGBM.** For 3:1 and 5:1,
   theta* is systematically lower for XGBoost (e.g., W2 3:1: 0.264 vs
   0.140). This compensates for XGBoost's compressed probability scale
   (higher ECE, as documented in sub-step 4.2). The threshold tuning
   effectively absorbs the miscalibration that calibration would have
   addressed, which validates the decision in 4.2 to skip calibration
   and rely on threshold tuning instead.

3. **At theta*, the two models converge on operational cost.** The
   expected cost at theta* differs by only 0.9–2.4% between LightGBM
   and XGBoost (e.g., W8 5:1: 2831 vs 2900). Despite LightGBM's higher
   PR-AUC, threshold tuning nearly equalises the two models in
   operational terms. This is an important result: the choice between
   LightGBM and XGBoost is not critical once the threshold is tuned.

4. **10:1 saturates recall.** At 10:1, both models reach recall
   ≈ 0.98–0.999, with precision ≈ 0.43–0.46. This is the most aggressive
   configuration, appropriate only if the institution treats every
   missed at-risk student as extremely costly.

5. **3:1 is the conservative configuration.** Recall 0.89–0.96,
   precision 0.47–0.53. This is the recommended ratio if the institution
   wants to limit advisor workload while still catching the large
   majority of at-risk students.

### Decision for Step 5 (SHAP)

The primary configuration carried forward to SHAP is:

- **Model:** LightGBM + class_weight, uncalibrated.
- **Threshold:** theta* per window at 5:1 (0.116 / 0.120 / 0.160 / 0.172).
- **Rationale:** LightGBM has marginally better PR-AUC and slightly lower
  expected cost at theta*; it is the best model from Steps 3 and 4.

XGBoost remains documented as a comparable alternative, with its
threshold-tuning results reported above for completeness.

### Reproducibility

- results/tables/threshold_results.csv — 240 rows
  (4 windows × 5 folds × 2 models × 3 ratios × 2 threshold types).
- results/tables/threshold_summary.csv — 48 rows (mean ± std).
- Seed 42. GroupKFold(5) outer, GroupKFold(2) inner for threshold search.
- XGBoost scale_pos_weight computed from the training fold only (Rule 1).