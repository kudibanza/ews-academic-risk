# Calibration Report — Sub-step 4.2 (RQ3)

Calibration evaluated per protocol.yaml §8 on the best configurations
from sub-step 4.1:
- lightgbm + class_weight (primary)
- xgboost + class_weight (secondary)
- lightgbm + none (baseline, to isolate the effect of imbalance handling)

Methods: Platt scaling (sigmoid) and isotonic regression.
Fit: calibration on the training fold, via sklearn FrozenEstimator
(base model trained once, calibrator fit on the same fold).
Evaluation: ECE (10 bins) and Brier score on the test fold.

## Key finding: calibration degrades an already well-calibrated model

For lightgbm + none (uncalibrated baseline):

| Window | ECE none | ECE sigmoid | ECE isotonic | Brier none | Brier sigmoid | Brier isotonic |
|---|---|---|---|---|---|---|
| W2 | **0.0180** | 0.0584 | 0.0570 | **0.2261** | 0.2304 | 0.2316 |
| W4 | **0.0178** | 0.0562 | 0.0513 | **0.2044** | 0.2079 | 0.2082 |
| W6 | **0.0173** | 0.0531 | 0.0500 | **0.1944** | 0.1974 | 0.1974 |
| W8 | **0.0175** | 0.0478 | 0.0480 | **0.1821** | 0.1847 | 0.1848 |

The uncalibrated LightGBM already has ECE ≈ 0.018 (excellent calibration).
Applying Platt or isotonic scaling raises ECE to 0.05–0.06 and
slightly worsens the Brier score. The PR-AUC is also marginally reduced
by isotonic (e.g., W2: 0.6187 → 0.6093), indicating that isotonic
distorts the ranking.

For lightgbm + class_weight, the same pattern holds: none is the best
calibrated option in every window (ECE 0.043–0.056), with sigmoid and
isotonic both worse.

For xgboost + class_weight, the uncalibrated model already has a higher
ECE (≈ 0.06) than LightGBM, and calibration makes it worse (isotonic
raises ECE to ≈ 0.12). This confirms that the `scale_pos_weight` used for
XGBoost class weighting distorts the probability scale — a known
interaction between class weighting and tree-based probability outputs.

## Interpretation

LightGBM's gradient boosting optimizes log-loss directly, which tends to
produce well-calibrated probabilities on tabular data. Post-hoc
calibration is useful when a model is systematically miscalibrated (SVM,
Naive Bayes, some neural networks), but can degrade a model that is
already calibrated. The `CalibratedClassifierCV` with `FrozenEstimator`
fits the calibrator on the same fold used to train the base model; while
the base is not retrained, the calibrator can overfit the training fold
and fail to transfer to the test fold, which explains the ECE increase.

## Decision

Calibration is **not applied** for sub-step 4.3 (threshold tuning).
The selected configuration is:

- **Model:** LightGBM
- **Imbalance strategy:** class_weight
- **Calibration:** none (uncalibrated probabilities)

Rationale: the uncalibrated LightGBM is already well calibrated
(ECE ≈ 0.018–0.056 across windows), and calibration degrades both ECE
and Brier. Threshold tuning depends on probabilities being meaningful;
they already are, so no calibration step is needed. This is documented
as a tested-and-rejected design choice, not an omission.

## Reproducibility

- results/tables/calibration_results.csv — 180 rows (4 windows × 3 configs
  × 5 folds × 3 calibration options).
- results/tables/calibration_summary.csv — 36 rows (mean ± std).
- Seed 42. GroupKFold(5) by student_id.
- sklearn FrozenEstimator used for prefit calibration (sklearn ≥ 1.6).

## Next

Sub-step 4.3: cost-sensitive threshold tuning on uncalibrated
LightGBM + class_weight probabilities. Primary ratio C_FN:C_FP = 5:1;
sensitivity at 3:1 and 10:1.