#!/usr/bin/env python3
"""
make_color_preview.py
Generates preview PNGs of the proposed CS495-presentation palette applied
to every visual element of crr_binomial_pricing_calculator.py.

Does NOT modify the production script. Outputs to previews/.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle

PREV_DIR = os.path.join(os.path.dirname(__file__), "previews")
os.makedirs(PREV_DIR, exist_ok=True)

# ── Palette ──────────────────────────────────────────────────────────────────
BG          = "#0E1117"   # Streamlit near-black (per user preference)
NAVY_DARK   = "#0B2041"   # navydark — legend panels / accent fills
NAVY_MID    = "#163A8C"   # navymid  — primary blue (CRR Model, Half Kelly bar)
SKY_BLUE    = "#3A7BD5"   # skyblue  — convergence line, ref lines, legend edge
LABEL_BLUE  = "#88B8E8"   # labelblue — axis labels, NO-TRADE zone tint
DESC_BLUE   = "#C8DCF0"   # descblue — tick labels, secondary text
FOREST      = "#145A22"   # forestgreen — BUY / NORMAL / Hold / positive edge
BURNT_ORG   = "#7A1E00"   # burntorange — COMPRESSION / Early-exercise / threshold lines
GOLD        = "#F57F17"   # goldaccent — Market price / boundary / Quarter Kelly / root
DEEP_RED    = "#C62828"   # deepred — HERDING / negative edge / Full Kelly bar
MAROON      = "#880E4F"   # maroon — SELL banner
SILVER      = "#546E7A"   # silvergray — NO TRADE banner / tree edges

SPINE       = SKY_BLUE
TICK        = DESC_BLUE
AXIS_LABEL  = LABEL_BLUE
TITLE       = "white"


def dark_fig(w=7, h=4):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.tick_params(colors=TICK)
    for sp in ax.spines.values():
        sp.set_edgecolor(SPINE)
        sp.set_alpha(0.45)
    return fig, ax


def style_axes(ax):
    ax.tick_params(colors=TICK)
    ax.xaxis.label.set_color(AXIS_LABEL)
    ax.yaxis.label.set_color(AXIS_LABEL)
    ax.title.set_color(TITLE)
    for sp in ax.spines.values():
        sp.set_edgecolor(SPINE)
        sp.set_alpha(0.45)


# ── Tab 1 — Pricing ──────────────────────────────────────────────────────────
def preview_pricing():
    mdl, mkt = 10.50, 9.80
    K = 200
    fig = plt.figure(figsize=(14, 9))
    fig.patch.set_facecolor(BG)

    ax1 = fig.add_subplot(2, 2, 1); ax1.set_facecolor(BG)
    bars = ax1.bar(["CRR Model", "V_market"], [mdl, mkt],
                   color=[NAVY_MID, GOLD], width=0.5)
    for b, v in zip(bars, [mdl, mkt]):
        ax1.text(b.get_x()+b.get_width()/2, v+0.1,
                 f"${v:.2f}", ha="center", va="bottom",
                 color="white", fontweight="bold", fontsize=10)
    ax1.set_ylabel("Price ($)")
    ax1.set_title(f"Model vs Market — CALL  K=${K:.0f}")
    style_axes(ax1)

    ax2 = fig.add_subplot(2, 2, 2); ax2.set_facecolor(BG)
    steps = [5, 10, 25, 50, 100, 150, 200]
    prices = [9.20, 10.10, 10.35, 10.45, 10.48, 10.49, 10.50]
    ax2.plot(steps, prices, "o-", color=SKY_BLUE, lw=2)
    ax2.axhline(mkt, color=GOLD, ls="--", lw=1.5,
                label=f"V_market = ${mkt:.2f}")
    ax2.set_xlabel("Steps (N)")
    ax2.set_ylabel("CRR Price ($)")
    ax2.set_title("CRR Convergence vs Step Count")
    ax2.legend(facecolor=NAVY_DARK, labelcolor="white",
               edgecolor=SKY_BLUE, fontsize=9)
    ax2.grid(True, alpha=0.2)
    style_axes(ax2)

    ax3 = fig.add_subplot(2, 1, 2); ax3.set_facecolor(BG)
    days = np.linspace(0, 30, 200)
    boundary = 195 - np.exp(-(30-days)/14)*55
    S = 200
    ax3.plot(days, boundary, ".", markersize=2, color=GOLD)
    ax3.axhline(S, color=SKY_BLUE, ls="--", lw=1.5,
                label=f"Current S = ${S:.2f}")
    ax3.set_xlabel("Days from today")
    ax3.set_ylabel("Critical S* ($)")
    ax3.set_title("Early Exercise Boundary — exercise the put when S falls below S*")
    ax3.legend(facecolor=NAVY_DARK, labelcolor="white",
               edgecolor=SKY_BLUE, fontsize=9)
    ax3.grid(True, alpha=0.2)
    style_axes(ax3)

    plt.tight_layout()
    plt.savefig(os.path.join(PREV_DIR, "tab1_pricing.png"),
                dpi=120, facecolor=BG)
    plt.close()
    print("  Saved tab1_pricing.png")


# ── Tab 3 — Edge Gauge ───────────────────────────────────────────────────────
def preview_edge_gauge():
    edge_pct = 7.0
    min_edge = 0.02

    fig, ax = dark_fig(10, 4.2)
    ax.barh(["Edge"], [edge_pct],
            color=FOREST if edge_pct >= 0 else DEEP_RED, height=0.35)
    min_line = ax.axvline(-min_edge*100, color=GOLD, ls="--", lw=1.5,
                          label=f"Min edge ± {min_edge*100:.1f}%")
    ax.axvline(min_edge*100, color=GOLD, ls="--", lw=1.5)
    nt_zone = ax.axvspan(-min_edge*100, min_edge*100, color="#7C3AED",
                         alpha=0.30, label="NO-TRADE zone")
    ax.set_xlabel("Edge %")

    handles = [
        mpatches.Patch(facecolor=FOREST,   label="Positive edge (undervalued)"),
        mpatches.Patch(facecolor=DEEP_RED, label="Negative edge (overvalued)"),
        min_line,
        nt_zone,
    ]
    # Legend below the chart so it doesn't overlap the bar
    ax.legend(handles=handles, facecolor=NAVY_DARK, labelcolor="white",
              edgecolor=SKY_BLUE, fontsize=9, ncol=2,
              loc="upper center", bbox_to_anchor=(0.5, -0.30),
              frameon=True)
    style_axes(ax)
    # Override axis labels and tick labels → white (per user)
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_color("white")
    plt.tight_layout()
    plt.savefig(os.path.join(PREV_DIR, "tab3_edge_gauge.png"),
                dpi=120, facecolor=BG, bbox_inches="tight")
    plt.close()
    print("  Saved tab3_edge_gauge.png")


# ── Tab 3 — Signal banners (mockup of Streamlit HTML) ────────────────────────
def preview_signal_banners():
    fig, ax = plt.subplots(figsize=(11, 3.6))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.set_xlim(0, 11); ax.set_ylim(0, 3.6); ax.axis("off")

    # Order (top → bottom): BUY, NO TRADE, SELL  (per user)
    banners = [
        ("BUY",      "Model price > market price — contract appears underpriced",  FOREST,   2.5),
        ("NO TRADE", "Edge below minimum threshold — market pricing looks efficient", SILVER, 1.35),
        ("SELL",     "Model price < market price — contract appears overpriced",   NAVY_MID, 0.2),
    ]
    for sig, reason, clr, y in banners:
        ax.add_patch(FancyBboxPatch((0.2, y), 10.6, 1.0,
                                     boxstyle="round,pad=0.04",
                                     facecolor=clr, edgecolor="none"))
        ax.text(5.5, y+0.68, sig, ha="center", va="center",
                fontsize=18, fontweight="bold", color="white")
        ax.text(5.5, y+0.27, reason, ha="center", va="center",
                fontsize=9, color=DESC_BLUE)

    plt.savefig(os.path.join(PREV_DIR, "tab3_signal_banners.png"),
                dpi=120, facecolor=BG, bbox_inches="tight")
    plt.close()
    print("  Saved tab3_signal_banners.png")


# ── Tab 3 — Regime cards (mockup of Streamlit HTML) ──────────────────────────
def preview_regime_cards():
    fig, ax = plt.subplots(figsize=(11, 3.6))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.set_xlim(0, 11); ax.set_ylim(0, 3.6); ax.axis("off")

    cards = [
        ("HERDING REGIME",     "IV / RV30 = 1.45 — crowd overbidding inflates premiums above CRR fair value", BURNT_ORG, 2.5,  "⚡"),
        ("NORMAL REGIME",      "IV / RV30 = 1.00 — efficient pricing, premiums reflect historical uncertainty", FOREST,    1.35, None),
        ("COMPRESSION REGIME", "IV / RV30 = 0.65 — market underpricing volatility relative to recent history", SKY_BLUE,  0.2,  None),
    ]
    for title, desc, clr, y, icon in cards:
        # translucent fill + colored border (mimics Streamlit alpha-bg + 1px border)
        ax.add_patch(FancyBboxPatch((0.2, y), 10.6, 1.0,
                                     boxstyle="round,pad=0.04",
                                     facecolor=clr+"30",  # ~19% alpha
                                     edgecolor=clr, linewidth=1.5))
        ax.text(0.5, y+0.68, title, ha="left", va="center",
                fontsize=14, fontweight="bold", color="white")
        ax.text(0.5, y+0.27, desc, ha="left", va="center",
                fontsize=9, color="white")
        if icon:
            ax.text(10.55, y+0.50, icon, ha="right", va="center",
                    fontsize=22, color=GOLD, fontweight="bold")

    plt.savefig(os.path.join(PREV_DIR, "tab3_regime_cards.png"),
                dpi=120, facecolor=BG, bbox_inches="tight")
    plt.close()
    print("  Saved tab3_regime_cards.png")


# ── Tab 4 — Kelly Sizing ─────────────────────────────────────────────────────
def preview_kelly():
    fig, ax = dark_fig(8, 3.6)
    variants = ["Full Kelly", "Half Kelly", "Quarter Kelly"]
    vals = [15.0, 7.5, 3.75]
    bars = ax.bar(variants, vals, color=[FOREST, NAVY_MID, GOLD], width=0.45)
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, v+0.25,
                f"{v:.2f}%", ha="center", va="bottom",
                color="white", fontweight="bold")
    ax.set_ylabel("Fraction of Capital (%)")
    ax.set_title("Kelly Position Sizing  —  f* = (p·b − q) / b")
    style_axes(ax)
    # Override axis labels and tick labels to gold (per user request)
    ax.yaxis.label.set_color(GOLD)
    ax.xaxis.label.set_color(GOLD)
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_color(GOLD)
    plt.tight_layout()
    plt.savefig(os.path.join(PREV_DIR, "tab4_kelly.png"),
                dpi=120, facecolor=BG)
    plt.close()
    print("  Saved tab4_kelly.png")


# ── Tab 5 — Monte Carlo P&L ──────────────────────────────────────────────────
def preview_monte_carlo():
    rng = np.random.default_rng(42)
    n = 1000
    full  = np.cumsum(rng.normal( 30, 100, n))
    half  = np.cumsum(rng.normal( 18,  60, n))
    quart = np.cumsum(rng.normal(  8,  30, n))

    fig, ax = dark_fig(10, 4.5)
    for vals, name, sharpe, clr in [
        (full,  "Full Kelly",    0.85, FOREST),
        (half,  "Half Kelly",    1.20, NAVY_MID),
        (quart, "Quarter Kelly", 0.95, GOLD)]:
        ax.plot(vals, color=clr, lw=1.5,
                label=f"{name}  (Sharpe = {sharpe:.2f})")
    ax.axhline(0, color="white", lw=0.8, alpha=0.35)
    ax.set_xlabel("Trades")
    ax.set_ylabel("Cumulative Profit and Loss ($)")
    ax.set_title("Monte Carlo Profit and Loss Simulation — 1,000 trades  |  p_win = 0.535")
    ax.legend(facecolor=NAVY_DARK, labelcolor="white",
              edgecolor=SKY_BLUE, fontsize=9)
    ax.grid(True, alpha=0.15)
    style_axes(ax)
    # Override axis labels and tick labels to white (per user request)
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_color("white")
    plt.tight_layout()
    plt.savefig(os.path.join(PREV_DIR, "tab5_montecarlo.png"),
                dpi=120, facecolor=BG)
    plt.close()
    print("  Saved tab5_montecarlo.png")


# ── Tab 6 — CRR Tree (one static frame) ──────────────────────────────────────
def preview_tree():
    N, K, S, sigma, T, r = 5, 200, 200, 0.30, 30/365, 0.053
    dt = T/N
    u = np.exp(sigma*np.sqrt(dt)); d = 1/u
    p = (np.exp(r*dt)-d)/(u-d);    disc = np.exp(-r*dt)

    stock = {(i, j): S*(u**(i-j))*(d**j)
             for i in range(N+1) for j in range(i+1)}
    option = {(N, j): max(K-stock[(N, j)], 0) for j in range(N+1)}  # put
    early = set()
    for i in range(N-1, -1, -1):
        for j in range(i+1):
            intr = max(K - stock[(i, j)], 0)
            cont = disc*(p*option[(i+1, j)] + (1-p)*option[(i+1, j+1)])
            option[(i, j)] = max(intr, cont)
            if intr > cont and intr > 0:
                early.add((i, j))

    # ── Original calculator colors (reverted per user request) ─────────────
    ROOT_C    = "#B45309"   # burnt orange — root node
    STOCK_C   = "#1E40AF"   # deep blue — stock price node (animation phase 1)
    HOLD_C    = "#065F46"   # dark green — hold (continuation wins)
    EARLY_C   = "#7C3AED"   # purple — early exercise (intrinsic wins)
    EDGE_C    = "#475569"   # dark slate — tree branches
    NODE_EC   = "#94A3B8"   # silver-gray — node border
    LEG_BG    = "#1E293B"   # original legend panel fill
    LEG_EDGE  = "#475569"   # original legend border
    AXIS_C    = "#CBD5E1"   # light slate — xlabel/ylabel
    SPINE_C   = "#1E293B"   # original spine color

    fig, ax = plt.subplots(figsize=(8, 6.5))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.set_aspect("equal", adjustable="box")

    def pos(i, j): return 2*i, i - 2*j
    r5 = np.sqrt(5.0)
    node_r = 0.72
    trim_x = node_r*2.0/r5
    trim_y = node_r/r5

    for i in range(N):
        for j in range(i+1):
            x0, y0 = pos(i, j); x1 = 2*(i+1)
            y_up = (i+1) - 2*j;  y_dn = (i+1) - 2*(j+1)
            ax.plot([x0+trim_x, x1-trim_x], [y0+trim_y, y_up-trim_y],
                    color=EDGE_C, lw=1.2, zorder=1)
            ax.plot([x0+trim_x, x1-trim_x], [y0-trim_y, y_dn+trim_y],
                    color=EDGE_C, lw=1.2, zorder=1)

    for i in range(N+1):
        for j in range(i+1):
            x, y = pos(i, j)
            if i == 0:                color = ROOT_C
            elif (i, j) in early:     color = EARLY_C
            else:                     color = HOLD_C
            ax.add_patch(Circle((x, y), node_r, color=color, zorder=3,
                                 ec=NODE_EC, lw=0.6))
            ax.text(x, y, f"${option[(i, j)]:.2f}", ha="center", va="center",
                    fontsize=7, color="white", fontweight="bold", zorder=4)

    ax.set_xlim(-1.2, 2*N+1.2); ax.set_ylim(-N-1.5, N+1.5)
    ax.set_xticks([2*k for k in range(N+1)])
    ax.set_xticklabels([str(round(k*30/N)) for k in range(N+1)])
    ax.set_xlabel("Days from Today  →", color=AXIS_C, fontsize=12)
    ax.set_ylabel("Binomial Tree Levels  (↑ up / ↓ down)", color=AXIS_C, fontsize=10)
    ax.set_title("CRR Binomial Tree  —  PUT  K=$200  |  N=5 display steps\n"
                 "← Backward induction: option values",
                 color="white", fontsize=13)
    ax.tick_params(colors="white", labelcolor="white")
    for sp in ax.spines.values():
        sp.set_edgecolor(SPINE_C)

    handles = [
        mpatches.Patch(color=ROOT_C,  label="Root  t = 0"),
        mpatches.Patch(color=STOCK_C, label="Stock price"),
        mpatches.Patch(color=HOLD_C,  label="Hold — continuation value wins"),
        mpatches.Patch(color=EARLY_C, label="Early exercise — intrinsic wins"),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=8,
              facecolor=LEG_BG, labelcolor="white",
              edgecolor=LEG_EDGE, handlelength=1.0, handleheight=0.7,
              borderpad=0.4, labelspacing=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(PREV_DIR, "tab6_tree.png"),
                dpi=120, facecolor=BG)
    plt.close()
    print("  Saved tab6_tree.png")


# ── Contract Parameters sidebar mockup ───────────────────────────────────────
def preview_sidebar():
    """Mockup of the Streamlit sidebar with proposed presentation colors."""
    SB_BG       = "#3F454C"   # sidebar background — medium dark gray (per user)
    FIELD_BG    = "#1E2737"   # input field fill
    FIELD_BORDER = SKY_BLUE
    HEADER_C    = LABEL_BLUE
    LABEL_C     = DESC_BLUE
    VALUE_C     = "white"
    DIVIDER_C   = SKY_BLUE
    BTN_BG      = NAVY_MID    # primary "Calculate" button
    BTN_BORDER  = SKY_BLUE
    SLIDER_TRK  = SILVER
    SLIDER_FILL = SKY_BLUE
    SLIDER_THMB = GOLD

    fig, ax = plt.subplots(figsize=(4.6, 13))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 32)
    ax.axis("off")

    # Sidebar panel
    ax.add_patch(FancyBboxPatch((0.15, 0.15), 9.7, 31.7,
                                 boxstyle="round,pad=0.05",
                                 facecolor=SB_BG, edgecolor=DIVIDER_C,
                                 linewidth=0.6, alpha=0.95))

    # Helper drawing functions
    def header(text, y, size=13, color=None):
        ax.text(0.55, y, text, fontsize=size, fontweight="bold",
                color=color or HEADER_C, ha="left", va="top")
        return y - 0.8

    def subheader(text, y):
        ax.text(0.55, y, text, fontsize=10, fontweight="bold",
                color="white", ha="left", va="top")
        return y - 0.55

    def label_field(label, value, y):
        ax.text(0.55, y, label, fontsize=7.5, color=LABEL_C,
                ha="left", va="top")
        ax.add_patch(FancyBboxPatch((0.55, y - 1.10), 8.9, 0.65,
                                     boxstyle="round,pad=0.02",
                                     facecolor=FIELD_BG, edgecolor=FIELD_BORDER,
                                     linewidth=0.7, alpha=0.9))
        ax.text(0.75, y - 0.78, value, fontsize=9.5,
                color=VALUE_C, ha="left", va="center")
        return y - 1.55

    def two_col_select(lbl1, val1, lbl2, val2, y):
        for i, (lbl, val) in enumerate([(lbl1, val1), (lbl2, val2)]):
            x = 0.55 + i * 4.55
            ax.text(x, y, lbl, fontsize=7.5, color=LABEL_C,
                    ha="left", va="top")
            ax.add_patch(FancyBboxPatch((x, y - 1.10), 4.35, 0.65,
                                         boxstyle="round,pad=0.02",
                                         facecolor=FIELD_BG, edgecolor=FIELD_BORDER,
                                         linewidth=0.7, alpha=0.9))
            ax.text(x + 0.2, y - 0.78, val, fontsize=9.5,
                    color=VALUE_C, ha="left", va="center")
            # dropdown chevron — white to match input text (per user)
            ax.text(x + 4.15, y - 0.78, "▾", fontsize=9,
                    color="white", fontweight="bold",
                    ha="right", va="center")
        return y - 1.55

    def slider(label, value, frac, vmin, vmax, y):
        ax.text(0.55, y, label, fontsize=7.5, color=LABEL_C,
                ha="left", va="top")
        # track
        ax.plot([0.55, 9.45], [y - 0.85, y - 0.85],
                color=SLIDER_TRK, lw=2.0, alpha=0.5,
                solid_capstyle="round")
        # filled portion
        fill_x = 0.55 + frac * 8.9
        ax.plot([0.55, fill_x], [y - 0.85, y - 0.85],
                color=SLIDER_FILL, lw=2.5, solid_capstyle="round")
        # thumb
        ax.add_patch(Circle((fill_x, y - 0.85), 0.18,
                             facecolor=SLIDER_THMB,
                             edgecolor="white", lw=0.8, zorder=4))
        # current value
        ax.text(9.45, y - 0.45, value, fontsize=7.5,
                color=VALUE_C, ha="right", va="center")
        # min / max tick labels — white (per user)
        ax.text(0.55, y - 1.15, vmin, fontsize=7,
                color="white", ha="left", va="center")
        ax.text(9.45, y - 1.15, vmax, fontsize=7,
                color="white", ha="right", va="center")
        return y - 1.60

    def divider_line(y):
        ax.plot([0.55, 9.45], [y, y], color=DIVIDER_C, lw=0.7, alpha=0.45)
        return y - 0.4

    def button(text, y):
        ax.add_patch(FancyBboxPatch((0.55, y - 0.95), 8.9, 0.85,
                                     boxstyle="round,pad=0.04",
                                     facecolor=BTN_BG,
                                     edgecolor=BTN_BORDER, linewidth=1.2))
        ax.text(5.0, y - 0.50, text, fontsize=11, fontweight="bold",
                color="white", ha="center", va="center")
        return y - 1.20

    # ── Build sidebar layout ─────────────────────────────────────────────────
    y = 31.2
    y = header("Contract Parameters", y, color="white")
    y = label_field("Ticker (for RV30 lookup)", "AAPL", y)
    y = two_col_select("Option Type", "put", "Action", "buy", y)
    y = label_field("Underlying Price (S $)", "200.00", y)
    y = label_field("Strike Price (K $)", "200.00", y)
    y = label_field("Market Price (V_market)", "10.00", y)
    y = label_field("Implied Volatility (IV)", "0.3000", y)
    y = divider_line(y)
    y = label_field("Days to Expiration (DTE)", "30", y)
    y = label_field("Risk-free Rate (r)", "0.053", y)
    y = label_field("CRR Steps (N)", "100", y)
    y = divider_line(y)
    y = subheader("Kelly Parameters", y)
    y = label_field("Capital ($)", "100,000", y)
    y = label_field("Min Edge Threshold", "0.020", y)
    y = divider_line(y)
    y = subheader("Tree Animation", y)
    y = slider("Display Steps (N)", "7",    0.43, "4",    "12", y)
    y = slider("Speed (sec/step)",  "0.25", 0.20, "0.05", "1",  y)
    y -= 0.3
    y = button("Calculate", y)

    plt.savefig(os.path.join(PREV_DIR, "sidebar_contract_params.png"),
                dpi=130, facecolor=BG, bbox_inches="tight")
    plt.close()
    print("  Saved sidebar_contract_params.png")


# ── Greeks tab mockup (caption + metric cards + table) ──────────────────────
def preview_greeks():
    """Mockup of the Greeks tab page (light theme) with proposed colors:
    - Caption text → navy blue
    - Table header → green background with gold text
    """
    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 14); ax.set_ylim(0, 9)
    ax.axis("off")

    # Title
    ax.text(0.4, 8.55, "CRR Binomial Pricing Calculator",
            fontsize=22, fontweight="bold", color="#1A1A2E")

    # Caption — navy blue (per user)
    ax.text(0.4, 7.95,
            "Cox-Ross-Rubinstein American option pricer · Kelly Criterion sizing · "
            "Monte Carlo simulation  |  Works for any ticker  ·  No dividends assumed",
            fontsize=10, color=NAVY_MID, style="italic")

    # Tab strip (emojis dropped — matplotlib default font lacks them)
    tabs_list = [("Pricing", False), ("Greeks", True),
                 ("Edge & Signal", False), ("Kelly Sizing", False),
                 ("Monte Carlo", False), ("Tree Animation", False),
                 ("User's Guide", False)]
    x = 0.4
    tab_y = 7.35
    for tab, active in tabs_list:
        clr = SKY_BLUE if active else "#666666"
        weight = "bold" if active else "normal"
        ax.text(x, tab_y, tab, fontsize=10, color=clr, fontweight=weight)
        if active:
            ax.plot([x - 0.05, x + 1.20], [tab_y - 0.18, tab_y - 0.18],
                    color=SKY_BLUE, lw=2.5)
        x += 1.85

    # Divider below tabs
    ax.plot([0.4, 13.6], [7.00, 7.00], color="#E0E0E0", lw=0.8)

    # Metric cards row (Delta, Gamma, Theta, Vega, Rho, IV)
    metrics = [
        ("Delta (Δ)",      "-0.4892"),
        ("Gamma (Γ)",      "0.0156"),
        ("Theta (Θ) /day", "-0.0721"),
        ("Vega (ν)",       "0.2143"),
        ("Rho (ρ)",        "-0.0085"),
        ("IV (σ)",         "0.3000"),
    ]
    card_w = 2.10
    card_gap = 0.10
    card_y = 5.40
    card_h = 1.35
    for i, (label, value) in enumerate(metrics):
        cx = 0.4 + i * (card_w + card_gap)
        ax.add_patch(FancyBboxPatch((cx, card_y), card_w, card_h,
                                     boxstyle="round,pad=0.02",
                                     facecolor="#F8F9FA",
                                     edgecolor="#E0E0E0", linewidth=0.5))
        ax.text(cx + 0.15, card_y + 1.05, label,
                fontsize=9.5, color="#666666")
        ax.text(cx + 0.15, card_y + 0.45, value,
                fontsize=16, fontweight="bold", color="#1A1A2E")

    # Divider above table
    ax.plot([0.4, 13.6], [4.95, 4.95], color="#E0E0E0", lw=0.8)

    # Greeks table — green header / gold text
    cols = ["Greek", "Value", "Interpretation"]
    col_widths = [2.5, 2.0, 8.7]
    rows = [
        ["Delta (Δ)", "-0.4892", "$-0.4892 per $1 move in underlying"],
        ["Gamma (Γ)", "0.0156",  "Delta shifts by +0.0156 per $1 move in underlying"],
        ["Theta (Θ)", "-0.0721", "$-0.0721 per calendar day (time decay)"],
        ["Vega (ν)",  "0.2143",  "$+0.2143 per 1 vol-point (0.01) move in IV"],
        ["Rho (ρ)",   "-0.0085", "$-0.0085 per 100bps change in r"],
        ["IV (σ)",    "0.3000",  "Implied Volatility — market's annualized expectation of price variation"],
    ]

    row_h = 0.62
    header_y = 4.25
    table_x = 0.4

    # Header row — navy bg + white text
    x_pos = table_x
    for col, width in zip(cols, col_widths):
        ax.add_patch(plt.Rectangle((x_pos, header_y), width, row_h,
                                    facecolor=NAVY_MID,
                                    edgecolor="white", linewidth=1))
        ax.text(x_pos + 0.2, header_y + row_h/2, col,
                fontsize=11, fontweight="bold", color="white",
                va="center", ha="left")
        x_pos += width

    # Body rows — alternating white / very light gray
    for i, row in enumerate(rows):
        y = header_y - (i + 1) * row_h
        row_bg = "#FFFFFF" if i % 2 == 0 else "#F5F7FA"
        x_pos = table_x
        for cell, width in zip(row, col_widths):
            ax.add_patch(plt.Rectangle((x_pos, y), width, row_h,
                                        facecolor=row_bg,
                                        edgecolor="#E0E0E0", linewidth=0.5))
            ax.text(x_pos + 0.2, y + row_h/2, cell,
                    fontsize=10, color="#1A1A2E",
                    va="center", ha="left")
            x_pos += width

    plt.savefig(os.path.join(PREV_DIR, "tab2_greeks.png"),
                dpi=120, facecolor="white", bbox_inches="tight")
    plt.close()
    print("  Saved tab2_greeks.png")


# ── Kelly Sizing tab mockup (metric + plot + table, in new order) ────────────
def preview_kelly_tab():
    """Full-page Kelly Sizing tab: Win Probability metric, then bar chart,
    then table below (matching Greeks-table navy header / white text)."""
    fig, ax = plt.subplots(figsize=(14, 11))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 14); ax.set_ylim(0, 11)
    ax.axis("off")

    # Title + caption
    ax.text(0.4, 10.55, "CRR Binomial Pricing Calculator",
            fontsize=22, fontweight="bold", color="#1A1A2E")
    ax.text(0.4, 9.95,
            "Cox-Ross-Rubinstein American option pricer · Kelly Criterion sizing · "
            "Monte Carlo simulation  |  Works for any ticker  ·  No dividends assumed",
            fontsize=10, color=NAVY_MID, style="italic")

    # Tab strip — Kelly Sizing active
    tabs_list = [("Pricing", False), ("Greeks", False),
                 ("Edge & Signal", False), ("Kelly Sizing", True),
                 ("Monte Carlo", False), ("Tree Animation", False),
                 ("User's Guide", False)]
    x = 0.4
    tab_y = 9.35
    for tab, active in tabs_list:
        clr = SKY_BLUE if active else "#666666"
        weight = "bold" if active else "normal"
        ax.text(x, tab_y, tab, fontsize=10, color=clr, fontweight=weight)
        if active:
            ax.plot([x - 0.05, x + 1.55], [tab_y - 0.18, tab_y - 0.18],
                    color=SKY_BLUE, lw=2.5)
        x += 1.85
    ax.plot([0.4, 13.6], [9.00, 9.00], color="#E0E0E0", lw=0.8)

    # Win Probability metric (single card, left-aligned)
    ax.add_patch(FancyBboxPatch((0.4, 7.85), 3.5, 1.0,
                                 boxstyle="round,pad=0.02",
                                 facecolor="#F8F9FA",
                                 edgecolor="#E0E0E0", linewidth=0.5))
    ax.text(0.55, 8.65, "Win Probability (p_win)",
            fontsize=10, color="#666666")
    ax.text(0.55, 8.15, "0.6750",
            fontsize=20, fontweight="bold", color="#1A1A2E")

    # ── Kelly Sizing bar chart (PLOT FIRST, matches dark-figure style) ──────
    chart_x0, chart_y0 = 0.4, 3.55
    chart_w, chart_h = 13.2, 3.85
    ax.add_patch(plt.Rectangle((chart_x0, chart_y0), chart_w, chart_h,
                                facecolor=BG, edgecolor=SKY_BLUE,
                                linewidth=0.8, alpha=0.95))
    ax.text(chart_x0 + chart_w/2, chart_y0 + chart_h - 0.30,
            "Kelly Position Sizing  —  f* = (p·b − q) / b",
            fontsize=12, fontweight="bold", color="white",
            ha="center", va="top")
    # Bars on the chart
    bar_labels = ["Full Kelly", "Half Kelly", "Quarter Kelly"]
    bar_vals   = [33.75, 16.88, 8.44]      # corresponding to p_win=0.675
    bar_clrs   = [FOREST, NAVY_MID, GOLD]
    bar_w = 1.4
    bar_gap = 2.8
    base_y = chart_y0 + 0.55
    max_val = max(bar_vals)
    bar_max_h = chart_h - 1.30
    for i, (lbl, val, clr) in enumerate(zip(bar_labels, bar_vals, bar_clrs)):
        bx = chart_x0 + 2.5 + i * bar_gap
        bar_h = (val / max_val) * bar_max_h
        ax.add_patch(plt.Rectangle((bx, base_y), bar_w, bar_h,
                                    facecolor=clr, edgecolor="none"))
        ax.text(bx + bar_w/2, base_y + bar_h + 0.12,
                f"{val:.2f}%", ha="center", va="bottom",
                fontsize=11, fontweight="bold", color="white")
        ax.text(bx + bar_w/2, base_y - 0.25, lbl,
                ha="center", va="top", fontsize=10, color=GOLD)
    ax.text(chart_x0 + 0.25, chart_y0 + chart_h/2 + 0.5,
            "Fraction of Capital (%)", rotation=90,
            ha="center", va="center", fontsize=10, color=GOLD)

    # ── Kelly table (BELOW the chart, navy header / white text) ─────────────
    cols = ["Variant", "Fraction (f*)", "% of Capital", "Dollar Amount", "Trade Signal"]
    col_widths = [2.5, 2.2, 2.5, 2.9, 3.1]
    rows = [
        ["Full Kelly",    "0.3375", "33.75%", "$33,750.00", "SELL"],
        ["Half Kelly",    "0.1688", "16.88%", "$16,880.00", "SELL"],
        ["Quarter Kelly", "0.0844", "8.44%",  "$8,440.00",  "SELL"],
    ]
    row_h = 0.55
    header_y = 2.80
    table_x = 0.4

    # Header — navy bg + white text
    x_pos = table_x
    for col, width in zip(cols, col_widths):
        ax.add_patch(plt.Rectangle((x_pos, header_y), width, row_h,
                                    facecolor=NAVY_MID,
                                    edgecolor="white", linewidth=1))
        ax.text(x_pos + 0.18, header_y + row_h/2, col,
                fontsize=10, fontweight="bold", color="white",
                va="center", ha="left")
        x_pos += width

    # Body rows
    for i, row in enumerate(rows):
        y = header_y - (i + 1) * row_h
        row_bg = "#FFFFFF" if i % 2 == 0 else "#F5F7FA"
        x_pos = table_x
        for cell, width in zip(row, col_widths):
            ax.add_patch(plt.Rectangle((x_pos, y), width, row_h,
                                        facecolor=row_bg,
                                        edgecolor="#E0E0E0", linewidth=0.5))
            ax.text(x_pos + 0.18, y + row_h/2, cell,
                    fontsize=10, color="#1A1A2E",
                    va="center", ha="left")
            x_pos += width

    plt.savefig(os.path.join(PREV_DIR, "tab4_kelly_full.png"),
                dpi=120, facecolor="white", bbox_inches="tight")
    plt.close()
    print("  Saved tab4_kelly_full.png")


# ── "About this screen" styled box mockup (used inside st.expander) ──────────
def preview_about_box():
    """Mockup of the 'About this screen' styled card that lives inside each
    tab's collapsible expander. Light blue-gray fill, sky-blue left accent,
    navy-blue section labels, dark body text."""
    fig, ax = plt.subplots(figsize=(13, 6))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 13); ax.set_ylim(0, 6)
    ax.axis("off")

    # Expander HEADER bar — now navy bg + white text (per user)
    ax.add_patch(FancyBboxPatch((0.2, 5.30), 12.6, 0.60,
                                 boxstyle="round,pad=0.02",
                                 facecolor=NAVY_MID, edgecolor="none"))
    ax.text(0.45, 5.60, "▼  About this screen",
            fontsize=11, color="white", fontweight="bold",
            va="center", ha="left")

    # Content card — back to original light styling
    ax.add_patch(FancyBboxPatch((0.2, 0.3), 12.6, 4.7,
                                 boxstyle="round,pad=0.02",
                                 facecolor="#F8FAFC", edgecolor="#E0E0E0",
                                 linewidth=0.5))
    ax.add_patch(plt.Rectangle((0.2, 0.3), 0.15, 4.7,
                                facecolor=SKY_BLUE, edgecolor="none"))

    # Body text — example using Pricing tab content
    label_c = NAVY_MID
    body_c  = "#1A1A2E"
    line_y  = 4.55

    def line(label, text, y):
        ax.text(0.6, y, label, fontsize=11, fontweight="bold",
                color=label_c, va="top", ha="left")
        return y - 0.30

    line("What this shows.", "", line_y)
    ax.text(0.6, line_y - 0.40,
            "The Cox–Ross–Rubinstein American binomial pricer applied to your sidebar\n"
            "contract: Model vs Market (CRR fair value V_model vs market premium V_market);\n"
            "Convergence of V_model as lattice depth N grows; Early Exercise Boundary S*\n"
            "below which exercising an American put dominates holding.",
            fontsize=10, color=body_c, va="top", ha="left", linespacing=1.5)

    line("Why it matters.", "", 3.05)
    ax.text(0.6, 2.65,
            "Pricing accuracy is hypothesis H1 of the research — every downstream decision\n"
            "(edge detection, regime classification, Kelly sizing) assumes V_model is calibrated.\n"
            "The boundary panel is the analytic capability that justifies the CRR lattice over\n"
            "the closed-form Black–Scholes model for American options.",
            fontsize=10, color=body_c, va="top", ha="left", linespacing=1.5)

    line("Research link.", "", 1.30)
    ax.text(0.6, 0.90,
            "Implements §3.4.1 — Layer 1: CRR Pricing Engine, validated in §4.2–§4.4 of the\n"
            "capstone report. Maps to Project 6's \"true p estimator\" deliverable.",
            fontsize=10, color=body_c, va="top", ha="left", linespacing=1.5)

    plt.savefig(os.path.join(PREV_DIR, "about_box_style.png"),
                dpi=120, facecolor="white", bbox_inches="tight")
    plt.close()
    print("  Saved about_box_style.png")


# ── Palette swatch summary ───────────────────────────────────────────────────
def preview_palette():
    palette = [
        ("BG (Streamlit default)", BG),
        ("navydark",   NAVY_DARK),
        ("navymid",    NAVY_MID),
        ("skyblue",    SKY_BLUE),
        ("labelblue",  LABEL_BLUE),
        ("descblue",   DESC_BLUE),
        ("forestgreen", FOREST),
        ("burntorange", BURNT_ORG),
        ("goldaccent",  GOLD),
        ("deepred",     DEEP_RED),
        ("maroon",      MAROON),
        ("silvergray",  SILVER),
    ]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.set_xlim(0, 12); ax.set_ylim(0, len(palette)); ax.axis("off")
    for i, (name, hexcode) in enumerate(palette[::-1]):
        y = i + 0.15
        ax.add_patch(FancyBboxPatch((0.3, y), 1.8, 0.7,
                                     boxstyle="round,pad=0.02",
                                     facecolor=hexcode, edgecolor="#222"))
        ax.text(2.4, y+0.35, name, ha="left", va="center",
                fontsize=11, color="white", fontweight="bold")
        ax.text(7.2, y+0.35, hexcode.upper(), ha="left", va="center",
                fontsize=11, color=DESC_BLUE, family="monospace")
    ax.set_title("Proposed Palette  —  from CS495 Capstone Presentation",
                 color="white", fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(PREV_DIR, "palette.png"),
                dpi=120, facecolor=BG)
    plt.close()
    print("  Saved palette.png")


if __name__ == "__main__":
    print("Generating previews ...")
    preview_palette()
    preview_sidebar()
    preview_pricing()
    preview_edge_gauge()
    preview_signal_banners()
    preview_regime_cards()
    preview_kelly()
    preview_monte_carlo()
    preview_tree()
    print(f"\nAll previews saved to: {PREV_DIR}")
