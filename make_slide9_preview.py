#!/usr/bin/env python3
"""
make_slide9_preview.py
Generates the three presentation figures referenced by the
"CRR Pricing Results" slides (9, 10, 11) of
CS495_Capstone_Presentation.tex:

    slides/figures/slide9_residual.png
    slides/figures/slide9_convergence.png
    slides/figures/slide9_boundary.png

These are tracked presentation assets (committed to git) — distinct
from the pipeline outputs in project/outputs/ which are regenerated
by `make run-all` and gitignored.

Run:
    .venv/bin/python make_slide9_preview.py
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# Import the project's CRR pricer
sys.path.insert(0, str(Path(__file__).parent / "project"))
from tree import price_american_option

PREV_DIR = Path(__file__).parent / "slides" / "figures"
PREV_DIR.mkdir(parents=True, exist_ok=True)

# ── Color palette (matches the rest of the project) ──────────────────────────
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
BG_WHITE   = "#FFFFFF"


# ── Load the actual AMD data ─────────────────────────────────────────────────
EDGES = pd.read_csv(Path(__file__).parent / "project/outputs/edges.csv")
CHAIN = pd.read_csv(Path(__file__).parent / "project/outputs/chain.csv")


# ════════════════════════════════════════════════════════════════════════════
# PLOT 1 — Residual plot (replaces Model vs Market bar chart)
# ════════════════════════════════════════════════════════════════════════════
def preview_residual():
    """Residual (V_model − V_market) per ticket, with %-error annotations and
    the ±5% H1-acceptance band drawn for reference."""
    labels = [f"T{int(r.ticket_id)}\n{r.action[:1].upper()}{r.option_type[:1].upper()}\nK=${int(r.K)}"
              for _, r in EDGES.iterrows()]
    residuals = (EDGES["V_model"] - EDGES["V_market"]).values
    edge_pcts = EDGES["edge_pct"].values
    v_market  = EDGES["V_market"].values

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(BG_WHITE)
    ax.set_facecolor(BG_WHITE)

    x = np.arange(len(labels))
    colors = [FOREST if r >= 0 else DEEP_RED for r in residuals]
    bars = ax.bar(x, residuals, width=0.55, color=colors, alpha=0.85,
                  edgecolor="white", linewidth=1.5, zorder=3)

    # ±5% acceptance band (the H1 hypothesis tolerance)
    band_top = 0.05 * v_market.mean()
    band_bot = -band_top
    ax.axhspan(band_bot, band_top, color=SKY_BLUE, alpha=0.10, zorder=1,
               label="H1 acceptance band (±5%)")
    ax.axhline(0, color="black", lw=1.0, zorder=2)

    # Annotate each bar with dollar residual + percent error
    for xi, dr, ep in zip(x, residuals, edge_pcts):
        # The actual numerical residual is < $0.01, so display in cents-style
        dr_str = f"${dr:+.4f}"
        ep_str = f"{ep:+.3f}%"
        # Position annotation above zero line regardless of bar direction
        y_text = max(abs(band_top * 0.20), 0.005)
        ax.text(xi, y_text * 1.5, dr_str, ha="center", va="bottom",
                fontsize=10, fontweight="bold", color="#1A1A2E")
        ax.text(xi, -y_text * 1.5, ep_str, ha="center", va="top",
                fontsize=9, color="#475569")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Residual: V_model − V_market ($)", fontsize=11)
    ax.set_title("Pricing Residual per Contract — AMD Tickets\n"
                 "All four residuals are <$0.01 (|edge| <0.01%), well inside the ±5% H1 band",
                 fontsize=11, fontweight="bold")
    ax.set_ylim(band_bot * 1.2, band_top * 1.2)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.legend(loc="upper right", fontsize=9, facecolor="white",
              edgecolor="#CBD5E1")

    plt.tight_layout()
    plt.savefig(PREV_DIR / "slide9_residual.png", dpi=150,
                facecolor=BG_WHITE, bbox_inches="tight")
    plt.close()
    print("  Saved slide9_residual.png")


# ════════════════════════════════════════════════════════════════════════════
# PLOT 2 — Convergence with tight y-axis + log-scale residual inset
# ════════════════════════════════════════════════════════════════════════════
def preview_convergence():
    """Tighten the y-axis around the plateau region. Add an inset showing
    |price(N) − price(200)| on log scale to make convergence obvious."""
    # Use representative contracts (call T2, put T4) since BC/SC and BP/SP overlap
    visible_chain = CHAIN.iloc[[1, 3]].reset_index(drop=True)  # T2 SC, T4 SP

    steps = [5, 7, 10, 15, 25, 50, 75, 100, 150, 200]
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor(BG_WHITE)
    ax.set_facecolor(BG_WHITE)

    series = {}
    line_colors = {"call": NAVY_MID, "put": GOLD}
    line_labels = {"call": "Calls (T1 / T2 overlap)",
                   "put":  "Puts  (T3 / T4 overlap)"}

    for _, row in visible_chain.iterrows():
        prices = [
            price_american_option(row["S"], row["K"], row["r"], row["iv"],
                                  row["T"], n, row["option_type"])[0]
            for n in steps
        ]
        clr = line_colors[row["option_type"]]
        lbl = line_labels[row["option_type"]]
        ax.plot(steps, prices, marker="o", lw=2, markersize=6,
                color=clr, label=lbl, zorder=3)
        series[row["option_type"]] = np.array(prices)

    # Tight y-axis: ±5% of stable price, not the wild N=5 outlier
    all_stable = [series[k][-1] for k in series]
    y_center = np.mean(all_stable)
    y_range = max(all_stable) - min(all_stable) + 1.5
    ax.set_ylim(min(all_stable) - 1.0, max(all_stable) + 1.0)

    ax.set_xlabel("Steps (N)", fontsize=11)
    ax.set_ylabel("CRR price ($)", fontsize=11)
    ax.set_title("CRR Convergence — Tightened View\n"
                 "Both contracts stabilize by N ≈ 25",
                 fontsize=11, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10, facecolor="white",
              edgecolor="#CBD5E1")
    ax.grid(True, alpha=0.25)

    # ── Log-scale residual inset ──────────────────────────────────────────────
    # Inset centered between the two flat lines (Calls ~$19 at axes-y≈0.10
    # and Puts ~$27 at axes-y≈0.90), and centered horizontally in the plot.
    inset = ax.inset_axes([0.29, 0.32, 0.42, 0.36])
    inset.set_facecolor("#F8FAFC")
    for opt_type, prices in series.items():
        residuals = np.abs(prices - prices[-1])  # |price(N) − price(200)|
        residuals = np.where(residuals < 1e-6, 1e-6, residuals)
        inset.semilogy(steps, residuals, marker="o", lw=1.5, markersize=4,
                       color=line_colors[opt_type])
    inset.axhline(0.01, color=DEEP_RED, ls="--", lw=1.2, alpha=0.7)
    inset.text(180, 0.015, "$0.01", fontsize=7.5, color=DEEP_RED, ha="right")
    inset.set_xlabel("N", fontsize=8)
    inset.set_ylabel("|price(N) − price(200)|", fontsize=8)
    inset.set_title("Residual error (log scale)", fontsize=8.5)
    inset.tick_params(labelsize=7)
    inset.grid(True, which="both", alpha=0.25)

    plt.tight_layout()
    plt.savefig(PREV_DIR / "slide9_convergence.png", dpi=150,
                facecolor=BG_WHITE, bbox_inches="tight")
    plt.close()
    print("  Saved slide9_convergence.png")


# ════════════════════════════════════════════════════════════════════════════
# PLOT 3 — Early Exercise Boundary with deeper-ITM put illustration
# ════════════════════════════════════════════════════════════════════════════
def preview_boundary():
    """Two boundary curves on one chart: the actual AMD put (S=$341, K=$350,
    OTM — boundary stays well below spot) AND a deeper-ITM put illustration
    (S=$310, K=$350) where the boundary clearly crosses spot.

    Hybrid rendering (per user): discrete lattice points as small markers +
    smoothed trend line overlay. Green for AMD live, red for illustrative."""
    amd_put = CHAIN[CHAIN["option_type"] == "put"].iloc[1]
    N = 100

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor(BG_WHITE)
    ax.set_facecolor(BG_WHITE)

    def smooth(arr, window=5):
        """Centered rolling mean — kills the lattice-parity saw-tooth."""
        return pd.Series(arr).rolling(window=window, center=True,
                                       min_periods=1).mean().values

    # 1) AMD live put — green markers + green smoothed trend
    _, boundary_amd = price_american_option(
        amd_put["S"], amd_put["K"], amd_put["r"], amd_put["iv"],
        amd_put["T"], N, "put"
    )
    valid = ~np.isnan(boundary_amd)
    dt = amd_put["T"] / N
    days_amd = np.arange(N + 1) * dt * 365
    b_amd_v = boundary_amd[valid]
    d_amd_v = days_amd[valid]
    ax.plot(d_amd_v, b_amd_v, "o", markersize=3.5, color=FOREST,
            alpha=0.55, zorder=2)
    ax.plot(d_amd_v, smooth(b_amd_v), lw=2.2, color=FOREST, zorder=4,
            label="AMD live put  (S=\\$341.35, K=\\$350)\n"
                  "OTM — boundary stays below spot")

    # 2) Deeper-ITM put illustration: S=$310, K=$350 — red markers + red trend
    illust_S = 310.0
    _, boundary_illust = price_american_option(
        illust_S, 350.0, amd_put["r"], amd_put["iv"],
        amd_put["T"], N, "put"
    )
    valid_il = ~np.isnan(boundary_illust)
    b_il_v = boundary_illust[valid_il]
    d_il_v = days_amd[valid_il]
    ax.plot(d_il_v, b_il_v, "o", markersize=3.5, color=DEEP_RED,
            alpha=0.55, zorder=2)
    ax.plot(d_il_v, smooth(b_il_v), lw=2.2, color=DEEP_RED, zorder=4,
            label=f"Illustrative deep-ITM put  (S=\\${illust_S:.0f}, K=\\$350)\n"
                  "boundary crosses spot")

    # 3) Spot price reference lines
    ax.axhline(amd_put["S"], color=NAVY_MID, ls="--", lw=1.3, alpha=0.75,
               label=f"AMD spot S = \\$341.35")
    ax.axhline(illust_S, color="#475569", ls=":", lw=1.3, alpha=0.65,
               label=f"Illustrative spot S = \\${illust_S:.0f}")

    # 4) Highlight the crossover region — grey shading (per user)
    cross_idx = np.where(boundary_illust[valid_il] > illust_S)[0]
    if len(cross_idx) > 0:
        first_cross_day = days_amd[valid_il][cross_idx[0]]
        ax.axvspan(first_cross_day, days_amd[valid_il].max(),
                   color=SILVER, alpha=0.28, zorder=1,
                   label="Early-exercise zone (illustrative)")
        ax.text((first_cross_day + days_amd[valid_il].max()) / 2,
                illust_S + 5,
                "exercise becomes\noptimal here",
                ha="center", va="bottom",
                fontsize=9, color=DEEP_RED, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3",
                          facecolor="white", edgecolor=DEEP_RED, alpha=0.90),
                zorder=5)

    # 5) S* definition box — upper-left (empty space at start of timeline)
    ax.text(0.015, 0.985,
            r"$S^*(t)$ = Critical stock price at time $t$" + "\n"
            "below which immediate exercise of the\n"
            "American put dominates continuing to hold.",
            transform=ax.transAxes, va="top", ha="left",
            fontsize=8.5, color="#1A1A2E",
            bbox=dict(boxstyle="round,pad=0.45",
                      facecolor="white", edgecolor="#94A3B8",
                      linewidth=0.8, alpha=0.95),
            zorder=5)

    ax.set_xlabel("Days from collection date", fontsize=11)
    ax.set_ylabel("Critical stock price S* (\\$)", fontsize=11)
    ax.set_title("Early Exercise Boundary — AMD live + illustrative deep-ITM contrast\n"
                 "S* > spot → exercise immediately; S* < spot → hold",
                 fontsize=11, fontweight="bold")
    ax.legend(loc="lower right", fontsize=8, facecolor="white",
              edgecolor="#CBD5E1", labelspacing=0.5,
              handlelength=1.6, borderpad=0.5)
    ax.grid(True, alpha=0.25)
    ax.set_ylim(min(boundary_amd[valid].min(),
                    boundary_illust[valid_il].min()) - 10,
                max(amd_put["K"] + 10, illust_S + 30))

    plt.tight_layout()
    plt.savefig(PREV_DIR / "slide9_boundary.png", dpi=150,
                facecolor=BG_WHITE, bbox_inches="tight")
    plt.close()
    print("  Saved slide9_boundary.png")


if __name__ == "__main__":
    print("Generating slide-9 plot previews ...")
    preview_residual()
    preview_convergence()
    preview_boundary()
    print(f"\nAll three previews saved to: {PREV_DIR}")
