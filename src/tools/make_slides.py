"""Generate CS495 Capstone Presentation slide deck as PDF."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Rectangle
import matplotlib.image as mpimg
import numpy as np
from textwrap import wrap
import os

OUT_DIR = "project/outputs"
PDF_OUT = "CS495_Capstone_Presentation.pdf"

NAVY   = "#0D1F3C"
GREEN  = "#166534"
RED    = "#DC2626"
BLUE   = "#1E40AF"
PURPLE = "#7C3AED"
TEAL   = "#047857"
GOLD   = "#D97706"
LIGHT  = "#F8FAFC"
GREY   = "#64748B"
WHITE  = "#FFFFFF"

SLIDE_W, SLIDE_H = 13.33, 7.5


def new_slide():
    fig = plt.figure(figsize=(SLIDE_W, SLIDE_H))
    fig.patch.set_facecolor(WHITE)
    return fig


def header_bar(fig, title, subtitle=None):
    bar = fig.add_axes([0, 0.875, 1, 0.125])
    bar.set_facecolor(NAVY)
    bar.axis("off")
    bar.text(0.03, 0.65, title, color=WHITE, fontsize=22, fontweight="bold",
             va="center", transform=bar.transAxes)
    if subtitle:
        bar.text(0.03, 0.20, subtitle, color="#94A3B8", fontsize=10.5,
                 va="center", transform=bar.transAxes)


def footer(fig, label="CS495 Capstone  ·  DeWayne Dantzler  ·  May 2026"):
    ft = fig.add_axes([0, 0, 1, 0.045])
    ft.set_facecolor(NAVY)
    ft.axis("off")
    ft.text(0.5, 0.5, label, color="#94A3B8", fontsize=8,
            ha="center", va="center", transform=ft.transAxes)


def body_ax(fig, rect=None):
    rect = rect or [0.03, 0.06, 0.94, 0.80]
    ax = fig.add_axes(rect)
    ax.set_facecolor(WHITE)
    ax.axis("off")
    return ax


def bullets(ax, items, x=0.03, y=0.94, dy=0.10, fs=11.5):
    for item in items:
        if item["text"] == "":
            y -= dy * 0.5
            continue
        indent = item.get("indent", False)
        col    = item.get("color", "#1E293B")
        bold   = item.get("bold", False)
        bul    = "▸" if indent else "●"
        ax.text(x + (0.025 if indent else 0), y, f"{bul}  {item['text']}",
                color=col, fontsize=fs - (1 if indent else 0),
                fontweight="bold" if bold else "normal",
                transform=ax.transAxes, va="top")
        y -= dy * (0.85 if indent else 1.0)
    return y


def section_title(ax, x, y, text, color=NAVY):
    ax.text(x, y, text, color=color, fontsize=12, fontweight="bold",
            transform=ax.transAxes, va="top")


def embed_image(fig, path, rect):
    try:
        img = mpimg.imread(path)
        ax = fig.add_axes(rect)
        ax.imshow(img, aspect="auto")
        ax.axis("off")
        return ax
    except Exception as e:
        print(f"  Warning: could not load {path}: {e}")
        return None


def sidebar(fig, rect, title, items, fs=10.5):
    ax = fig.add_axes(rect)
    ax.set_facecolor(LIGHT)
    ax.axis("off")
    ax.text(0.5, 0.97, title, ha="center", va="top",
            fontsize=13, fontweight="bold", color=NAVY, transform=ax.transAxes)
    y = 0.88
    for item in items:
        col  = item.get("color", "#1E293B")
        bold = item.get("bold", False)
        text = item["text"]
        if text == "":
            y -= 0.04
            continue
        ax.text(0.04, y, text, color=col, fontsize=fs,
                fontweight="bold" if bold else "normal",
                transform=ax.transAxes, va="top")
        y -= 0.066
    return ax


with PdfPages(PDF_OUT) as pdf:

    # ── SLIDE 1: TITLE ─────────────────────────────────────────────────────────
    fig = new_slide()
    bg = fig.add_axes([0, 0, 1, 1])
    bg.set_facecolor(NAVY)
    bg.axis("off")

    accent = fig.add_axes([0, 0, 0.008, 1])
    accent.set_facecolor(GREEN)
    accent.axis("off")

    ax = fig.add_axes([0.06, 0.10, 0.88, 0.85])
    ax.set_facecolor(NAVY)
    ax.axis("off")

    ax.text(0.5, 0.97, "CS 495 Capstone Project 6", color="#94A3B8",
            fontsize=13, ha="center", va="top", transform=ax.transAxes)
    ax.text(0.5, 0.87,
            "Mathematical and Empirical Models in Agreement:",
            color=WHITE, fontsize=26, fontweight="bold",
            ha="center", va="top", transform=ax.transAxes)
    ax.text(0.5, 0.73,
            "Cross-Validating CRR Binomial Pricing and Machine Learning\n"
            "for Crowd Mispricing Detection in Equity Options",
            color="#38BDF8", fontsize=17, ha="center", va="top",
            transform=ax.transAxes, linespacing=1.5)

    ax.axhline(0.52, color=GREEN, lw=2.5, xmin=0.20, xmax=0.80)

    ax.text(0.5, 0.46, "DeWayne Dantzler", color=WHITE, fontsize=19,
            fontweight="bold", ha="center", va="top", transform=ax.transAxes)
    ax.text(0.5, 0.37, "Bellevue College  ·  CS 495  ·  May 2026",
            color="#94A3B8", fontsize=13, ha="center", va="top",
            transform=ax.transAxes)

    ax.text(0.5, 0.14,
            "Datasets: AMD live chain (April 2026)  +  AAPL 2016–2020 Kaggle (101,535 contracts)",
            color="#64748B", fontsize=11, ha="center", va="top", transform=ax.transAxes)

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 2: OVERVIEW ──────────────────────────────────────────────────────
    fig = new_slide()
    header_bar(fig, "Overview", "The Core Scientific Question and Two-Layer Architecture")
    footer(fig)

    ax = body_ax(fig, [0.03, 0.065, 0.57, 0.80])
    items = [
        {"text": "The Core Scientific Question", "bold": True, "color": NAVY},
        {"text": "Do two completely independent methods — one mathematical, one empirical — agree on which equity options are mispriced by the crowd?", "indent": True},
        {"text": ""},
        {"text": "Layer 1: CRR Binomial Pricing Engine", "bold": True, "color": NAVY},
        {"text": "No-arbitrage lattice using realized volatility (RV30)", "indent": True},
        {"text": "American option backward induction (N=100 steps)", "indent": True},
        {"text": "Mispricing edge + Kelly Criterion sizing framework", "indent": True},
        {"text": ""},
        {"text": "Layer 2: Prediction Market Extensions", "bold": True, "color": NAVY},
        {"text": "XGBoost independent probability estimator (binary ITM/OTM)", "indent": True},
        {"text": "Crowd bias regime detector (herding vs normal)", "indent": True},
        {"text": "Microstructure cost model + walk-forward backtest", "indent": True},
        {"text": ""},
        {"text": "Central Result", "bold": True, "color": GREEN},
        {"text": "Pearson r = 0.413 in herding regime (p = 2.4×10⁻¹⁰)", "indent": True, "color": GREEN},
        {"text": "r ≈ 0 in normal regime → agreement only when crowd is most biased", "indent": True, "color": GREEN},
    ]
    bullets(ax, items, dy=0.082, fs=11.5)

    # Architecture boxes (right)
    rax = fig.add_axes([0.63, 0.065, 0.35, 0.80])
    rax.set_facecolor(LIGHT)
    rax.axis("off")
    rax.text(0.5, 0.97, "Pipeline Architecture", ha="center", va="top",
             fontsize=13, fontweight="bold", color=NAVY, transform=rax.transAxes)

    arch_boxes = [
        (0.04, 0.76, 0.92, 0.16, "Market Data\nAAPL 2016–2020 Kaggle\nAMD Live Chain Apr 2026", "#EFF6FF", BLUE),
        (0.04, 0.56, 0.92, 0.16, "Layer 1: CRR Engine\ntree.py → edge.py → kelly.py", "#F0FDF4", GREEN),
        (0.04, 0.36, 0.92, 0.16, "Layer 2: ML Extensions\np_estimator → bias_detector\nmicro_cost → backtest", "#FDF4FF", PURPLE),
        (0.04, 0.16, 0.92, 0.16, "Cross-Model Comparison\nlayer1_vs_layer2.py\nAgreement in herding regime", "#FFF7ED", GOLD),
    ]
    for bx, by, bw, bh, txt, bg, col in arch_boxes:
        patch = FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0.02",
                               facecolor=bg, edgecolor=col, lw=1.8,
                               transform=rax.transAxes, clip_on=False)
        rax.add_patch(patch)
        rax.text(bx + bw/2, by + bh/2, txt, transform=rax.transAxes,
                 ha="center", va="center", fontsize=10, color=NAVY,
                 fontweight="bold", linespacing=1.4)
        if by > 0.16:
            rax.annotate("", xy=(0.5, by - 0.02), xytext=(0.5, by),
                         xycoords=rax.transAxes, textcoords=rax.transAxes,
                         arrowprops=dict(arrowstyle="->", color=GREY, lw=1.5))

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 3: PROBLEM STATEMENT ────────────────────────────────────────────
    fig = new_slide()
    header_bar(fig, "Problem Statement",
               "When is a model-vs-market divergence large enough — and reliable enough — to trade?")
    footer(fig)

    ax = body_ax(fig, [0.03, 0.065, 0.57, 0.80])
    items = [
        {"text": "The Fundamental Question", "bold": True, "color": NAVY},
        {"text": "When an options model produces a fair value that diverges from the observed market premium, is that divergence large enough to justify a trade? If so, how much capital should be committed?", "indent": True},
        {"text": ""},
        {"text": "Primary Dataset: AMD Live Option Chain (April 2026)", "bold": True, "color": NAVY},
        {"text": "Spot price S₀ = $341.35,  Strike K = $350,  T = 18 days", "indent": True},
        {"text": "Implied volatility σ ≈ 74% (elevated semiconductor-sector levels)", "indent": True},
        {"text": "Risk-free rate r = 5.3% (3-month U.S. Treasury yield)", "indent": True},
        {"text": "4 tickets: Buy Call, Sell Call, Buy Put, Sell Put at K=$350", "indent": True},
        {"text": ""},
        {"text": "Why the CRR Model?", "bold": True, "color": NAVY},
        {"text": "American options require backward induction for early exercise", "indent": True},
        {"text": "Black–Scholes cannot handle American-style contracts", "indent": True, "color": RED},
        {"text": "CRR handles early exercise natively at every node", "indent": True, "color": TEAL},
        {"text": ""},
        {"text": "Secondary Dataset: AAPL 2016–2020 Kaggle", "bold": True, "color": NAVY},
        {"text": "101,535 historical option contracts for ML training + backtest", "indent": True},
        {"text": "Binary ITM/OTM outcomes = training labels for Layer 2", "indent": True},
    ]
    bullets(ax, items, dy=0.080, fs=11.5)

    # Hypotheses boxes
    rax = fig.add_axes([0.63, 0.065, 0.35, 0.80])
    rax.set_facecolor(LIGHT)
    rax.axis("off")
    rax.text(0.5, 0.97, "Three Hypotheses", ha="center", va="top",
             fontsize=13, fontweight="bold", color=NAVY, transform=rax.transAxes)
    hyps = [
        ("H1", "CRR price V_model diverges from V_market by a detectable, signed edge — validated within ±5% for all AMD contracts", "#EFF6FF", BLUE),
        ("H2", "XGBoost Brier score < 0.25 naïve baseline and < market-implied benchmark on the held-out test set", "#F0FDF4", GREEN),
        ("H3", "Fractional Kelly sizing produces materially better risk-adjusted outcomes than full Kelly across the simulated trade history", "#FDF4FF", PURPLE),
    ]
    y = 0.88
    for code, text, bg, col in hyps:
        patch = FancyBboxPatch((0.04, y - 0.24), 0.92, 0.24,
                               boxstyle="round,pad=0.02", facecolor=bg,
                               edgecolor=col, lw=1.8,
                               transform=rax.transAxes, clip_on=False)
        rax.add_patch(patch)
        rax.text(0.50, y - 0.03, code, ha="center", va="top",
                 fontsize=15, fontweight="bold", color=col, transform=rax.transAxes)
        wrapped = wrap(text, 34)
        ty = y - 0.09
        for line in wrapped:
            rax.text(0.50, ty, line, ha="center", va="top",
                     fontsize=9.5, color=NAVY, transform=rax.transAxes)
            ty -= 0.065
        y -= 0.28

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 4: METHODOLOGY — CRR ENGINE ────────────────────────────────────
    fig = new_slide()
    header_bar(fig, "Layer 1: CRR Pricing Engine",
               "Backward induction binomial lattice for American-style equity options (N=100 steps)")
    footer(fig)

    ax = body_ax(fig, [0.03, 0.065, 0.52, 0.80])
    items = [
        {"text": "Forward Pass (Stock Price Lattice)", "bold": True, "color": NAVY},
        {"text": "S(i,j) = S₀ · u^(i−j) · d^j", "indent": True},
        {"text": "u = e^(σ√Δt),  d = 1/u,  Δt = T/N", "indent": True},
        {"text": ""},
        {"text": "Risk-Neutral Probability", "bold": True, "color": NAVY},
        {"text": "p* = (e^(rΔt) − d) / (u − d)", "indent": True},
        {"text": ""},
        {"text": "Backward Induction (American Early Exercise)", "bold": True, "color": NAVY},
        {"text": "hold = e^(−rΔt) [p*·V_up + (1−p*)·V_down]", "indent": True},
        {"text": "V = max(intrinsic, hold)  at every node", "indent": True, "color": GREEN},
        {"text": ""},
        {"text": "Greeks via Centered Finite Differences", "bold": True, "color": NAVY},
        {"text": "Δ (delta), Γ (gamma), θ (theta), ν (vega), ρ (rho)", "indent": True},
        {"text": "Perturbations: h_S=$0.01, h_σ=0.001, h_r=0.0001", "indent": True},
        {"text": ""},
        {"text": "Mispricing Edge & Kelly Sizing", "bold": True, "color": NAVY},
        {"text": "edge = (V_model − V_market) / V_market", "indent": True},
        {"text": "f* = (p·b − q) / b  [full / half / quarter-Kelly]", "indent": True},
        {"text": "No-trade flag when |edge| < 2%", "indent": True, "color": RED},
    ]
    bullets(ax, items, dy=0.073, fs=11.5)

    # Right: lattice schematic
    rax = fig.add_axes([0.58, 0.08, 0.40, 0.79])
    rax.set_facecolor(LIGHT)
    rax.set_xlim(0, 4.8)
    rax.set_ylim(-2.5, 2.8)
    rax.axis("off")
    rax.text(2.4, 2.65, "CRR Binomial Lattice  (N=3 schematic)", ha="center",
             fontsize=11, fontweight="bold", color=NAVY)

    nodes = [(0,0),(1,1),(1,-1),(2,2),(2,0),(2,-2),(3,3),(3,1),(3,-1),(3,-3)]
    edges_e = [(0,0,1,1),(0,0,1,-1),(1,1,2,2),(1,1,2,0),(1,-1,2,0),(1,-1,2,-2),
               (2,2,3,3),(2,2,3,1),(2,0,3,1),(2,0,3,-1),(2,-2,3,-1),(2,-2,3,-3)]
    for x0,y0,x1,y1 in edges_e:
        rax.plot([x0,x1],[y0,y1], color="#94A3B8", lw=1.2, zorder=1)
    node_cols = {0: NAVY, 1: BLUE, 2: TEAL, 3: GREEN}
    labels_n  = {
        (0,0):"S₀", (1,1):"S⋅u", (1,-1):"S⋅d",
        (2,2):"Su²", (2,0):"S", (2,-2):"Sd²",
        (3,3):"max(Su³−K,0)", (3,1):"max(Su⋅d²−K,0)",
        (3,-1):"max(Su⋅d²−K,0)", (3,-3):"max(Sd³−K,0)",
    }
    for x,y in nodes:
        rax.scatter(x, y, s=200, color=node_cols[x], zorder=3)
        if (x,y) in labels_n:
            rax.text(x, y+0.28, labels_n[(x,y)], ha="center", fontsize=8.5,
                     color=node_cols[x], fontweight="bold")

    # Backward arrow
    rax.annotate("", xy=(0.3, -0.5), xytext=(2.5, -0.5),
                 arrowprops=dict(arrowstyle="<-", color=RED, lw=2))
    rax.text(1.4, -0.85, "Backward induction", ha="center",
             fontsize=10, color=RED, fontweight="bold")
    rax.text(2.4, -2.35, "← Forward pass →", ha="center",
             fontsize=10, color=GREY, style="italic")

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 5: FIGURE 1 — CRR vs MARKET ────────────────────────────────────
    fig = new_slide()
    header_bar(fig, "Figure 1 — CRR Model vs. Market Price",
               "Pricing accuracy validation for all four AMD trade tickets (K=$350, S₀=$341.35, σ≈74%, T=18 days)")
    footer(fig)

    embed_image(fig, f"{OUT_DIR}/model_vs_market.png", [0.04, 0.09, 0.53, 0.76])

    side_items = [
        {"text": "How to read:", "bold": True, "color": NAVY},
        {"text": "Each bar pair = one trade ticket", "indent": True},
        {"text": "Blue = V_model  (CRR, N=100 steps)", "indent": True},
        {"text": "Orange = V_market (Fidelity observed)", "indent": True},
        {"text": "% error annotated above each pair", "indent": True},
        {"text": ""},
        {"text": "Key Results:", "bold": True, "color": NAVY},
        {"text": "Sub-rounding error on call contracts", "indent": True, "color": TEAL},
        {"text": "Near-zero error on put contracts", "indent": True, "color": TEAL},
        {"text": "All within ±5% acceptance band ✓", "indent": True, "color": GREEN},
        {"text": "Hypothesis H1 validated", "indent": True, "color": GREEN},
        {"text": ""},
        {"text": "Why it matters:", "bold": True, "color": NAVY},
        {"text": "Without this validation step, any downstream Kelly sizing rests on an uncalibrated foundation. This step proves the CRR model is a reliable fair-value benchmark for mispricing detection.", "indent": True},
    ]
    ax = sidebar(fig, [0.61, 0.09, 0.37, 0.76], "", side_items, fs=11)
    ax.text(0.5, 0.97, "How to Read", ha="center", va="top",
            fontsize=13, fontweight="bold", color=NAVY, transform=ax.transAxes)

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 6: FIGURE 2 — CONVERGENCE ──────────────────────────────────────
    fig = new_slide()
    header_bar(fig, "Figure 2 — Binomial Tree Convergence",
               "CRR price stabilization as step count N increases from 5 to 200")
    footer(fig)

    embed_image(fig, f"{OUT_DIR}/convergence.png", [0.04, 0.09, 0.53, 0.76])

    side_items = [
        {"text": "How to read:", "bold": True, "color": NAVY},
        {"text": "x-axis: step count N (5 to 200)", "indent": True},
        {"text": "y-axis: CRR American price ($)", "indent": True},
        {"text": "Each line = one AMD trade ticket", "indent": True},
        {"text": "Convergence = price stabilizes flat", "indent": True},
        {"text": ""},
        {"text": "Key Results:", "bold": True, "color": NAVY},
        {"text": "Put (≈$27) stable by N ≈ 25", "indent": True, "color": TEAL},
        {"text": "Call (≈$19) stable by N ≈ 10", "indent": True, "color": TEAL},
        {"text": "N=100 is conservative — well beyond convergence threshold", "indent": True, "color": GREEN},
        {"text": ""},
        {"text": "Literature Validation:", "bold": True, "color": NAVY},
        {"text": "Nwobi & Ugomma (2023): N=50–100 sufficient for standard equity options", "indent": True},
        {"text": "Short T=18 days converges faster than longer-dated contracts", "indent": True},
        {"text": "No visible odd/even oscillation — numerical stability confirmed", "indent": True},
    ]
    ax = sidebar(fig, [0.61, 0.09, 0.37, 0.76], "", side_items, fs=11)
    ax.text(0.5, 0.97, "How to Read", ha="center", va="top",
            fontsize=13, fontweight="bold", color=NAVY, transform=ax.transAxes)

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 7: FIGURE 3 — EARLY EXERCISE ───────────────────────────────────
    fig = new_slide()
    header_bar(fig, "Figure 3 — Early Exercise Boundary",
               "Critical stock price S* below which immediate exercise dominates continuation for AMD American puts")
    footer(fig)

    embed_image(fig, f"{OUT_DIR}/early_exercise_boundary.png", [0.04, 0.09, 0.53, 0.76])

    side_items = [
        {"text": "How to read:", "bold": True, "color": NAVY},
        {"text": "y-axis: S* (critical exercise price)", "indent": True},
        {"text": "x-axis: calendar days elapsed", "indent": True},
        {"text": "Dashed line: current S₀ = $341.35", "indent": True},
        {"text": "S* above dashed line → exercise now", "indent": True},
        {"text": ""},
        {"text": "Key Findings:", "bold": True, "color": NAVY},
        {"text": "S* starts near $247 at day 3", "indent": True, "color": TEAL},
        {"text": "Rises steeply to ≈$336 by day 18", "indent": True, "color": TEAL},
        {"text": "Saw-tooth = odd/even lattice parity artifact", "indent": True},
        {"text": ""},
        {"text": "Why it matters:", "bold": True, "color": NAVY},
        {"text": "Black–Scholes CANNOT price American options", "indent": True, "color": RED},
        {"text": "CRR is required — this validates the model architecture choice", "indent": True, "color": GREEN},
        {"text": "Optimal exercise region expands rapidly in the final days", "indent": True},
        {"text": "Consistent with Mou et al. (2022) and Barone-Adesi & Whaley (1987)", "indent": True},
    ]
    ax = sidebar(fig, [0.61, 0.09, 0.37, 0.76], "", side_items, fs=11)
    ax.text(0.5, 0.97, "How to Read", ha="center", va="top",
            fontsize=13, fontweight="bold", color=NAVY, transform=ax.transAxes)

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 8: FIGURE 4 — KELLY FRACTIONS ──────────────────────────────────
    fig = new_slide()
    header_bar(fig, "Figure 4 — Kelly Fractions & Mispricing Edge",
               "Position-sizing recommendations for AMD trade tickets: an unexpected finding")
    footer(fig)

    embed_image(fig, f"{OUT_DIR}/kelly_fractions.png", [0.04, 0.09, 0.53, 0.76])

    side_items = [
        {"text": "How to read:", "bold": True, "color": NAVY},
        {"text": "y-axis: Kelly fraction (% of capital)", "indent": True},
        {"text": "Red = Full Kelly, Orange = Half, Gold = Quarter", "indent": True},
        {"text": "Above zero → BUY; at/below zero → NO TRADE", "indent": True},
        {"text": ""},
        {"text": "Unexpected Finding:", "bold": True, "color": RED},
        {"text": "All four AMD tickets show Kelly fractions at or near ZERO", "indent": True, "color": RED},
        {"text": "NO-TRADE condition detected ✓", "indent": True, "color": RED},
        {"text": ""},
        {"text": "Interpretation:", "bold": True, "color": NAVY},
        {"text": "Zero Kelly = a finding, not a failure", "indent": True, "color": TEAL},
        {"text": "AMD market was efficiently pricing at this snapshot (normal regime)", "indent": True},
        {"text": "Pipeline correctly suppresses trading when no edge exists", "indent": True, "color": GREEN},
        {"text": ""},
        {"text": "Critical Contrast:", "bold": True, "color": NAVY},
        {"text": "AAPL backtest → $2.9M over 4 years", "indent": True, "color": GREEN},
        {"text": "Single snapshot ≠ persistent edge", "indent": True},
        {"text": "Historical backtest is the primary profitability evaluation", "indent": True},
    ]
    ax = sidebar(fig, [0.61, 0.09, 0.37, 0.76], "", side_items, fs=10.5)
    ax.text(0.5, 0.97, "How to Read", ha="center", va="top",
            fontsize=13, fontweight="bold", color=NAVY, transform=ax.transAxes)

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 9: LAYER 2 METHODOLOGY ─────────────────────────────────────────
    fig = new_slide()
    header_bar(fig, "Layer 2: Prediction Market Extensions",
               "Independent probability estimation, crowd bias detection, and walk-forward backtest")
    footer(fig)

    ax_l = body_ax(fig, [0.03, 0.065, 0.48, 0.80])
    items = [
        {"text": "Independent Probability Estimator", "bold": True, "color": NAVY},
        {"text": "XGBoost on binary ITM/OTM labels (no IV input!)", "indent": True},
        {"text": "Features: moneyness, DTE, RV–IV spread, vol/OI, bid-ask", "indent": True},
        {"text": "Platt scaling calibration → Brier score = 0.211 < 0.25", "indent": True, "color": GREEN},
        {"text": ""},
        {"text": "Crowd Bias Regime Detector", "bold": True, "color": NAVY},
        {"text": "HERDING: IV−RV spread > 10%  or  rapid IV momentum", "indent": True, "color": RED},
        {"text": "NORMAL: spread < 5%, quiet conditions", "indent": True, "color": TEAL},
        {"text": "Edge threshold: 2% normal, 8% herding (high-conviction only)", "indent": True},
        {"text": ""},
        {"text": "Microstructure Cost Model", "bold": True, "color": NAVY},
        {"text": "edge_net = edge_indep − (0.5×spread + fee + slippage) / V_market", "indent": True},
        {"text": "Fee = $0.65/contract, slippage = $0.005/contract", "indent": True},
        {"text": "VaR: reject positions > 5% of capital", "indent": True},
        {"text": "Circuit breaker: halt if drawdown > 15%", "indent": True},
        {"text": ""},
        {"text": "Walk-Forward Backtest", "bold": True, "color": NAVY},
        {"text": "Chronological 60/20/20 split (no shuffling, no lookahead)", "indent": True},
        {"text": "Quarter-Kelly sizing → $2.9M cumulative P&L (2017–2021)", "indent": True, "color": GREEN},
    ]
    bullets(ax_l, items, dy=0.072, fs=11)

    # Right: feature importance bar chart
    rax = fig.add_axes([0.56, 0.065, 0.42, 0.80])
    rax.set_facecolor(LIGHT)
    rax.axis("off")
    rax.text(0.5, 0.97, "Top Features by XGBoost Gain", ha="center", va="top",
             fontsize=13, fontweight="bold", color=NAVY, transform=rax.transAxes)

    features = [
        ("Moneyness (S/K)",      0.38, NAVY),
        ("Days to Expiration",   0.24, BLUE),
        ("RV–IV Spread",    0.17, TEAL),
        ("Volume / OI Ratio",    0.11, GREEN),
        ("Bid–Ask Spread",  0.10, PURPLE),
    ]
    fy = 0.85
    for feat, gain, col in features:
        rax.text(0.03, fy, feat, transform=rax.transAxes,
                 fontsize=11, color=NAVY, va="center")
        bw = gain * 0.87
        rect = Rectangle((0.42, fy - 0.028), bw, 0.056,
                          facecolor=col, alpha=0.85,
                          transform=rax.transAxes)
        rax.add_patch(rect)
        rax.text(0.42 + bw + 0.01, fy, f"{gain:.0%}", transform=rax.transAxes,
                 fontsize=10.5, color=col, va="center", fontweight="bold")
        fy -= 0.115

    rax.text(0.5, 0.38,
             "Moneyness + DTE account for 62%\nof predictive gain — consistent with\nfinancial theory.  The RV–IV spread\nranked 3rd, confirming crowd bias\ncontributes beyond moneyness and\nDTE alone (direct link to Figure 5).",
             ha="center", va="top", fontsize=11, color="#1E293B",
             transform=rax.transAxes, linespacing=1.5,
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#EFF6FF",
                       edgecolor=BLUE, lw=1.5))

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 10: FIGURE 5 — REGIME ANALYSIS ─────────────────────────────────
    fig = new_slide()
    header_bar(fig, "Figure 5 — Crowd Bias Regime Analysis",
               "AAPL ATM implied volatility vs. 30-day realized volatility, 2016–2021")
    footer(fig)

    embed_image(fig, f"{OUT_DIR}/regime_analysis.png", [0.03, 0.09, 0.62, 0.77])

    side_items = [
        {"text": "Three Panels:", "bold": True, "color": NAVY},
        {"text": "Top: ATM IV (blue) vs RV-30d (red)", "indent": True},
        {"text": "Mid: RV–IV spread; orange=IV>RV, teal=IV≤RV", "indent": True},
        {"text": "Bottom: Daily regime label (herding / normal)", "indent": True},
        {"text": ""},
        {"text": "COVID-19 Event (2020):", "bold": True, "color": RED},
        {"text": "ONLY sustained period where RV > IV", "indent": True, "color": RED},
        {"text": "Crowd UNDERPRICED volatility — rare inversion", "indent": True, "color": RED},
        {"text": ""},
        {"text": "Herding Statistics:", "bold": True, "color": NAVY},
        {"text": "n=217 contracts in herding regime (7.4% of dates)", "indent": True, "color": TEAL},
        {"text": "This 7.4% is EXACTLY where both models agree", "indent": True, "color": GREEN},
        {"text": ""},
        {"text": "Bridge to Layer 2:", "bold": True, "color": NAVY},
        {"text": "Regime label conditions the edge threshold", "indent": True},
        {"text": "Prevents over-trading in low-signal normal environments", "indent": True},
        {"text": "Unlocks high-conviction trades in herding regime", "indent": True, "color": GREEN},
    ]
    ax = sidebar(fig, [0.68, 0.09, 0.30, 0.77], "", side_items, fs=10.5)
    ax.text(0.5, 0.97, "Interpretation", ha="center", va="top",
            fontsize=13, fontweight="bold", color=NAVY, transform=ax.transAxes)

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 11: FIGURE 6 — CROSS-MODEL COMPARISON ──────────────────────────
    fig = new_slide()
    header_bar(fig, "Figure 6 — Cross-Model Comparison: Mathematical vs. Empirical",
               "CRR (Layer 1) vs. XGBoost (Layer 2) on the same 3,000 AAPL contracts — the analytical centerpiece")
    footer(fig)

    embed_image(fig, f"{OUT_DIR}/l1_vs_l2_comparison.png", [0.02, 0.09, 0.66, 0.77])

    rax = fig.add_axes([0.71, 0.09, 0.28, 0.77])
    rax.set_facecolor(LIGHT)
    rax.axis("off")
    rax.text(0.5, 0.99, "The Core Finding", ha="center", va="top",
             fontsize=13, fontweight="bold", color=NAVY, transform=rax.transAxes)

    panel_items = [
        ("Panel 1: Edge Scatter", NAVY, True),
        ("L1 edge (x) vs L2 edge (y)", "#1E293B", False),
        ("Red=herding, Blue=normal", "#1E293B", False),
        ("Panel 2: Agreement", NAVY, True),
        ("44.2% both BUY (Q1)", TEAL, False),
        ("1.2% both SELL (Q3)", RED, False),
        ("54.7% disagree", GREY, False),
        ("Panel 3: ITM Rate by Zone", NAVY, True),
        ("Q3 (both SELL): 76.5% ITM", RED, False),
        ("Q1 (both BUY): 63.4% ITM", TEAL, False),
        ("Crowd overprices puts that DO expire ITM", "#1E293B", False),
        ("Panel 4: Regime Correlation", NAVY, True),
        ("Normal: r=0.013  (p=0.499) ≈ zero", GREY, False),
        ("Herding: r=0.413  (p=2.4×10⁻¹⁰)", GREEN, False),
        ("Models agree ONLY when crowd", GREEN, False),
        ("is most behaviorally biased", GREEN, False),
    ]
    y = 0.90
    for txt, col, bold in panel_items:
        rax.text(0.04, y, txt, color=col, fontsize=10,
                 fontweight="bold" if bold else "normal",
                 transform=rax.transAxes, va="top")
        y -= 0.065

    rax.text(0.5, 0.08,
             "Bidirectional cross-validation:\nneither model designed to agree\nwith the other. Agreement arises\nfrom shared reality.",
             ha="center", va="bottom", fontsize=10, color=NAVY,
             transform=rax.transAxes, linespacing=1.5,
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#F0FDF4",
                       edgecolor=GREEN, lw=2))

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 12: FIGURE 7 — BACKTEST ─────────────────────────────────────────
    fig = new_slide()
    header_bar(fig, "Figure 7 — Walk-Forward Backtest Results",
               "Quarter-Kelly P&L: AAPL 2017–2021 out-of-sample validation (seed=42)")
    footer(fig)

    embed_image(fig, f"{OUT_DIR}/pnl_curve.png", [0.04, 0.09, 0.55, 0.77])

    side_items = [
        {"text": "Three Growth Phases:", "bold": True, "color": NAVY},
        {"text": "2017–mid 2018: Steady early gains ~$400K from mild herding signals", "indent": True},
        {"text": "Mid 2018–2019: Plateau $600K–$800K; regime detector suppressed low-signal trading", "indent": True},
        {"text": "2020 onward: COVID spike → accelerated to $2.9M; high-conviction quarter-Kelly positions deployed", "indent": True, "color": GREEN},
        {"text": ""},
        {"text": "Validation Metrics:", "bold": True, "color": NAVY},
        {"text": "Mean per-trade P&L: $51.31", "indent": True, "color": TEAL},
        {"text": "Max drawdown: < 15% (never triggered)", "indent": True, "color": TEAL},
        {"text": "Cumulative P&L monotonically positive", "indent": True, "color": TEAL},
        {"text": "No extended consecutive-loss periods", "indent": True, "color": TEAL},
        {"text": ""},
        {"text": "Why it matters:", "bold": True, "color": NAVY},
        {"text": "Tests the complete trading policy — pricing, regime detection, micro cost, Kelly sizing — against realized market outcomes never seen during training. Hypothesis H3 validated ✓", "indent": True, "color": GREEN},
    ]
    ax = sidebar(fig, [0.63, 0.09, 0.35, 0.77], "", side_items, fs=11)
    ax.text(0.5, 0.97, "How to Read", ha="center", va="top",
            fontsize=13, fontweight="bold", color=NAVY, transform=ax.transAxes)

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 13: UNEXPECTED FINDINGS ────────────────────────────────────────
    fig = new_slide()
    header_bar(fig, "Unexpected Findings",
               "Three results not anticipated by the pre-study hypotheses")
    footer(fig)

    box_data = [
        (0.02, 0.56, 0.30, 0.37,
         "Near-Zero Kelly Fractions\non the AMD Snapshot",
         "All four AMD tickets produced Kelly fractions at or near zero. The pipeline correctly identified a NO-TRADE condition: the market was efficiently pricing AMD contracts at this snapshot. A well-calibrated model should suppress trading when there is no exploitable edge.",
         "#FFF7ED", GOLD),
        (0.35, 0.56, 0.30, 0.37,
         "COVID-19 Inverted the\nTypical IV Premium",
         "2020 is the only sustained period where realized volatility exceeded implied volatility. The crowd underpriced options during the most extreme event in the sample. The pipeline gained $2M+ by detecting deep underpricing, not the usual overpricing trade.",
         "#FEF2F2", RED),
        (0.68, 0.56, 0.30, 0.37,
         "Simpson's Paradox in\nL1–L2 Correlation",
         "Overall Pearson r=0.032 could be misread as models disagreeing. The large normal-regime population (n=2,727) dominates and dilutes the strong herding signal (r=0.413, n=217). Stopping at the aggregate correlation misses the central cross-validation result.",
         "#EFF6FF", BLUE),
    ]
    for x, y, w, h, title, body, bg, col in box_data:
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01",
                               facecolor=bg, edgecolor=col, lw=2.5,
                               transform=fig.transFigure, clip_on=False)
        fig.add_artist(patch)
        fig.text(x + w/2, y + h - 0.05, title, ha="center", va="top",
                 fontsize=12, fontweight="bold", color=col)
        wy = y + h - 0.12
        for line in wrap(body, 38):
            fig.text(x + w/2, wy, line, ha="center", va="top",
                     fontsize=9.5, color="#1E293B")
            wy -= 0.048

    # Bottom callout
    patch2 = FancyBboxPatch((0.04, 0.095), 0.92, 0.12,
                            boxstyle="round,pad=0.01", facecolor="#F0FDF4",
                            edgecolor=GREEN, lw=2,
                            transform=fig.transFigure, clip_on=False)
    fig.add_artist(patch2)
    fig.text(0.50, 0.195,
             "Key Takeaway: All three unexpected findings reinforce the same conclusion — "
             "the pipeline works precisely BECAUSE it is regime-aware. Without the crowd bias detector, "
             "the COVID inversion and the Simpson's Paradox would produce incorrect signals or missed opportunities.",
             ha="center", va="top", fontsize=11, color=NAVY, fontweight="bold")

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 14: STATISTICAL VALIDATION ─────────────────────────────────────
    fig = new_slide()
    header_bar(fig, "Statistical Validation",
               "Quantitative confirmation of all three hypotheses")
    footer(fig)

    ax = body_ax(fig, [0.03, 0.065, 0.94, 0.80])

    rows = [
        ("H1", "CRR Pricing Accuracy",   "±5% for all four AMD contracts", "All tickets within ±0.0% (sub-rounding)", GREEN, "✓"),
        ("H1", "Greek Validation",        "Within ±10% of Fidelity reported",  "All five Greeks validated; Vega max ≤9.3%", GREEN, "✓"),
        ("H1", "Convergence",             "N=100 sufficient; price stable pre-N=100","Stable at N≈10–25 (T=18d, faster than lit.)", GREEN, "✓"),
        ("H2", "Brier Score",             "< 0.25 naïve and < market-implied",  "0.211 with Platt scaling ✓", GREEN, "✓"),
        ("H2", "Calibration",             "Mean bin deviation < 0.04",           "p=[0.3–0.7] tracked ITM freq; tails minor overconf.", GREEN, "✓"),
        ("H3", "Backtest P&L",            "Positive at test-set end",             "$2.9M cumulative; mean $51.31/trade", GREEN, "✓"),
        ("H3", "Max Drawdown",            "Below 15% circuit-breaker at all times","Never triggered in 2017–2021 window", GREEN, "✓"),
        ("H3", "Regime Correlation",      "Herding r > normal r",                 "Herding r=0.413 vs Normal r=0.013 (p=2.4×10⁻¹⁰)", GREEN, "✓"),
    ]

    col_xs = [0.01, 0.06, 0.19, 0.44, 0.70, 0.97]
    hdrs   = ["",   "Metric", "Acceptance Criterion", "Result", "Finding", ""]

    y_hdr = 0.94
    hdr_rect = Rectangle((0.0, y_hdr - 0.01), 1.0, 0.08,
                          facecolor=NAVY, transform=ax.transAxes)
    ax.add_patch(hdr_rect)
    for xi, hd in zip(col_xs, hdrs):
        ax.text(xi, y_hdr + 0.025, hd, color=WHITE, fontsize=10.5,
                fontweight="bold", transform=ax.transAxes, va="center")

    y = y_hdr - 0.045
    for i, (hyp, metric, criterion, result, col, mark) in enumerate(rows):
        bg_c = LIGHT if i % 2 == 0 else WHITE
        row_rect = Rectangle((0.0, y - 0.060), 1.0, 0.075,
                              facecolor=bg_c, transform=ax.transAxes)
        ax.add_patch(row_rect)
        ax.text(col_xs[0], y - 0.015, hyp, transform=ax.transAxes,
                fontsize=9.5, va="top", color=BLUE, fontweight="bold")
        ax.text(col_xs[1], y - 0.015, metric, transform=ax.transAxes,
                fontsize=9.5, va="top", color="#1E293B", fontweight="bold")
        ax.text(col_xs[2], y - 0.015, criterion, transform=ax.transAxes,
                fontsize=9.5, va="top", color="#1E293B")
        ax.text(col_xs[3], y - 0.015, result, transform=ax.transAxes,
                fontsize=9.5, va="top", color=col, fontweight="bold")
        ax.text(col_xs[5], y - 0.015, mark, transform=ax.transAxes,
                fontsize=12, va="top", color=col, fontweight="bold")
        y -= 0.083

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 15: CONCLUSIONS ─────────────────────────────────────────────────
    fig = new_slide()
    header_bar(fig, "Conclusions",
               "The central contribution and implications of this research")
    footer(fig)

    ax_l = body_ax(fig, [0.03, 0.065, 0.55, 0.80])
    items = [
        {"text": "Central Contribution", "bold": True, "color": NAVY},
        {"text": "A mathematical no-arbitrage model (CRR) and an empirical ML model (XGBoost) — using entirely independent inputs — agree on the direction of options mispricing in high-herding-regime conditions.", "indent": True},
        {"text": "This bidirectional agreement constitutes mutual cross-validation; neither model was designed to confirm the other.", "indent": True, "color": GREEN},
        {"text": ""},
        {"text": "H1 Confirmed: CRR as Reliable Benchmark", "bold": True, "color": NAVY},
        {"text": "Sub-rounding error on AMD contracts validates CRR as a fair-value reference for mispricing detection", "indent": True},
        {"text": ""},
        {"text": "H2 Confirmed: XGBoost Independent Estimator", "bold": True, "color": NAVY},
        {"text": "Brier score 0.211 < 0.25 baseline; RV–IV spread is 3rd most important feature", "indent": True},
        {"text": ""},
        {"text": "H3 Confirmed: Fractional Kelly Dominates", "bold": True, "color": NAVY},
        {"text": "$2.9M cumulative P&L, max drawdown < 15%, positive mean per-trade return", "indent": True, "color": GREEN},
        {"text": ""},
        {"text": "Practical Implication", "bold": True, "color": NAVY},
        {"text": "Single-snapshot AMD analysis correctly identifies NO-TRADE — the model works because it says NO when there is no edge.", "indent": True},
    ]
    bullets(ax_l, items, dy=0.083, fs=11.5)

    # Right: key numbers
    rax = fig.add_axes([0.62, 0.065, 0.36, 0.80])
    rax.set_facecolor(LIGHT)
    rax.axis("off")
    rax.text(0.5, 0.97, "Key Numbers at a Glance", ha="center", va="top",
             fontsize=13, fontweight="bold", color=NAVY, transform=rax.transAxes)

    stats = [
        ("r = 0.413",   "Herding-regime L1–L2\nPearson correlation", GREEN),
        ("p = 2.4×10⁻¹⁰", "Statistical significance\nof herding agreement", BLUE),
        ("$2.9M",       "Cumulative backtest P&L\n(quarter-Kelly, 2017–2021)", TEAL),
        ("0.211",       "XGBoost Brier score\n(below 0.25 naïve baseline)", PURPLE),
        ("< 15%",       "Max drawdown — circuit\nbreaker never triggered", GREEN),
        ("N = 100",     "CRR step count; converges\nat N≈10–25 for T=18d", NAVY),
    ]
    sy = 0.88
    for val, desc, col in stats:
        patch = FancyBboxPatch((0.04, sy - 0.12), 0.92, 0.125,
                               boxstyle="round,pad=0.01", facecolor=WHITE,
                               edgecolor=col, lw=1.8,
                               transform=rax.transAxes)
        rax.add_patch(patch)
        rax.text(0.26, sy - 0.055, val, ha="center", va="center",
                 fontsize=15, fontweight="bold", color=col,
                 transform=rax.transAxes)
        rax.text(0.64, sy - 0.055, desc, ha="center", va="center",
                 fontsize=9.5, color="#1E293B",
                 transform=rax.transAxes, linespacing=1.3)
        sy -= 0.143

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

    # ── SLIDE 16: REFERENCES ──────────────────────────────────────────────────
    fig = new_slide()
    header_bar(fig, "References",
               "Key sources supporting the theoretical and empirical framework")
    footer(fig)

    ax = body_ax(fig, [0.03, 0.065, 0.94, 0.80])

    refs = [
        ("Cox, Ross & Rubinstein (1979)", "Option pricing: A simplified approach", "Journal of Financial Economics 7(3), 229–263", NAVY),
        ("Black & Scholes (1973)", "The pricing of options and corporate liabilities", "Journal of Political Economy 81(3), 637–654", NAVY),
        ("Nwobi & Ugomma (2023)", "CRR binomial model: accuracy, convergence and stability using Python", "IJSRP", BLUE),
        ("Josheski & Apostolov (2020)", "A review of binomial and trinomial models for option pricing", "Econometrics: Advances in Applied Data Analysis", BLUE),
        ("Carr & Wu (2009)", "Variance risk premiums", "Review of Financial Studies 22(3), 1311–1341", TEAL),
        ("Jackwerth & Rubinstein (1996)", "Recovering probability distributions from option prices", "Journal of Finance 51(5), 1611–1631", TEAL),
        ("Kelly (1956)", "A new interpretation of information rate", "Bell System Technical Journal 35(4), 917–926", PURPLE),
        ("MacLean, Thorp & Ziemba (2010)", "Good and bad properties of the Kelly criterion", "Risk 23(2), 20–25", PURPLE),
        ("Mou et al. (2022)", "American put option pricing under binomial consideration", "ICEMED 2022, Atlantis Press", GREEN),
        ("Thaler & Ziemba (1988)", "Anomalies: Parimutuel betting markets", "Journal of Economic Perspectives 2(2), 161–174", GOLD),
        ("Wolfers & Zitzewitz (2004)", "Prediction markets", "Journal of Economic Perspectives 18(2), 107–126", GOLD),
        ("Manski (2006)", "Interpreting the predictions of prediction markets", "Economics Letters 91(3), 425–429", RED),
    ]

    y = 0.96
    col_x = [0.01, 0.51]
    for i, (authors, title, journal, col) in enumerate(refs):
        xi = col_x[i % 2]
        if i % 2 == 0 and i > 0:
            y -= 0.118
        ax.text(xi, y, f"[{i+1}]  {authors}", transform=ax.transAxes,
                fontsize=9.5, color=col, va="top", fontweight="bold")
        ax.text(xi, y - 0.033, f'"{title}"', transform=ax.transAxes,
                fontsize=8.5, color="#1E293B", va="top", style="italic")
        ax.text(xi, y - 0.063, journal, transform=ax.transAxes,
                fontsize=8.5, color=GREY, va="top")

    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

print(f"Done! Saved {PDF_OUT}")
