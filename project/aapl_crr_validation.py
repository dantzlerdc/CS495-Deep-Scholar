"""
aapl_crr_validation.py -- Layer 1 x Layer 2 Cross-Validation
Compare CRR binomial tree predictions against actual AAPL market prices
using the Kaggle 2016-2020 historical options dataset.

Two comparisons are made for each contract:
  1. CRR(sigma=IV)   vs V_market  -- IV is calibrated FROM market price, so
                                      CRR should reproduce the market closely.
                                      This validates that the tree is correct.
  2. CRR(sigma=RV30) vs V_market  -- RV30 is the physical realized volatility.
                                      When market IV >> RV30, the crowd is
                                      overpricing the option (vol risk premium /
                                      herding regime). This is the Layer 2 edge.

Saves aapl_crr_validation.png to project/outputs/.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from market_data import load_prepared
from tree import price_american_option

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

N_STEPS  = 50     # CRR steps -- converges to Black-Scholes within ~0.1%
R        = 0.02   # approx avg risk-free rate 2016-2020 (Fed Funds ~0.5-2.5%)
N_SAMPLE = 1500   # rows per option type (call + put = 3000 CRR evaluations)


def crr_price(S, K, sigma, T, option_type):
    """Run CRR tree for one contract. Returns NaN on invalid inputs."""
    if sigma <= 0 or T < 1 / 365 or S <= 0 or K <= 0:
        return np.nan
    try:
        price, _ = price_american_option(S, K, R, sigma, T, N_STEPS, option_type)
        return max(price, 0.0)
    except Exception:
        return np.nan


def validate_option_type(df, option_type):
    """
    For calls or puts: compute V_model_iv, V_model_rv, and V_market.
    Returns a filtered DataFrame with error and edge columns added.
    """
    if option_type == "call":
        bid_col, ask_col, iv_col = "C_BID", "C_ASK", "C_IV"
    else:
        bid_col, ask_col, iv_col = "P_BID", "P_ASK", "P_IV"

    mask = (
        (df[bid_col] > 0) & (df[ask_col] > 0) &
        (df[iv_col]  > 0.01) &
        (df["RV30"]  > 0.01) &
        (df["DTE"]   >= 5) &
        (df["UNDERLYING_LAST"] > 0) &
        (df["STRIKE"] > 0)
    )
    pool = df[mask]
    n    = min(N_SAMPLE, len(pool))
    sub  = pool.sample(n, random_state=42).copy()
    print(f"  Evaluating {n} {option_type} contracts ...")

    sub["V_market"]   = (sub[bid_col] + sub[ask_col]) / 2.0
    sub["T_years"]    = sub["DTE"] / 365.0

    sub["V_model_iv"] = [
        crr_price(row.UNDERLYING_LAST, row.STRIKE,
                  row[iv_col], row.T_years, option_type)
        for _, row in sub.iterrows()
    ]
    sub["V_model_rv"] = [
        crr_price(row.UNDERLYING_LAST, row.STRIKE,
                  row.RV30, row.T_years, option_type)
        for _, row in sub.iterrows()
    ]

    sub = sub.dropna(subset=["V_model_iv", "V_model_rv", "V_market"])
    sub = sub[sub["V_market"] > 0.05]   # drop near-zero prices (OTM noise)

    sub["error_iv"]     = sub["V_model_iv"] - sub["V_market"]
    sub["pct_error_iv"] = sub["error_iv"] / sub["V_market"] * 100
    sub["edge_rv"]      = (sub["V_model_rv"] - sub["V_market"]) / sub["V_market"] * 100
    sub["option_type"]  = option_type
    return sub


def print_summary(res, option_type):
    label = option_type.upper()
    iv_mae  = res["error_iv"].abs().mean()
    iv_rmse = np.sqrt((res["error_iv"] ** 2).mean())
    iv_mpe  = res["pct_error_iv"].mean()
    iv_std  = res["pct_error_iv"].std()
    edge_mean = res["edge_rv"].mean()
    edge_std  = res["edge_rv"].std()
    within_5  = (res["pct_error_iv"].abs() < 5).mean() * 100
    within_10 = (res["pct_error_iv"].abs() < 10).mean() * 100

    print(f"\n  [{label}] CRR(IV) vs Market:")
    print(f"    MAE          : ${iv_mae:.4f}")
    print(f"    RMSE         : ${iv_rmse:.4f}")
    print(f"    Mean % error : {iv_mpe:.2f}%  (std {iv_std:.2f}%)")
    print(f"    Within  5%   : {within_5:.1f}% of contracts")
    print(f"    Within 10%   : {within_10:.1f}% of contracts")
    print(f"\n  [{label}] CRR(RV30) vs Market (vol premium):")
    print(f"    Mean edge    : {edge_mean:.2f}%  (std {edge_std:.2f}%)")
    print(f"    Negative edge: {(res['edge_rv'] < 0).mean()*100:.1f}% of contracts "
          f"(market overprices)")


def plot_validation(call_res, put_res):
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    fig.suptitle(
        "CRR Binomial Tree vs AAPL Historical Market Prices (2016-2020)",
        fontsize=13, fontweight="bold"
    )

    colors = {"call": "#2563EB", "put": "#7C3AED"}

    for row_idx, (res, label) in enumerate(
            [(call_res, "Call"), (put_res, "Put")]):
        col = colors[label.lower()]

        # Panel 1 -- CRR(IV) vs V_market scatter
        ax = axes[row_idx][0]
        lim_max = min(res["V_market"].quantile(0.97),
                      res["V_model_iv"].quantile(0.97))
        ax.scatter(res["V_market"], res["V_model_iv"],
                   alpha=0.15, s=6, color=col)
        ax.plot([0, lim_max], [0, lim_max], "r--", lw=1.2, label="Perfect fit")
        ax.set_xlim(0, lim_max)
        ax.set_ylim(0, lim_max)
        ax.set_xlabel("V_market ($)")
        ax.set_ylabel("V_model_iv ($)")
        ax.set_title(f"{label}: CRR(IV) vs Market\n"
                     f"(IV is calibrated from market -- expects tight fit)")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

        # Panel 2 -- CRR(RV30) vs V_market scatter
        ax = axes[row_idx][1]
        ax.scatter(res["V_market"], res["V_model_rv"],
                   alpha=0.15, s=6, color="#F59E0B")
        ax.plot([0, lim_max], [0, lim_max], "r--", lw=1.2, label="Perfect fit")
        ax.set_xlim(0, lim_max)
        ax.set_ylim(0, lim_max)
        ax.set_xlabel("V_market ($)")
        ax.set_ylabel("V_model_rv ($)")
        ax.set_title(f"{label}: CRR(RV30) vs Market\n"
                     f"(RV30 is physical vol -- gap = vol risk premium)")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

        # Panel 3 -- % error distribution and vol premium
        ax = axes[row_idx][2]
        ax.hist(res["pct_error_iv"].clip(-50, 50), bins=60,
                color=col, alpha=0.6, label="CRR(IV) % error", density=True)
        ax.hist(res["edge_rv"].clip(-100, 20), bins=60,
                color="#F59E0B", alpha=0.5, label="CRR(RV30) edge %", density=True)
        ax.axvline(0, color="black", lw=1)
        ax.axvline(res["pct_error_iv"].mean(), color=col, lw=1.5, ls="--",
                   label=f"IV mean {res['pct_error_iv'].mean():.1f}%")
        ax.axvline(res["edge_rv"].mean(), color="#F59E0B", lw=1.5, ls="--",
                   label=f"RV mean {res['edge_rv'].mean():.1f}%")
        ax.set_xlabel("% difference from market price")
        ax.set_ylabel("Density")
        ax.set_title(f"{label}: Pricing Error Distribution")
        ax.legend(fontsize=7)
        ax.grid(alpha=0.3)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "aapl_crr_validation.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Saved -> {out_path}")


if __name__ == "__main__":
    print("Loading AAPL dataset (10% sample) ...")
    df = load_prepared(sample_frac=0.10)
    print(f"  {len(df):,} rows loaded\n")

    print("Running CRR validation (call options) ...")
    call_res = validate_option_type(df, "call")

    print("\nRunning CRR validation (put options) ...")
    put_res = validate_option_type(df, "put")

    print("\n=== Validation Summary ===")
    print_summary(call_res, "call")
    print_summary(put_res, "put")

    print("\nGenerating validation plot ...")
    plot_validation(call_res, put_res)
    print("\nDone.")
