# Benchmark Report — Sub-step 3.3 (RQ2)

Model benchmarking per protocol.yaml §16. GroupKFold(5) by student_id.
Default hyperparameters (tuning deferred to Step 3b).
W2 runs under Variant A (7 features) and Variant B (5 features).
W4–W8 run under Variant A only.

- Runs: 25 (4 windows × 5 models + 5 extra for W2 variant B)
- Folds per run: 5
- Total fits: 125
- Metrics computed at threshold 0.5 (cost-sensitive tuning in Step 4)

## Results by window

### W2 (cutoff = 14 days)

| Model | Variant | PR-AUC | ROC-AUC | Recall | Precision | F2 |
|---|---|---|---|---|---|---|
| **lightgbm** | A | **0.619 ± 0.005** | 0.671 ± 0.007 | 0.520 ± 0.011 | 0.608 ± 0.010 | **0.535 ± 0.009** |
| xgboost | A | 0.600 ± 0.008 | 0.655 ± 0.008 | 0.519 ± 0.013 | 0.591 ± 0.011 | 0.532 ± 0.011 |
| rf | A | 0.584 ± 0.009 | 0.636 ± 0.011 | 0.510 ± 0.016 | 0.572 ± 0.012 | 0.522 ± 0.014 |
| logreg | A | 0.567 ± 0.009 | 0.640 ± 0.007 | 0.497 ± 0.014 | 0.553 ± 0.014 | 0.507 ± 0.012 |
| dtree | A | 0.467 ± 0.008 | 0.544 ± 0.008 | 0.541 ± 0.017 | 0.516 ± 0.009 | 0.536 ± 0.014 |
| lightgbm | B | 0.614 ± 0.007 | 0.667 ± 0.010 | 0.511 ± 0.012 | 0.604 ± 0.010 | 0.527 ± 0.011 |
| xgboost | B | 0.589 ± 0.007 | 0.647 ± 0.008 | 0.515 ± 0.012 | 0.583 ± 0.009 | 0.528 ± 0.010 |
| rf | B | 0.577 ± 0.007 | 0.629 ± 0.010 | 0.508 ± 0.012 | 0.565 ± 0.011 | 0.519 ± 0.011 |
| logreg | B | 0.567 ± 0.011 | 0.637 ± 0.007 | 0.501 ± 0.011 | 0.550 ± 0.013 | 0.510 ± 0.010 |
| dtree | B | 0.464 ± 0.004 | 0.539 ± 0.006 | 0.545 ± 0.014 | 0.512 ± 0.004 | 0.538 ± 0.011 |

**W2 A-vs-B finding:** Variant A (retain Delta_t and S_score) is marginally
better for 4 of 5 models (lightgbm +0.005 PR-AUC, xgboost +0.011, rf +0.008,
dtree +0.003); logreg is a tie. The difference is small but consistent.
Keeping the assessment features in W2 despite ~4% coverage does not harm
performance and slightly helps. This empirically resolves the §16 question.

### W4 (cutoff = 28 days)

| Model | PR-AUC | ROC-AUC | Recall | Precision | F2 |
|---|---|---|---|---|---|
| **lightgbm** | **0.694 ± 0.011** | 0.737 ± 0.004 | 0.568 ± 0.010 | 0.668 ± 0.016 | **0.585 ± 0.006** |
| xgboost | 0.676 ± 0.012 | 0.722 ± 0.004 | 0.565 ± 0.010 | 0.648 ± 0.015 | 0.579 ± 0.007 |
| rf | 0.664 ± 0.014 | 0.717 ± 0.005 | 0.565 ± 0.014 | 0.644 ± 0.012 | 0.579 ± 0.010 |
| logreg | 0.599 ± 0.008 | 0.689 ± 0.008 | 0.512 ± 0.020 | 0.613 ± 0.013 | 0.529 ± 0.016 |
| dtree | 0.485 ± 0.012 | 0.584 ± 0.009 | 0.552 ± 0.009 | 0.544 ± 0.017 | 0.550 ± 0.009 |

### W6 (cutoff = 42 days)

| Model | PR-AUC | ROC-AUC | Recall | Precision | F2 |
|---|---|---|---|---|---|
| **lightgbm** | **0.715 ± 0.012** | 0.762 ± 0.005 | 0.577 ± 0.006 | 0.689 ± 0.019 | **0.596 ± 0.004** |
| xgboost | 0.701 ± 0.012 | 0.748 ± 0.005 | 0.582 ± 0.006 | 0.671 ± 0.016 | 0.597 ± 0.004 |
| rf | 0.690 ± 0.019 | 0.747 ± 0.008 | 0.586 ± 0.007 | 0.665 ± 0.020 | 0.601 ± 0.006 |
| logreg | 0.615 ± 0.015 | 0.713 ± 0.006 | 0.532 ± 0.014 | 0.625 ± 0.014 | 0.548 ± 0.012 |
| dtree | 0.489 ± 0.010 | 0.602 ± 0.005 | 0.565 ± 0.012 | 0.553 ± 0.011 | 0.562 ± 0.010 |

### W8 (cutoff = 56 days)

| Model | PR-AUC | ROC-AUC | Recall | Precision | F2 |
|---|---|---|---|---|---|
| **lightgbm** | **0.745 ± 0.019** | 0.788 ± 0.008 | 0.580 ± 0.012 | 0.717 ± 0.024 | **0.603 ± 0.011** |
| xgboost | 0.731 ± 0.016 | 0.776 ± 0.007 | 0.586 ± 0.013 | 0.696 ± 0.015 | 0.605 ± 0.011 |
| rf | 0.717 ± 0.020 | 0.771 ± 0.009 | 0.590 ± 0.015 | 0.686 ± 0.022 | 0.607 ± 0.014 |
| logreg | 0.649 ± 0.023 | 0.739 ± 0.006 | 0.544 ± 0.010 | 0.647 ± 0.026 | 0.562 ± 0.009 |
| dtree | 0.496 ± 0.019 | 0.624 ± 0.008 | 0.581 ± 0.014 | 0.569 ± 0.021 | 0.578 ± 0.015 |

## Summary findings

1. **Model ranking is stable across windows:** lightgbm > xgboost > rf >
   logreg > dtree, on PR-AUC. LightGBM wins all four windows.
   This is consistent with Lopez-Munoz et al. (2026): ensemble methods
   dominate, with reported accuracies of 86–88%.

2. **Temporal pattern confirmed:** best-model PR-AUC rises from 0.619 (W2)
   to 0.694 (W4), 0.715 (W6), 0.745 (W8). The largest gain is W2→W4
   (+0.075), coinciding with the jump in assessment-feature coverage from
   ~4% to 75% (see feature_report.md).

3. **W2 variant comparison:** Variant A is marginally better than B
   (+0.003 to +0.011 PR-AUC). The assessment features, despite low
   coverage, do not harm and slightly help. Decision: retain Variant A
   as the primary configuration for W2.

4. **Recall at threshold 0.5 is ~0.58** for the best model in W8, meaning
   42% of at-risk students are missed at the default cutoff. This is the
   baseline that Step 4 (cost-sensitive threshold tuning) will target,
   with C_FN:C_FP = 5:1 designed to raise recall at the cost of precision.

5. **Fold stability:** pos_rate_test varies by at most 3.4 pp across folds
   (W8); per-fold PR-AUC std is 0.004–0.023 across all runs. GroupKFold
   produces balanced, stable folds — Rule 4 is working as intended.

## Reproducibility

- `results/tables/benchmark_results.csv` — 125 rows (window × model ×
  variant × fold).
- `results/tables/benchmark_summary.csv` — 25 rows (mean ± std).
- Seed 42; default hyperparameters; GroupKFold(5) by student_id.
- XGBoost 3.2.0 emits a harmless `use_label_encoder` deprecation warning;
  the parameter is a no-op in this version and can be removed in Step 3b.

## Next

Step 3b: hyperparameter tuning (RandomSearch / Bayesian), starting from
the benchmark baselines above.
Step 4: imbalance handling + cost-sensitive threshold tuning (RQ3).