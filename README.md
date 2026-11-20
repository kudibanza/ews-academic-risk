# EWS — Early Warning System (OULAD benchmark)
- source .venv/bin/activate
- deactivate
Master's thesis project: Design and implementation of an Early Warning
System for student academic risk and dropout prediction using machine
learning.

## Status
- Protocol frozen: v1.0.1 (2026-11-09)
- Current phase: Step 0 completed (scientific contract + project skeleton)

## Frozen scientific decisions
1. Primary target: `Withdrawn ∪ Fail` vs. `{Pass, Distinction}`.
   Secondary target (exploratory): `Withdrawn` only.
2. Observation windows: W2=14d, W4=28d, W6=42d, W8=56d.
3. Operational exclusion: `date_unregistration <= cutoff` → exclude.
4. Zero-leakage: Rules 1–4 (see `config/protocol.yaml` §6).
5. Validation: GroupKFold(5) by `student_id` + cross-cohort 2013→2014.
6. Cost ratio: 5:1 primary; 3:1 and 10:1 sensitivity.
7. Global seed: 42.

## How to reproduce (to be filled in subsequent steps)
- Step 1: data acquisition and audit — see `experiments/01_data_audit/`.
- Step 2: feature engineering and zero-leakage asserts.
- Step 3: model benchmarking (RQ2).
- Step 4: imbalance and cost-sensitive threshold tuning (RQ3).
- Step 5: SHAP caching (RQ4).
- Step 6: cross-cohort generalization.
- Step 7: web prototype contract and implementation (RQ5).
- Step 8: SCS evaluation session with academic coordinators.

## Structure