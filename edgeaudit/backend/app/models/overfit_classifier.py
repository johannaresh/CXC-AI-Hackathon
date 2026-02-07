"""
Overfit Classifier — XGBoost model that predicts the probability
a given strategy is overfit to its backtest data.
"""

from pathlib import Path

import numpy as np

_MODEL_DIR = Path(__file__).resolve().parents[3] / "data" / "models"
_xgb_model = None


def _load_model():
    """Lazily load trained XGBoost model from disk."""
    global _xgb_model
    model_path = _MODEL_DIR / "overfit_xgb.json"
    if model_path.exists():
        import xgboost as xgb
        _xgb_model = xgb.XGBClassifier()
        _xgb_model.load_model(str(model_path))
    else:
        _xgb_model = None


def predict_overfit(features: dict) -> dict:
    """Return overfit probability for a strategy.

    Args:
        features: Dictionary of 20 engineered strategy features.

    Returns:
        Dict with probability, confidence, and label.
    """
    global _xgb_model
    if _xgb_model is None:
        _load_model()

    if _xgb_model is None:
        # No trained model — return conservative defaults
        return {
            "probability": 0.5,
            "confidence": 0.0,
            "label": "medium",
        }

    from ..services.feature_engineering import FEATURE_NAMES

    # Build ordered feature array
    feature_array = np.array(
        [features.get(name, 0.0) for name in FEATURE_NAMES],
        dtype=np.float64,
    ).reshape(1, -1)

    # Predict
    proba = _xgb_model.predict_proba(feature_array)[0]
    probability = float(proba[1])  # P(overfit)

    # Confidence = 1 - entropy (normalized)
    entropy = 0.0
    for p in proba:
        if p > 1e-10:
            entropy -= p * np.log2(p)
    confidence = float(1.0 - entropy)  # 0 = uncertain, 1 = certain

    if probability < 0.3:
        label = "low"
    elif probability < 0.6:
        label = "medium"
    else:
        label = "high"

    return {
        "probability": round(probability, 4),
        "confidence": round(confidence, 4),
        "label": label,
    }
