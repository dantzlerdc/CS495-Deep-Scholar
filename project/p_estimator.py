"""
p_estimator.py -- Layer 2, Step 2
Train a gradient boosting classifier to estimate the probability that an
option expires ITM, independently of the market price.
Outputs p_independent -- the core edge signal for the trading policy.
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, log_loss

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

from market_data import load_prepared, CALL_FEATURES, PUT_FEATURES

MODEL_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(MODEL_DIR, exist_ok=True)

CALL_MODEL_PATH = os.path.join(MODEL_DIR, "call_model.pkl")
PUT_MODEL_PATH  = os.path.join(MODEL_DIR, "put_model.pkl")


def _build_model():
    if HAS_XGB:
        base = XGBClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
            verbosity=0,
        )
    else:
        print("  XGBoost not found -- using logistic regression baseline")
        base = LogisticRegression(max_iter=1000, random_state=42)
    # Platt scaling calibration wraps the base model
    return CalibratedClassifierCV(base, method="sigmoid", cv=3)


def train(df, option_type="call"):
    """Train and calibrate a probability model for calls or puts."""
    if option_type == "call":
        features, label = CALL_FEATURES, "call_itm"
    else:
        features, label = PUT_FEATURES, "put_itm"

    X = df[features].values
    y = df[label].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)

    print(f"  Training {option_type} model on {len(X_train):,} rows ...")
    model = _build_model()
    model.fit(X_train, y_train)

    p_test = model.predict_proba(X_test)[:, 1]
    bs  = brier_score_loss(y_test, p_test)
    ll  = log_loss(y_test, p_test)
    acc = ((p_test > 0.5) == y_test).mean()
    print(f"    Brier score : {bs:.4f}  (baseline 0.25)")
    print(f"    Log loss    : {ll:.4f}")
    print(f"    Accuracy    : {acc:.3f}")

    bundle = {"model": model, "scaler": scaler,
              "features": features, "label": label,
              "brier": bs, "test_size": len(y_test)}
    return bundle, X_test, y_test, p_test


def save(bundle, option_type="call"):
    path = CALL_MODEL_PATH if option_type == "call" else PUT_MODEL_PATH
    with open(path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"  Saved model -> {path}")


def load(option_type="call"):
    path = CALL_MODEL_PATH if option_type == "call" else PUT_MODEL_PATH
    with open(path, "rb") as f:
        return pickle.load(f)


def predict_p(bundle, X_raw):
    """Return calibrated p_independent for a feature matrix."""
    X_scaled = bundle["scaler"].transform(X_raw)
    return bundle["model"].predict_proba(X_scaled)[:, 1]


def compute_edge_independent(p_independent, q_market):
    """
    edge_independent = p_independent - q_market
    q_market is the market-implied probability: option_price / max_payoff.
    For a put: q_market = P_mid / STRIKE  (simplified)
    For a call: q_market = C_mid / UNDERLYING_LAST
    """
    return p_independent - q_market


if __name__ == "__main__":
    print("Loading dataset (10% sample for speed) ...")
    df = load_prepared(sample_frac=0.1)

    print("\n--- Call model ---")
    call_bundle, Xc_test, yc_test, pc_test = train(df, "call")
    save(call_bundle, "call")

    print("\n--- Put model ---")
    put_bundle, Xp_test, yp_test, pp_test = train(df, "put")
    save(put_bundle, "put")

    print("\nDone. Models saved to project/outputs/")
