"""
sklearn Pipeline construction with zero-leakage guarantees (Rule 1).
Imputation and scaling are fit only on the training fold.
"""
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

# Feature sets per protocol.yaml §5
FEATURES_FULL = [
    "S_vle", "D_active", "H_entropy", "Delta_t", "S_score", "click_trend",
]
FEATURES_W2_VARIANT_B = [
    "S_vle", "D_active", "H_entropy", "click_trend",
]
# still_registered is constant (=1) after exclusion; it carries no signal
# and is excluded from the model to avoid a zero-variance column.

MODELS = {
    "logreg": lambda: LogisticRegression(
        max_iter=1000, random_state=42, class_weight=None
    ),
    "dtree": lambda: DecisionTreeClassifier(random_state=42),
    "rf": lambda: RandomForestClassifier(
        n_estimators=100, random_state=42, n_jobs=-1
    ),
    "xgboost": lambda: XGBClassifier(
        n_estimators=100, random_state=42, n_jobs=-1,
        eval_metric="logloss",
    ),
    "lightgbm": lambda: LGBMClassifier(
        n_estimators=100, random_state=42, n_jobs=-1, verbose=-1,
    ),
}

SCALED_MODELS = {"logreg"}  # only linear models need scaling


def get_features(variant: str) -> list[str]:
    """Return the feature list for a given variant."""
    if variant == "A":
        return FEATURES_FULL
    if variant == "B":
        return FEATURES_W2_VARIANT_B
    raise ValueError(f"unknown variant: {variant}")


def build_pipeline(model_name: str, variant: str = "A") -> Pipeline:
    """
    Build a leakage-free Pipeline:
    - imputer fit only on training fold (Rule 1)
    - scaler fit only on training fold (Rule 1), only for scaled models
    The caller is responsible for splitting before calling fit().
    """
    if model_name not in MODELS:
        raise ValueError(f"unknown model: {model_name}")
    features = get_features(variant)
    steps = [
        ("imputer", SimpleImputer(strategy="median")),
    ]
    if model_name in SCALED_MODELS:
        steps.append(("scaler", StandardScaler()))
    steps.append(("model", MODELS[model_name]()))
    return Pipeline(steps)


def get_feature_names(variant: str = "A") -> list[str]:
    return get_features(variant)