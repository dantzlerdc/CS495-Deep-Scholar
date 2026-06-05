#!/usr/bin/env python3
"""
make_slide12_preview.py
Generates the three presentation figures referenced by the
"Cross-Model & Backtest" slides (12, 13, 14) of
CS495_Capstone_Presentation.tex:

    slides/figures/slide12_cross_val.png   — L1 vs L2 cross-validation
                                              (copy of existing PNG;
                                              chart was visually OK)
    slides/figures/slide12_regime.png      — Regime analysis with FIXED
                                              y-axis clipping (the original
                                              had a COVID outlier dominating
                                              the y-range, hiding the actual
                                              regime structure)
    slides/figures/slide12_backtest.png    — Walk-forward backtest with FIXED
                                              histogram (the original had
                                              53k+ zero-P&L "no-trade" rows
                                              squashing one bin to dominate,
                                              hiding the actual executed-trade
                                              distribution)

These are tracked presentation assets (committed to git) — distinct
from the pipeline outputs in project/outputs/ which are regenerated
by `make run-all` and gitignored.

Run:
    .venv/bin/python make_slide12_preview.py
"""
import os
import sys
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Import the project's regime utilities
sys.path.insert(0, str(Path(__file__).parent / "project"))
from market_data    import load_prepared
from bias_detector  import compute_atm_iv, compute_regime, \
                           NORMAL_THRESHOLD, HERDING_THRESHOLD

OUT_DIR = Path(__file__).parent / "slides" / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_OUTPUTS = Path(__file__).parent / "project" / "outputs"

# ── Color palette (matches slide-9 figures) ──────────────────────────────────
BG_WHITE   = "#FFFFFF"
NAVY_DARK  = "#0B2041"
NAVY_MID   = "#163A8C"
SKY_BLUE   = "#3A7BD5"
LABEL_BLUE = "#88B8E8"
DESC_BLUE  = "#C8DCF0"
FOREST     = "#145A22"
BURNT_ORG  = "#7A1E00"
GOLD       = "#F57F17"
DEEP_RED   = "#C62828"
SILVER     = "#546E7A"


# ════════════════════════════════════════════════════════════════════════════
# PLOT 1 — L1 vs L2 cross-validation (copy existing as-is)
# ════════════════════════════════════════════════════════════════════════════
def preview_cross_val():
    src = PROJECT_OUTPUTS / "l1_vs_l2_comparison.png"
    dst = OUT_DIR / "slide12_cross_val.png"
    shutil.copy(src, dst)
    print(f"  Copied {src.name} -> {dst.name}")


# ════════════════════════════════════════════════════════════════════════════
# PLOT 2 — Regime analysis with FIXED y-axis clipping
# ════════════════════════════════════════════════════════════════════════════
def preview_regime():
    print("  Loading AAPL data (10% sample) for regime computation ...")
    df = load_prepared(sample_frac=0.10)

    print("  Computing ATM IV / RV30 / regime classification ...")
    daily      = compute_atm_iv(df)
    daily_reg  = compute_regime(daily)

    dates  = pd.to_datetime(daily_reg["QUOTE_DATE"])
    iv     = daily_reg["ATM_IV"].values
    rv     = daily_reg["RV30"].values
    spread = daily_reg["rv_iv_spread"].values
    regime = daily_reg["regime"].values

    # ── Identify outlier days (COVID) for annotation ─────────────────────────
    VOL_CLIP    = 1.30      # top-panel y-axis ceiling
    SPREAD_CLIP = 0.35      # middle-panel y-axis bound (positive & negative)

    rv_peak_idx = int(np.nanargmax(rv))
    rv_peak_val = float(rv[rv_peak_idx])
    rv_peak_dt  = dates.iloc[rv_peak_idx].strftime("%b %Y")

    spread_min_idx = int(np.nanargmin(spread))
    spread_min_val = float(spread[spread_min_idx])
    spread_min_dt  = dates.iloc[spread_min_idx].strftime("%b %Y")

    fig, axes = plt.subplots(3, 1, figsize=(12, 8.5), sharex=True,
                             gridspec_kw={"height_ratios": [3.0, 2.5, 1.0]})
    fig.patch.set_facecolor(BG_WHITE)
    fig.suptitle("Crowd Bias Regime Analysis  —  AAPL 2016–2021  "
                 "(y-axes clipped to reveal regime structure)",
                 fontsize=13, fontweight="bold", y=0.99)

    # ── Panel 1 ── ATM IV vs RV30 ────────────────────────────────────────────
    ax = axes[0]
    ax.set_facecolor(BG_WHITE)
    ax.plot(dates, iv, label="ATM IV",  color=NAVY_MID, lw=1.0)
    ax.plot(dates, rv, label="RV-30d",  color=DEEP_RED, lw=1.0)
    ax.axhline(0, color="gray", lw=0.5)
    ax.set_ylim(0, VOL_CLIP)
    ax.set_ylabel("Volatility (annualized)", fontsize=10)
    ax.set_title("Implied vs Realized Volatility", fontsize=10)
    ax.legend(loc="upper left", fontsize=9, facecolor=BG_WHITE,
              edgecolor="#CBD5E1")
    ax.grid(True, alpha=0.25)

    # Annotate the off-chart RV30 peak
    ax.annotate(
        f"RV-30d peak ≈ {rv_peak_val:.1f}\n({rv_peak_dt}, clipped)",
        xy=(dates.iloc[rv_peak_idx], VOL_CLIP * 0.95),
        xytext=(dates.iloc[rv_peak_idx], VOL_CLIP * 0.65),
        fontsize=8, color=DEEP_RED, ha="center",
        arrowprops=dict(arrowstyle="->", color=DEEP_RED, lw=1.0),
        bbox=dict(boxstyle="round,pad=0.3", facecolor=BG_WHITE,
                  edgecolor=DEEP_RED, alpha=0.95))

    # ── Panel 2 ── RV-IV Spread, herding band shaded ─────────────────────────
    ax = axes[1]
    ax.set_facecolor(BG_WHITE)
    ax.fill_between(dates, spread, 0,
                    where=(spread > 0),
                    color=GOLD,   alpha=0.45,
                    label="IV > RV  (herding bias zone)")
    ax.fill_between(dates, spread, 0,
                    where=(spread <= 0),
                    color=FOREST, alpha=0.30,
                    label="IV ≤ RV  (normal zone)")
    ax.axhline(HERDING_THRESHOLD,  color=DEEP_RED,  lw=1.0, ls="--",
               label=f"Herding threshold ({HERDING_THRESHOLD:.0%})")
    ax.axhline(NORMAL_THRESHOLD,   color=NAVY_MID,  lw=0.8, ls="--",
               alpha=0.7,
               label=f"Normal threshold ({NORMAL_THRESHOLD:.0%})")
    ax.axhline(-NORMAL_THRESHOLD,  color=NAVY_MID,  lw=0.8, ls="--",
               alpha=0.7)
    ax.set_ylim(-SPREAD_CLIP, SPREAD_CLIP)
    ax.set_ylabel("RV − IV spread", fontsize=10)
    ax.set_title("RV−IV Spread  (positive = IV above RV = crowd "
                 "overpricing volatility)", fontsize=10)
    ax.legend(loc="lower left", fontsize=7.5, facecolor=BG_WHITE,
              edgecolor="#CBD5E1", ncol=2)
    ax.grid(True, alpha=0.25)

    # Annotate the off-chart deep negative excursion
    ax.annotate(
        f"Spread trough ≈ {spread_min_val:.1f}\n({spread_min_dt}, clipped)",
        xy=(dates.iloc[spread_min_idx], -SPREAD_CLIP * 0.95),
        xytext=(dates.iloc[spread_min_idx], -SPREAD_CLIP * 0.55),
        fontsize=8, color=FOREST, ha="center",
        arrowprops=dict(arrowstyle="->", color=FOREST, lw=1.0),
        bbox=dict(boxstyle="round,pad=0.3", facecolor=BG_WHITE,
                  edgecolor=FOREST, alpha=0.95))

    # ── Panel 3 ── Regime classification ribbon ──────────────────────────────
    ax = axes[2]
    ax.set_facecolor(BG_WHITE)
    regime_num = (regime == "herding").astype(int)
    ax.fill_between(dates, regime_num, step="post",
                    color=BURNT_ORG, alpha=0.75, label="Herding")
    ax.fill_between(dates, 1 - regime_num, step="post",
                    color=FOREST,    alpha=0.35, label="Normal")
    ax.set_yticks([0.5, 1.0])
    ax.set_yticklabels(["Normal", "Herding"])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Regime", fontsize=10)
    ax.set_title("Detected Market Regime  (per trading day)", fontsize=10)
    ax.legend(loc="upper right", fontsize=8, facecolor=BG_WHITE,
              edgecolor="#CBD5E1")

    n_herding = int(regime_num.sum())
    n_total   = int(len(regime_num))
    ax.text(0.005, -0.30, f"Herding: {n_herding}/{n_total} days "
                          f"({100*n_herding/n_total:.1f}%)",
            transform=ax.transAxes, fontsize=8.5, color="#475569")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "slide12_regime.png",
                dpi=150, facecolor=BG_WHITE, bbox_inches="tight")
    plt.close()
    print("  Saved slide12_regime.png")


# ════════════════════════════════════════════════════════════════════════════
# PLOT 3 — Walk-forward backtest with FIXED histogram
# ════════════════════════════════════════════════════════════════════════════
def preview_backtest():
    print("  Loading backtest_trades.csv ...")
    df = pd.read_csv(PROJECT_OUTPUTS / "backtest_trades.csv")
    df["date"] = pd.to_datetime(df["date"])

    # Filter to actually executed trades (drop the 53k "no-trade" zero rows)
    executed = df[df["trade_pnl"] != 0].copy()
    n_executed = len(executed)
    n_total    = len(df)

    # Cumulative P&L (recomputed from executed trades only so it’s self-consistent)
    executed = executed.sort_values("date").reset_index(drop=True)
    executed["cum_pnl"] = executed["trade_pnl"].cumsum()

    pnl = executed["trade_pnl"].values
    mean_pnl   = float(np.mean(pnl))
    median_pnl = float(np.median(pnl))
    hit_rate   = float((pnl > 0).mean()) * 100

    # ── Figure layout ────────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 1, figsize=(12, 7.5),
                             gridspec_kw={"height_ratios": [1.4, 1.0]})
    fig.patch.set_facecolor(BG_WHITE)
    fig.suptitle("Walk-Forward Backtest  —  P&L Summary  "
                 "(AAPL 2017–2021, quarter-Kelly sizing)",
                 fontsize=13, fontweight="bold", y=0.995)

    # ── Top panel ── Cumulative P&L curve ────────────────────────────────────
    ax = axes[0]
    ax.set_facecolor(BG_WHITE)
    ax.plot(executed["date"], executed["cum_pnl"] / 1e6,
            color=NAVY_MID, lw=1.4)
    ax.fill_between(executed["date"], executed["cum_pnl"] / 1e6, 0,
                    where=(executed["cum_pnl"] >= 0),
                    color=FOREST, alpha=0.30, label="Cumulative profit")
    ax.fill_between(executed["date"], executed["cum_pnl"] / 1e6, 0,
                    where=(executed["cum_pnl"] <  0),
                    color=DEEP_RED, alpha=0.30, label="Cumulative loss")
    ax.axhline(0, color="gray", lw=0.6)
    ax.set_ylabel("Cumulative P&L ($ millions)", fontsize=10)
    ax.set_title("Cumulative P&L over the walk-forward test window",
                 fontsize=10)
    ax.legend(loc="upper left", fontsize=9, facecolor=BG_WHITE,
              edgecolor="#CBD5E1")
    ax.grid(True, alpha=0.25)

    final_pnl = executed["cum_pnl"].iloc[-1] / 1e6
    ax.annotate(f"Terminal: ${final_pnl:.2f}M",
                xy=(executed["date"].iloc[-1], final_pnl),
                xytext=(-110, -20), textcoords="offset points",
                fontsize=10, fontweight="bold", color=FOREST,
                bbox=dict(boxstyle="round,pad=0.4", facecolor=BG_WHITE,
                          edgecolor=FOREST, alpha=0.95))

    # ── Bottom panel ── FIXED histogram (executed trades only) ───────────────
    ax = axes[1]
    ax.set_facecolor(BG_WHITE)

    # Clip extreme tails for visualization (1%/99%) but report full count
    q01, q99 = np.quantile(pnl, [0.01, 0.99])
    HIST_LO, HIST_HI = -5000, 5000
    n_bins = 80

    # Split into wins and losses for colored bars
    pnl_wins   = pnl[pnl > 0]
    pnl_losses = pnl[pnl < 0]

    edges = np.linspace(HIST_LO, HIST_HI, n_bins + 1)
    ax.hist(pnl_losses, bins=edges, color=DEEP_RED, alpha=0.65,
            edgecolor="white", linewidth=0.5,
            label=f"Losses ({len(pnl_losses):,})")
    ax.hist(pnl_wins,   bins=edges, color=FOREST,   alpha=0.70,
            edgecolor="white", linewidth=0.5,
            label=f"Wins   ({len(pnl_wins):,})")

    ax.axvline(mean_pnl,   color=GOLD,     lw=2.0, ls="--",
               label=f"Mean   = ${mean_pnl:,.0f}")
    ax.axvline(median_pnl, color=NAVY_MID, lw=1.5, ls=":",
               label=f"Median = ${median_pnl:,.0f}")
    ax.axvline(0, color="gray", lw=0.6)

    ax.set_xlim(HIST_LO, HIST_HI)
    ax.set_xlabel("Per-trade P&L ($)", fontsize=10)
    ax.set_ylabel("Number of trades", fontsize=10)
    ax.set_title(f"Per-trade P&L distribution  "
                 f"(executed trades only: {n_executed:,} of {n_total:,};  "
                 f"hit rate = {hit_rate:.1f}%)",
                 fontsize=10)
    ax.legend(loc="upper right", fontsize=8.5, facecolor=BG_WHITE,
              edgecolor="#CBD5E1")
    ax.grid(True, axis="y", alpha=0.25)

    plt.tight_layout()
    plt.savefig(OUT_DIR / "slide12_backtest.png",
                dpi=150, facecolor=BG_WHITE, bbox_inches="tight")
    plt.close()
    print("  Saved slide12_backtest.png")


if __name__ == "__main__":
    print("Generating slide-12 plot previews ...")
    preview_cross_val()
    preview_regime()
    preview_backtest()
    print(f"\nAll three previews saved to: {OUT_DIR}")
