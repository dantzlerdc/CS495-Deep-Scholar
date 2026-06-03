"""
layer1_vs_layer2.py -- Layer 1 vs Layer 2 Cross-Model Comparison (PLAN2.md)

Runs both the CRR binomial tree (Layer 1) and the XGBoost estimator (Layer 2)
on the same 3,000 AAPL contracts sampled from the Kaggle 2016-2020 dataset,
then generates a 4-panel comparison figure.

Edge signals:
  edge_L1 = (V_model_rv - V_market) / V_market   (CRR with sigma=RV30)
  edge_L2 = p_independent - q_market              (XGBoost vs market-implied prob)

Negative = market overprices; Positive = market underprices.
Both signals negative (Quadrant III) = strong SELL agreement.

Output: project/outputs/l1_vs_l2_comparison.png
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.path.insert(0, os.path.dirname(__file__))
from market_data import load_prepared, CALL_FEATURES, PUT_FEATURES
from tree import price_american_option
from p_estimator import load as load_model, predict_p
from bias_detector import compute_atm_iv, compute_regime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

N_STEPS  = 50
R        = 0.02
N_SAMPLE = 1500   # per option type


# ── Helpers ───────────────────────────────────────────────────────────────────

def crr_price(S, K, sigma, T, option_type):
    if sigma <= 0 or T < 1 / 365 or S <= 0 or K <= 0:
        return np.nan
    try:
        price, _ = price_american_option(S, K, R, sigma, T, N_STEPS, option_type)
        return max(price, 0.0)
    except Exception:
        return np.nan


def sample_contracts(df, option_type):
    if option_type == "call":
        bid_col, ask_col, iv_col = "C_BID", "C_ASK", "C_IV"
    else:
        bid_col, ask_col, iv_col = "P_BID", "P_ASK", "P_IV"

    mask = (
        (df[bid_col]  > 0) & (df[ask_col]  > 0) &
        (df[iv_col]   > 0.01) &
        (df["RV30"]   > 0.01) &
        (df["DTE"]    >= 5) &
        (df["UNDERLYING_LAST"] > 0) &
        (df["STRIKE"] > 0)
    )
    pool = df[mask]
    n    = min(N_SAMPLE, len(pool))
    return pool.sample(n, random_state=42).copy(), bid_col, ask_col, iv_col


# ── Layer 1 edge ──────────────────────────────────────────────────────────────

def compute_l1_edge(sub, bid_col, ask_col, iv_col, option_type):
    sub = sub.copy()
    sub["V_market"] = (sub[bid_col] + sub[ask_col]) / 2.0
    sub["T_years"]  = sub["DTE"] / 365.0

    print(f"  Computing CRR(RV30) for {len(sub):,} {option_type} contracts ...")
    sub["V_model_rv"] = [
        crr_price(row.UNDERLYING_LAST, row.STRIKE,
                  row.RV30, row.T_years, option_type)
        for _, row in sub.iterrows()
    ]

    sub = sub.dropna(subset=["V_model_rv", "V_market"])
    sub = sub[sub["V_market"] > 0.05]
    sub["edge_L1"] = (sub["V_model_rv"] - sub["V_market"]) / sub["V_market"]
    return sub


# ── Layer 2 edge ──────────────────────────────────────────────────────────────

def compute_l2_edge(sub, option_type):
    sub    = sub.copy()
    bundle = load_model(option_type)
    feats  = CALL_FEATURES if option_type == "call" else PUT_FEATURES

    # Drop rows missing any required feature
    sub = sub.dropna(subset=feats)
    X_raw = sub[feats].values

    p_ind = predict_p(bundle, X_raw)
    sub   = sub.copy()
    sub["p_independent"] = p_ind

    if option_type == "call":
        C_mid = (sub["C_BID"] + sub["C_ASK"]) / 2.0
        sub["q_market"] = (C_mid / sub["UNDERLYING_LAST"]).clip(0, 1)
    else:
        P_mid = (sub["P_BID"] + sub["P_ASK"]) / 2.0
        sub["q_market"] = (P_mid / sub["STRIKE"]).clip(0, 1)

    sub["edge_L2"] = sub["p_independent"] - sub["q_market"]
    return sub


# ── Regime labels ─────────────────────────────────────────────────────────────

def get_regime_map(df):
    daily      = compute_atm_iv(df)
    daily_reg  = compute_regime(daily)
    return daily_reg.set_index("QUOTE_DATE")["regime"].to_dict()


# ── Plotting ──────────────────────────────────────────────────────────────────

REGIME_COLORS = {"herding": "#DC2626", "normal": "#2563EB", "unknown": "#9CA3AF"}

def plot_comparison(combined):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        "Layer 1 (CRR) vs Layer 2 (XGBoost) — Cross-Model Comparison\n"
        "AAPL Options 2016-2020 · Same 3,000 Contracts",
        fontsize=13, fontweight="bold", y=0.99
    )

    # ── Panel 1: Edge Scatter ─────────────────────────────────────────────────
    ax = axes[0]
    for regime, grp in combined.groupby("regime"):
        c = REGIME_COLORS.get(regime, REGIME_COLORS["unknown"])
        ax.scatter(grp["edge_L1"], grp["edge_L2"],
                   alpha=0.18, s=7, color=c, label=regime)

    ax.axhline(0, color="black", lw=0.8, ls="--")
    ax.axvline(0, color="black", lw=0.8, ls="--")

    # Quadrant shading
    xlim = (-1.2, 0.6)
    ylim = (-0.8, 0.8)
    ax.fill_between([-1.2, 0], -0.8, 0, color="#FEE2E2", alpha=0.35, zorder=0)  # Q3
    ax.fill_between([0, 0.6], 0, 0.8,  color="#D1FAE5", alpha=0.35, zorder=0)   # Q1

    r, pval = pearsonr(combined["edge_L1"].clip(-2, 2),
                       combined["edge_L2"].clip(-1, 1))
    ax.text(0.03, 0.97, f"Pearson r = {r:.3f}  (p={pval:.2e})",
            transform=ax.transAxes, va="top", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.85))

    ax.text(-0.8, -0.55, "Q3\nBoth: SELL", fontsize=8, color="#991B1B",
            ha="center", fontweight="bold")
    ax.text(0.35, 0.55, "Q1\nBoth: BUY", fontsize=8, color="#065F46",
            ha="center", fontweight="bold")

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xlabel("Layer 1 Edge  (V_model_rv − V_market) / V_market", fontsize=10)
    ax.set_ylabel("Layer 2 Edge  p_independent − q_market", fontsize=10)
    ax.set_title("Panel 1 — Edge Scatter by Regime", fontsize=11, fontweight="bold")
    ax.legend(fontsize=9, markerscale=2)
    ax.grid(alpha=0.25)

    # ── Panel 2: Actual ITM Rate by Zone ─────────────────────────────────────
    ax = axes[1]
    itm_col = None
    for cand in ("call_itm", "put_itm", "itm"):
        if cand in combined.columns:
            itm_col = cand
            break

    if itm_col:
        zones = {
            "Both SELL\n(Q3)":       combined[(combined["edge_L1"] < 0) & (combined["edge_L2"] < 0)],
            "Both BUY\n(Q1)":        combined[(combined["edge_L1"] > 0) & (combined["edge_L2"] > 0)],
            "Disagree":              combined[~(
                                         ((combined["edge_L1"] < 0) & (combined["edge_L2"] < 0)) |
                                         ((combined["edge_L1"] > 0) & (combined["edge_L2"] > 0))
                                     )],
        }
        zone_names = list(zones.keys())
        itm_rates  = [grp[itm_col].mean() * 100 for grp in zones.values()]
        counts     = [len(grp) for grp in zones.values()]
        zone_cols  = ["#DC2626", "#059669", "#9CA3AF"]
        bars = ax.bar(zone_names, itm_rates, color=zone_cols, alpha=0.8, edgecolor="white")
        for bar, rate, cnt in zip(bars, itm_rates, counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                    f"{rate:.1f}%\n(n={cnt:,})", ha="center", va="bottom",
                    fontsize=9, fontweight="bold")
        ax.set_ylabel("Actual ITM Rate (%)", fontsize=10)
        ax.set_title("Panel 2 — Actual ITM Rate by Agreement Zone\n"
                     "(lower = market was overpriced, signal has predictive content)",
                     fontsize=10, fontweight="bold")
        ax.set_ylim(0, max(itm_rates) * 1.25)
        ax.grid(axis="y", alpha=0.3)
    else:
        ax.text(0.5, 0.5, "ITM outcome column not available\nin this sample subset",
                ha="center", va="center", transform=ax.transAxes, fontsize=10)
        ax.set_title("Panel 2 — Actual ITM Rate by Zone", fontsize=11, fontweight="bold")

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "l1_vs_l2_comparison.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Saved -> {out_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Loading AAPL dataset (10% sample) ...")
    df = load_prepared(sample_frac=0.10)
    print(f"  {len(df):,} rows loaded")

    print("\nBuilding regime map ...")
    regime_map = get_regime_map(df)

    results = []
    for opt_type in ("call", "put"):
        print(f"\n--- {opt_type.upper()} contracts ---")
        sub, bid_col, ask_col, iv_col = sample_contracts(df, opt_type)

        sub = compute_l1_edge(sub, bid_col, ask_col, iv_col, opt_type)
        print(f"  {len(sub):,} contracts after L1 filter")

        sub = compute_l2_edge(sub, opt_type)
        print(f"  {len(sub):,} contracts after L2 filter")

        sub["regime"] = sub["QUOTE_DATE"].map(regime_map).fillna("unknown")
        sub["option_type"] = opt_type

        # Assign the correct ITM column
        if opt_type == "call" and "call_itm" in sub.columns:
            sub["itm"] = sub["call_itm"]
        elif opt_type == "put" and "put_itm" in sub.columns:
            sub["itm"] = sub["put_itm"]

        results.append(sub)

    combined = pd.concat(results, ignore_index=True)
    print(f"\n=== Combined: {len(combined):,} contracts ===")

    q3_pct  = ((combined["edge_L1"] < 0) & (combined["edge_L2"] < 0)).mean() * 100
    q1_pct  = ((combined["edge_L1"] > 0) & (combined["edge_L2"] > 0)).mean() * 100
    r_all, _ = pearsonr(combined["edge_L1"].clip(-2, 2),
                        combined["edge_L2"].clip(-1, 1))

    print(f"  Overall Pearson r   : {r_all:.4f}")
    print(f"  Q3 (both SELL)      : {q3_pct:.1f}%")
    print(f"  Q1 (both BUY)       : {q1_pct:.1f}%")
    print(f"  Disagree            : {100 - q3_pct - q1_pct:.1f}%")

    for reg in ("normal", "herding"):
        grp = combined[combined["regime"] == reg]
        if len(grp) >= 10:
            rv, _ = pearsonr(grp["edge_L1"].clip(-2, 2),
                             grp["edge_L2"].clip(-1, 1))
            print(f"  Pearson r [{reg:8s}] : {rv:.4f}  (n={len(grp):,})")

    print("\nGenerating comparison plot ...")
    plot_comparison(combined)
    print("Done.")

    return combined


if __name__ == "__main__":
    main()
