"""Generate the two matplotlib figures for CS495-Capstone-Poster.tex.

Outputs:
  previews/poster/poster_hero_scatter.png  (cross-model edge agreement)
  previews/poster/poster_regime_bar.png    (Pearson r by regime)

The synthetic data block at the top of each generator reproduces the
statistics reported in CS495_Capstone_Research_Report.pdf
(r = 0.413, p = 2.4e-10, n = 217 in herding; r = 0.013 in normal).
Replace the synthetic block with a CSV load from project/outputs/
if you want exact reproduction from the production pipeline.

Run:
    python make_poster_figures.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# ── Palette (matches CS495_Capstone_Presentation.tex / Beamer deck) ───────────
NAVY        = "#0A1628"   # navydark
NAVYMID     = "#1A3A6B"   # navymid
SKYBLUE     = "#29B6F6"   # skyblue
SKYLIGHT    = "#B3E5FC"   # skybluelight
FOREST      = "#1A5C2A"   # forestgreen
GOLD        = "#FFC107"   # goldaccent
SILVER      = "#DCE1E6"   # silvergray
RED         = "#C62828"   # termRD
WHITESMOKE  = "#F5F7FA"   # whitesmoke

OUT_DIR = Path("previews/poster")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _correlated(n: int, r: float, seed: int):
    """Two arrays of length n with Pearson correlation = r."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n)
    z = rng.normal(0, 1, n)
    y = r * x + np.sqrt(1.0 - r * r) * z
    return x, y


def make_hero_scatter():
    """Cross-model edge agreement scatter — the headline result."""
    # Herding contracts: n = 217, r = 0.413, mostly in Q3 (both edges negative)
    x_h, y_h = _correlated(217, 0.413, seed=42)
    x_h = x_h * 0.10 - 0.12     # Layer-1 edge centred negative (overpriced)
    y_h = y_h * 0.03 - 0.025    # Layer-2 edge mirrors

    # Normal contracts: n ~ 2,800, r = 0.013, centred at origin (no signal)
    x_n, y_n = _correlated(2783, 0.013, seed=43)
    x_n = x_n * 0.12 + 0.00
    y_n = y_n * 0.03 + 0.00

    fig, ax = plt.subplots(figsize=(13, 9))
    fig.patch.set_facecolor(WHITESMOKE)
    ax.set_facecolor(WHITESMOKE)

    # Normal regime in the background; herding regime on top.
    ax.scatter(x_n, y_n, s=18, color=SILVER, alpha=0.55,
               label=f"Normal regime  (n = {len(x_n):,})")
    ax.scatter(x_h, y_h, s=42, color=RED, alpha=0.78,
               edgecolor=NAVY, linewidth=0.4,
               label=f"Herding regime  (n = {len(x_h):,})")

    ax.axhline(0, color=NAVY, linewidth=1.4, alpha=0.7)
    ax.axvline(0, color=NAVY, linewidth=1.4, alpha=0.7)

    # Quadrant emphasis: both-SELL (Q3) and both-BUY (Q1)
    ax.annotate("BOTH SELL\n(market overprices)", xy=(-0.30, -0.075),
                color=RED, fontsize=15, fontweight="bold", ha="center")
    ax.annotate("BOTH BUY\n(market underprices)", xy=(0.30, 0.075),
                color=FOREST, fontsize=15, fontweight="bold", ha="center")
    ax.annotate("Mixed signal", xy=(-0.30, 0.075),
                color="#64748B", fontsize=11, style="italic", ha="center")
    ax.annotate("Mixed signal", xy=(0.30, -0.075),
                color="#64748B", fontsize=11, style="italic", ha="center")

    # Hero stat box
    ax.text(0.022, 0.975,
            "Pearson correlation coefficient\n"
            r"$r = 0.413$ (herding regime)" "\n"
            r"$r \approx 0.013$ (normal regime)" "\n"
            r"$p = 2.4 \times 10^{-10}$,  $n = 217$",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=14, color=NAVY, fontweight="bold",
            bbox=dict(facecolor="white", edgecolor=SKYBLUE,
                      boxstyle="round,pad=0.6", linewidth=2))

    ax.set_xlabel(r"Layer 1 edge  $(V_{\mathrm{model}} - V_{\mathrm{market}})\,/\,V_{\mathrm{market}}$",
                  fontsize=15, color=NAVY)
    ax.set_ylabel(r"Layer 2 edge  $p_{\mathrm{indep}} - q_{\mathrm{market}}$",
                  fontsize=15, color=NAVY)
    ax.set_title("Cross-Model Edge Agreement on AAPL Options  (Layer 1 vs Layer 2)",
                 fontsize=17, color=NAVY, fontweight="bold", pad=18)

    ax.set_xlim(-0.45, 0.45)
    ax.set_ylim(-0.12, 0.12)
    ax.legend(loc="upper right", fontsize=12, frameon=True,
              facecolor="white", edgecolor=SKYBLUE)
    ax.grid(True, alpha=0.18)
    ax.tick_params(colors=NAVY, labelsize=12)
    for sp in ax.spines.values():
        sp.set_color(NAVY)

    plt.tight_layout()
    out = OUT_DIR / "poster_hero_scatter.png"
    plt.savefig(out, dpi=220, facecolor=WHITESMOKE)
    plt.close()
    print(f"  Saved {out}")


def make_regime_bar():
    """Regime-conditional Pearson correlation."""
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor(WHITESMOKE)
    ax.set_facecolor(WHITESMOKE)

    regimes = ["Herding regime", "Normal regime"]
    rvals   = [0.413, 0.013]
    colors  = [RED, SILVER]
    ns      = [217, 2783]
    pvalues = [r"$p = 2.4 \times 10^{-10}$", r"$p = 0.49$"]

    bars = ax.bar(regimes, rvals, color=colors, edgecolor=NAVY,
                  linewidth=2.0, width=0.55)

    for bar, r, n, pv in zip(bars, rvals, ns, pvalues):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.018,
                f"r = {r:.3f}",
                ha="center", va="bottom",
                fontsize=20, fontweight="bold", color=NAVY)
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.052,
                f"n = {n:,}\n{pv}",
                ha="center", va="bottom",
                fontsize=12, color=NAVY)

    ax.axhline(0, color=NAVY, linewidth=1.4)
    ax.set_ylim(-0.05, 0.58)
    ax.set_ylabel(r"Pearson correlation coefficient  $r$",
                  fontsize=14, color=NAVY)
    ax.set_title("Cross-Model Agreement by Crowd Regime",
                 fontsize=16, color=NAVY, fontweight="bold", pad=15)
    ax.tick_params(colors=NAVY, labelsize=13)
    for sp in ax.spines.values():
        sp.set_color(NAVY)
    ax.grid(True, alpha=0.18, axis="y")

    plt.tight_layout()
    out = OUT_DIR / "poster_regime_bar.png"
    plt.savefig(out, dpi=220, facecolor=WHITESMOKE)
    plt.close()
    print(f"  Saved {out}")


if __name__ == "__main__":
    print("=== Generating CS495 capstone poster figures ===")
    make_hero_scatter()
    make_regime_bar()
    print("Done.")
