"""
calibration.py -- Layer 2, Step 5
Evaluate probability model accuracy using:
  - Brier score (mean squared error of probability predictions)
  - Reliability diagram (calibration curve)
  - Expected Calibration Error (ECE)
Saves calibration_curve.png to project/outputs/.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

from market_data import load_prepared, CALL_FEATURES, PUT_FEATURES
from p_estimator import load as load_model, predict_p
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import brier_score_loss

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def expected_calibration_error(y_true, p_pred, n_bins=10):
    """Mean absolute deviation between predicted and actual frequencies."""
    bins = np.linspace(0, 1, n_bins + 1)
    ece  = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (p_pred >= lo) & (p_pred < hi)
        if mask.sum() == 0:
            continue
        frac_pos  = y_true[mask].mean()
        mean_pred = p_pred[mask].mean()
        ece += mask.mean() * abs(frac_pos - mean_pred)
    return ece


def reliability_diagram_data(y_true, p_pred, n_bins=10):
    """Return arrays for plotting the reliability diagram."""
    bins       = np.linspace(0, 1, n_bins + 1)
    mean_pred  = []
    frac_pos   = []
    counts     = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (p_pred >= lo) & (p_pred < hi)
        if mask.sum() == 0:
            continue
        mean_pred.append(p_pred[mask].mean())
        frac_pos.append(y_true[mask].mean())
        counts.append(mask.sum())
    return np.array(mean_pred), np.array(frac_pos), np.array(counts)


def evaluate(y_true, p_pred, label="model", n_bins=10):
    bs    = brier_score_loss(y_true, p_pred)
    ece   = expected_calibration_error(y_true, p_pred, n_bins)
    naive = brier_score_loss(y_true, np.full_like(p_pred, 0.5))
    print(f"  [{label}]")
    print(f"    Brier score : {bs:.4f}  (naive baseline {naive:.4f})")
    print(f"    ECE         : {ece:.4f}")
    print(f"    Skill score : {1 - bs/naive:.3f}  (0=no skill, 1=perfect)")
    return {"brier": bs, "ece": ece, "naive": naive}


def plot_calibration(results, path=None):
    """
    results: list of dicts with keys:
      label, y_true, p_pred, color
    """
    if path is None:
        path = os.path.join(OUTPUT_DIR, "calibration_curve.png")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("Probability Calibration -- p_independent Model",
                 fontsize=13, fontweight="bold")

    for ax_idx, res in enumerate(results):
        ax = axes[ax_idx]
        mp, fp, counts = reliability_diagram_data(
            res["y_true"], res["p_pred"])
        bs  = brier_score_loss(res["y_true"], res["p_pred"])
        ece = expected_calibration_error(res["y_true"], res["p_pred"])

        ax.plot([0, 1], [0, 1], "k--", lw=1, label="Perfect calibration")
        ax.bar(mp, fp, width=0.08, alpha=0.4,
               color=res["color"], label="Actual frequency")
        ax.plot(mp, fp, "o-", color=res["color"], lw=1.5,
                label=f"Model  Brier={bs:.4f}  ECE={ece:.4f}")
        ax.set_xlabel("Mean Predicted Probability")
        ax.set_ylabel("Fraction Positive (Actual ITM Rate)")
        ax.set_title(res["label"])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved calibration curve -> {path}")


if __name__ == "__main__":
    print("Loading dataset (10% sample) ...")
    df = load_prepared(sample_frac=0.1)

    results = []
    for opt_type, features, label, color in [
        ("call", CALL_FEATURES, "call_itm", "#2563EB"),
        ("put",  PUT_FEATURES,  "put_itm",  "#7C3AED"),
    ]:
        print(f"\n--- {opt_type.upper()} calibration ---")
        bundle = load_model(opt_type)

        X = df[features].values
        y = df[label].values
        _, X_test, _, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y)
        X_test_scaled = bundle["scaler"].transform(X_test)
        p_pred = bundle["model"].predict_proba(X_test_scaled)[:, 1]

        evaluate(y_test, p_pred, label=opt_type.upper())
        results.append({
            "label": f"{opt_type.capitalize()} Option -- ITM Probability",
            "y_true": y_test,
            "p_pred": p_pred,
            "color":  color,
        })

    print("\nGenerating calibration curve plot ...")
    plot_calibration(results)
    print("Done.")
