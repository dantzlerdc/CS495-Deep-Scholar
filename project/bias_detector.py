"""
bias_detector.py -- Layer 2, Step 3
Classify each trading day as normal or herding regime using:
  - RV-IV spread (primary signal)
  - IV momentum (3-day and 5-day change in ATM IV)
  - Volume spike indicator
Outputs a regime label per date used by policy.py.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NORMAL_THRESHOLD  = 0.05   # |RV-IV spread| < 5%  => normal
HERDING_THRESHOLD = 0.10   # RV-IV spread  > 10%  => herding


def compute_atm_iv(df):
    """
    Select the nearest-ATM strike per quote date (smallest STRIKE_DISTANCE_PCT)
    and return average of call and put IV as ATM_IV.
    """
    atm = (df.sort_values("STRIKE_DISTANCE_PCT")
             .groupby("QUOTE_DATE")
             .first()
             .reset_index())
    atm["ATM_IV"] = (atm["C_IV"].fillna(0) + atm["P_IV"].fillna(0)) / 2
    return atm[["QUOTE_DATE", "ATM_IV", "RV30"]].drop_duplicates("QUOTE_DATE")


def compute_regime(daily):
    """
    Given a daily DataFrame with ATM_IV and RV30, compute regime signals
    and return a regime label: 'normal' or 'herding'.
    """
    d = daily.copy().sort_values("QUOTE_DATE").reset_index(drop=True)
    d["rv_iv_spread"]  = d["ATM_IV"] - d["RV30"]
    d["iv_mom_3d"]     = d["ATM_IV"].diff(3)
    d["iv_mom_5d"]     = d["ATM_IV"].diff(5)

    # Herding: IV well above RV AND accelerating upward
    herding_mask = (
        (d["rv_iv_spread"] > HERDING_THRESHOLD) |
        ((d["iv_mom_3d"] > 0.05) & (d["rv_iv_spread"] > NORMAL_THRESHOLD))
    )
    d["regime"] = np.where(herding_mask, "herding", "normal")
    return d


def min_edge_for_regime(regime_label):
    """Return the minimum edge threshold appropriate for the regime."""
    return 0.08 if regime_label == "herding" else 0.02


def plot_regime(daily, path=None):
    if path is None:
        path = os.path.join(OUTPUT_DIR, "regime_analysis.png")

    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
    fig.suptitle("Crowd Bias Regime Analysis", fontsize=13, fontweight="bold")

    dates = daily["QUOTE_DATE"]

    # Panel 1 -- ATM IV vs RV30
    axes[0].plot(dates, daily["ATM_IV"], label="ATM IV",  color="#2563EB", lw=1.2)
    axes[0].plot(dates, daily["RV30"],   label="RV-30d",  color="#DC2626", lw=1.2)
    axes[0].axhline(0, color="gray", lw=0.5)
    axes[0].set_ylabel("Volatility")
    axes[0].legend(fontsize=8)
    axes[0].set_title("Implied vs Realized Volatility")

    # Panel 2 -- RV-IV spread
    spread = daily["rv_iv_spread"]
    axes[1].fill_between(dates, spread, 0,
                         where=(spread > 0), color="#FBBF24", alpha=0.5,
                         label="IV > RV (herding zone)")
    axes[1].fill_between(dates, spread, 0,
                         where=(spread <= 0), color="#6EE7B7", alpha=0.4,
                         label="IV <= RV (normal zone)")
    axes[1].axhline(HERDING_THRESHOLD,  color="red",   lw=0.8, ls="--",
                    label=f"Herding threshold ({HERDING_THRESHOLD:.0%})")
    axes[1].axhline(NORMAL_THRESHOLD,   color="green", lw=0.8, ls="--",
                    label=f"Normal threshold ({NORMAL_THRESHOLD:.0%})")
    axes[1].set_ylabel("RV-IV Spread")
    axes[1].legend(fontsize=7)
    axes[1].set_title("RV-IV Spread (positive = IV above RV)")

    # Panel 3 -- Regime state
    regime_num = (daily["regime"] == "herding").astype(int)
    axes[2].fill_between(dates, regime_num, step="post",
                         color="#7C3AED", alpha=0.6, label="Herding")
    axes[2].fill_between(dates, 1 - regime_num, step="post",
                         color="#059669", alpha=0.3, label="Normal")
    axes[2].set_yticks([0, 1])
    axes[2].set_yticklabels(["Normal", "Herding"])
    axes[2].set_ylabel("Regime")
    axes[2].legend(fontsize=8)
    axes[2].set_title("Detected Market Regime")

    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved regime plot -> {path}")


if __name__ == "__main__":
    from market_data import load_prepared
    print("Loading dataset (10% sample) ...")
    df = load_prepared(sample_frac=0.1)

    print("Computing ATM IV per day ...")
    daily = compute_atm_iv(df)
    daily = compute_regime(daily)

    herding_days = (daily["regime"] == "herding").sum()
    total_days   = len(daily)
    print(f"  Total days   : {total_days}")
    print(f"  Herding days : {herding_days} ({herding_days/total_days:.1%})")
    print(f"  Normal  days : {total_days - herding_days} "
          f"({(total_days-herding_days)/total_days:.1%})")

    print("Generating regime plot ...")
    plot_regime(daily)
    print("\nSample regime labels:")
    print(daily[["QUOTE_DATE", "ATM_IV", "RV30",
                 "rv_iv_spread", "regime"]].tail(10).to_string())
