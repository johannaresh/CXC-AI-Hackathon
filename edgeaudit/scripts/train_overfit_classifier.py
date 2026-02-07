"""
Train XGBoost Overfit Classifier on synthetic labeled strategies.

Usage:
    python -m scripts.train_overfit_classifier
"""

import json
import pickle
import sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score
import xgboost as xgb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.services.feature_engineering import build_feature_vector, FEATURE_NAMES
from backend.app.models.strategy_encoder import get_reconstruction_error

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MODEL_DIR = DATA_DIR / "models"


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Load training data
    data_path = DATA_DIR / "synthetic" / "training_strategies.json"
    with open(data_path) as f:
        strategies = json.load(f)
    print(f"Loaded {len(strategies)} strategies")

    # Load scaler for reconstruction error
    scaler_path = MODEL_DIR / "feature_scaler.pkl"
    has_encoder = scaler_path.exists()
    if has_encoder:
        print("VAE encoder found — computing reconstruction errors")
    else:
        print("No VAE encoder found — using reconstruction_error=0.0")

    # Compute features
    X_list = []
    y_list = []
    for strat in strategies:
        feat = build_feature_vector(strat)

        # Compute reconstruction error from VAE if available
        if has_encoder:
            feat_array = [feat[name] for name in FEATURE_NAMES[:19]] + [0.0]
            recon_err = get_reconstruction_error(feat_array)
            feat["reconstruction_error"] = recon_err

        row = [feat[name] for name in FEATURE_NAMES]
        X_list.append(row)
        y_list.append(1 if strat["is_overfit"] else 0)

    X = np.array(X_list, dtype=np.float64)
    y = np.array(y_list, dtype=np.int32)

    print(f"Feature matrix: {X.shape}")
    print(f"Class distribution: {np.bincount(y)} (0=clean, 1=overfit)")

    # Train XGBoost
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42,
    )

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    auc_scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc")
    print(f"\n5-Fold CV AUC-ROC: {auc_scores.mean():.4f} (+/- {auc_scores.std():.4f})")

    # Final training on full dataset
    model.fit(X, y)

    # Evaluate on full training set (for reference)
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1]
    print(f"\nFull dataset AUC-ROC: {roc_auc_score(y, y_proba):.4f}")
    print("\nClassification Report:")
    print(classification_report(y, y_pred, target_names=["clean", "overfit"]))

    # Feature importance
    importances = model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    print("Top 10 Features by Importance:")
    for i in sorted_idx[:10]:
        print(f"  {FEATURE_NAMES[i]:30s} {importances[i]:.4f}")

    # Save model
    model_path = MODEL_DIR / "overfit_xgb.json"
    model.save_model(str(model_path))
    print(f"\nSaved XGBoost model -> {model_path}")


if __name__ == "__main__":
    main()
