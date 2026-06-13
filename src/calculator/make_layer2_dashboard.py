"""
make_layer2_dashboard.py
Interactive HTML dashboard for the Layer 2 walk-forward backtest.

Renders matplotlib frames as base64 PNGs embedded in a self-contained
HTML player (same structure as crr_pipeline_animation.html).

Frame sequence:
  0   -- Intro / key stats
  1   -- Layer 2 pipeline architecture
  2-17 -- Walk-forward windows (one per quarter, 2017Q1-2020Q4)
  18  -- Regime comparison (normal vs herding)
  19  -- Probability calibration curves
  20  -- Brier score trend over time
  21  -- Full P&L summary
  22  -- Summary metrics table

Saves layer2_dashboard.html to project root.
"""

import os, io, base64
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

ROOT       = os.path.dirname(os.path.abspath(__file__))
TRADES_CSV = os.path.join(ROOT, "project", "outputs", "backtest_trades.csv")
OUT_HTML   = os.path.join(ROOT, "layer2_dashboard.html")

# ── Dark palette (matches crr_pipeline_animation.html) ───────────────────────
BG     = '#0d1117'
PANEL  = '#161b22'
BORDER = '#30363d'
WHITE  = '#f1f5f9'
DIM    = '#94a3b8'
BLUE   = '#2563eb'
PURPLE = '#7c3aed'
GREEN  = '#059669'
RED    = '#dc2626'
AMBER  = '#f59e0b'
TEAL   = '#0e7490'
NC     = BLUE   # normal regime
HC     = AMBER  # herding regime

FW, FH = 14, 7.5   # figure size (inches)


def to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=110,
                facecolor=BG, bbox_inches='tight')
    buf.seek(0)
    enc = base64.b64encode(buf.getvalue()).decode('ascii')
    plt.close(fig)
    return enc


def dark_ax(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(PANEL)
    for sp in ax.spines.values():
        sp.set_color(BORDER)
    ax.tick_params(colors=DIM, labelsize=7)
    if title:   ax.set_title(title,  color=WHITE, fontsize=9,  pad=4)
    if xlabel:  ax.set_xlabel(xlabel, color=DIM,  fontsize=8)
    if ylabel:  ax.set_ylabel(ylabel, color=DIM,  fontsize=8)
    ax.grid(color=BORDER, alpha=0.4)


def sharpe(series):
    s = series.std()
    return series.mean() / s * np.sqrt(252) if s > 0 else 0.0


def max_dd(cum):
    return float((cum.cummax() - cum).max())


# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading backtest_trades.csv ...")
df = pd.read_csv(TRADES_CSV, parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)
df["quarter"] = df["date"].dt.to_period("Q")

put_df   = df[df["option_type"] == "put"].copy()
call_df  = df[df["option_type"] == "call"].copy()
quarters = sorted(df["quarter"].unique())
n_q      = len(quarters)

# Combined daily cumulative P&L for the timeline
daily_cum = (df.groupby("date")["trade_pnl"].sum()
               .cumsum().reset_index()
               .rename(columns={"trade_pnl": "cum_pnl"}))

frames = []   # list of (b64, label)

def add(fig, label):
    frames.append((to_b64(fig), label))


# ─────────────────────────────────────────────────────────────────────────────
# FRAME 0 — Intro
# ─────────────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(FW, FH), facecolor=BG)
ax  = fig.add_axes([0, 0, 1, 1], facecolor=BG)
ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_visible(False)

ax.text(0.5, 0.84, "Layer 2 Walk-Forward Backtest Dashboard",
        ha='center', va='center', fontsize=24, fontweight='bold',
        color=WHITE, transform=ax.transAxes)
ax.text(0.5, 0.74,
        "Step through 16 quarterly windows  |  Explore regimes  |  "
        "Check calibration",
        ha='center', va='center', fontsize=12, color=DIM,
        transform=ax.transAxes)

# Key stat boxes
stats = [
    (f"{len(put_df):,}",  "Put Trades",  PURPLE),
    (f"{len(call_df):,}", "Call Trades", BLUE),
    (f"{n_q}",            "Quarters",    TEAL),
    ("91.5%",             "Normal Days", NC),
    ("8.5%",              "Herding Days",HC),
]
for i, (val, lbl, col) in enumerate(stats):
    x = 0.08 + i * 0.195
    r = mpatches.FancyBboxPatch((x - 0.08, 0.39), 0.155, 0.20,
        boxstyle="round,pad=0.01", fc=PANEL, ec=col,
        lw=2, transform=ax.transAxes)
    ax.add_patch(r)
    ax.text(x, 0.525, val, ha='center', va='center',
            fontsize=17, fontweight='bold', color=col,
            transform=ax.transAxes)
    ax.text(x, 0.425, lbl, ha='center', va='center',
            fontsize=8.5, color=DIM, transform=ax.transAxes)

ax.text(0.5, 0.25,
        "12-month training window  |  3-month test window  "
        "|  Quarter-Kelly sizing  |  $100K capital",
        ha='center', va='center', fontsize=10, color=DIM,
        transform=ax.transAxes)
ax.text(0.5, 0.17,
        "Normal regime: 2% min edge    |    "
        "Herding regime: 8% min edge    |    "
        "15% drawdown circuit breaker",
        ha='center', va='center', fontsize=10, color=AMBER,
        transform=ax.transAxes)
ax.text(0.5, 0.07,
        "CS495 Deep Scholar  |  AAPL Options 2016-2020  "
        "|  github.com/dantzlerdc/CS495-Deep-Scholar",
        ha='center', va='center', fontsize=8, color=BORDER,
        transform=ax.transAxes)
add(fig, "Introduction")


# ─────────────────────────────────────────────────────────────────────────────
# FRAME 1 — Architecture diagram
# ─────────────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(FW, FH), facecolor=BG)
ax  = fig.add_axes([0.01, 0.04, 0.98, 0.88], facecolor=BG)
ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_visible(False)
ax.set_xlim(0, 10); ax.set_ylim(0, 7)
fig.text(0.5, 0.96, "Layer 2 Pipeline Architecture",
         ha='center', color=WHITE, fontsize=13, fontweight='bold')

boxes = [
    (1.1, 5.6, "market_data.py",   "Step 1", TEAL,
     "Load AAPL CSV\nCompute RV30\nLabel ITM/OTM"),
    (3.2, 5.6, "p_estimator.py",   "Step 2", BLUE,
     "XGBoost + Platt\np_independent\nBrier 0.103"),
    (5.3, 5.6, "bias_detector.py", "Step 3", PURPLE,
     "RV-IV spread\niv_mom 3d/5d\nNormal|Herding"),
    (7.4, 5.6, "micro_cost.py",    "Step 4", AMBER,
     "bid-ask spread\nfee $0.0065/sh\nnet_edge filter"),
    (2.2, 2.6, "calibration.py",   "Step 5", GREEN,
     "Brier score\nECE\nReliability diag"),
    (5.0, 2.6, "policy.py",        "Step 6", TEAL,
     "Regime-gated\nTRADE/NO TRADE\nKelly sizing"),
    (7.8, 2.6, "backtest.py",      "Step 7", RED,
     "Walk-forward\n12mo train 3mo\nP&L + metrics"),
]
for (x, y, name, step, col, desc) in boxes:
    r = mpatches.FancyBboxPatch(
        (x - 0.95, y - 0.80), 1.9, 1.65,
        boxstyle="round,pad=0.06", fc=PANEL, ec=col, lw=1.8)
    ax.add_patch(r)
    ax.text(x, y + 0.60, step,  ha='center', fontsize=7,
            color=col, fontweight='bold')
    ax.text(x, y + 0.18, name,  ha='center', fontsize=8.5,
            color=WHITE, fontweight='bold')
    ax.text(x, y - 0.42, desc,  ha='center', fontsize=6.8,
            color=DIM, linespacing=1.5)

arrow_kw = dict(arrowstyle='->', color=DIM, lw=1.2)
for (x0, y0, x1, y1) in [
    (2.05, 5.6, 2.25, 5.6), (4.15, 5.6, 4.35, 5.6),
    (6.25, 5.6, 6.45, 5.6),
    (3.2,  4.8, 2.6,  3.4), (5.3,  4.8, 5.0,  3.4),
    (7.4,  4.8, 7.8,  3.4),
    (3.15, 2.6, 4.05, 2.6), (5.95, 2.6, 6.85, 2.6),
]:
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=arrow_kw)

ax.text(5.0, 0.55,
        "Outputs:  call_model.pkl   put_model.pkl   "
        "regime_analysis.png   calibration_curve.png   "
        "pnl_curve.png   backtest_trades.csv",
        ha='center', fontsize=7.5, color=DIM, family='monospace')
add(fig, "Layer 2 Pipeline Architecture")


# ─────────────────────────────────────────────────────────────────────────────
# FRAMES 2-17 — Walk-forward windows (one per quarter)
# ─────────────────────────────────────────────────────────────────────────────
print(f"Rendering {n_q} walk-forward window frames ...")
n_window_frames = 0

for qi, q in enumerate(quarters):
    q_df = df[df["quarter"] == q]
    if len(q_df) == 0:
        continue
    n_window_frames += 1

    fig = plt.figure(figsize=(FW, FH), facecolor=BG)
    gs  = GridSpec(2, 3, figure=fig, hspace=0.44, wspace=0.32,
                   left=0.06, right=0.98, top=0.91, bottom=0.09)

    fig.suptitle(
        f"Walk-Forward Window {qi+1}/{n_q}: {q}  "
        f"({q_df['date'].min().date()} → {q_df['date'].max().date()})",
        color=WHITE, fontsize=11, fontweight='bold', y=0.97)

    # ── Left (spans both rows): cumulative P&L with window highlighted
    ax_t = fig.add_subplot(gs[:, :2])
    dark_ax(ax_t, "Cumulative P&L — Walk-Forward All Windows",
            "Date", "P&L ($)")
    ax_t.plot(daily_cum["date"], daily_cum["cum_pnl"],
              color=BLUE, lw=1.3, zorder=3)
    ax_t.fill_between(daily_cum["date"], daily_cum["cum_pnl"], 0,
                      where=(daily_cum["cum_pnl"] >= 0),
                      color=GREEN, alpha=0.18, zorder=1)
    ax_t.fill_between(daily_cum["date"], daily_cum["cum_pnl"], 0,
                      where=(daily_cum["cum_pnl"] < 0),
                      color=RED, alpha=0.18, zorder=1)
    w0, w1 = q_df["date"].min(), q_df["date"].max()
    ax_t.axvspan(w0, w1, color=AMBER, alpha=0.12, zorder=2)
    ax_t.axvline(w0, color=AMBER, lw=0.9, ls='--', zorder=4)
    ax_t.axvline(w1, color=AMBER, lw=0.9, ls='--', zorder=4)
    ax_t.axhline(0, color=DIM, lw=0.7)
    ax_t.tick_params(axis='x', labelrotation=30)

    # ── Top-right: trade P&L distribution for this window
    ax_d = fig.add_subplot(gs[0, 2])
    dom_regime = "herding" if (q_df["regime"] == "herding").mean() > 0.3 \
                 else "normal"
    bar_col = HC if dom_regime == "herding" else NC
    lo = q_df["trade_pnl"].quantile(0.02)
    hi = q_df["trade_pnl"].quantile(0.98)
    dark_ax(ax_d, f"Trade P&L  (n={len(q_df):,})", "P&L ($)", "Count")
    ax_d.hist(q_df["trade_pnl"].clip(lo, hi),
              bins=30, color=bar_col, alpha=0.85, ec=BORDER)
    ax_d.axvline(0, color=WHITE, lw=0.8)
    mean_v = q_df["trade_pnl"].mean()
    ax_d.axvline(mean_v, color=AMBER, lw=1.2, ls='--',
                 label=f"Mean ${mean_v:.1f}")
    ax_d.legend(fontsize=7, labelcolor=DIM,
                facecolor=PANEL, edgecolor=BORDER)

    # ── Bottom-right: window stats table
    ax_s = fig.add_subplot(gs[1, 2])
    ax_s.set_facecolor(PANEL)
    ax_s.set_xticks([]); ax_s.set_yticks([])
    for sp in ax_s.spines.values(): sp.set_color(BORDER)

    n_norm  = int((q_df["regime"] == "normal").sum())
    n_herd  = int((q_df["regime"] == "herding").sum())
    w_pnl   = q_df["trade_pnl"].sum()
    hit     = (q_df["trade_pnl"] > 0).mean()
    brier   = q_df["brier_window"].mean()

    rows = [
        ("Window P&L", f"${w_pnl:+,.0f}", GREEN if w_pnl >= 0 else RED),
        ("Hit Rate",   f"{hit:.1%}",       WHITE),
        ("Avg Brier",  f"{brier:.4f}",     TEAL),
        ("Normal",     f"{n_norm:,}",      NC),
        ("Herding",    f"{n_herd:,}",      HC),
        ("Trades",     f"{len(q_df):,}",   DIM),
    ]
    for si, (lbl, val, col) in enumerate(rows):
        y_s = 0.88 - si * 0.148
        ax_s.text(0.07, y_s, lbl + ":", transform=ax_s.transAxes,
                  fontsize=8, color=DIM, va='top')
        ax_s.text(0.93, y_s, val, transform=ax_s.transAxes,
                  fontsize=9.5, color=col, fontweight='bold',
                  va='top', ha='right')

    add(fig, f"Window {qi+1}/{n_q}: {q}")

REGIME_IDX = 2 + n_window_frames


# ─────────────────────────────────────────────────────────────────────────────
# FRAME — Regime comparison
# ─────────────────────────────────────────────────────────────────────────────
print("Rendering regime comparison ...")
norm_df = df[df["regime"] == "normal"]
herd_df = df[df["regime"] == "herding"]

fig = plt.figure(figsize=(FW, FH), facecolor=BG)
gs  = GridSpec(2, 3, figure=fig, hspace=0.44, wspace=0.32,
               left=0.06, right=0.98, top=0.91, bottom=0.09)
fig.suptitle("Regime Comparison: Normal vs Herding",
             color=WHITE, fontsize=12, fontweight='bold', y=0.97)

for ci, (rdf, rlabel, rcol) in enumerate([
        (norm_df, "Normal Regime", NC),
        (herd_df, "Herding Regime", HC)]):
    lo = rdf["trade_pnl"].quantile(0.02)
    hi = rdf["trade_pnl"].quantile(0.98)

    ax_d = fig.add_subplot(gs[0, ci])
    dark_ax(ax_d,
            f"{rlabel}  (n={len(rdf):,})",
            "Trade P&L ($)", "Count")
    ax_d.hist(rdf["trade_pnl"].clip(lo, hi),
              bins=40, color=rcol, alpha=0.85, ec=BORDER)
    ax_d.axvline(0, color=WHITE, lw=0.8)
    ax_d.axvline(rdf["trade_pnl"].mean(), color=AMBER, lw=1.2, ls='--',
                 label=f"Mean ${rdf['trade_pnl'].mean():.2f}")
    ax_d.legend(fontsize=7, labelcolor=DIM,
                facecolor=PANEL, edgecolor=BORDER)

    r_cum = rdf.sort_values("date").copy()
    r_cum["cum"] = r_cum["trade_pnl"].cumsum()

    ax_c = fig.add_subplot(gs[1, ci])
    dark_ax(ax_c, f"{rlabel} Cumulative P&L", "Date", "P&L ($)")
    ax_c.plot(r_cum["date"], r_cum["cum"], color=rcol, lw=1.2)
    ax_c.fill_between(r_cum["date"], r_cum["cum"], 0,
                      where=(r_cum["cum"] >= 0),
                      color=GREEN, alpha=0.2)
    ax_c.fill_between(r_cum["date"], r_cum["cum"], 0,
                      where=(r_cum["cum"] < 0),
                      color=RED, alpha=0.2)
    ax_c.axhline(0, color=DIM, lw=0.7)
    ax_c.tick_params(axis='x', labelrotation=30)

# Summary column
ax_s = fig.add_subplot(gs[:, 2])
ax_s.set_facecolor(PANEL)
ax_s.set_xticks([]); ax_s.set_yticks([])
for sp in ax_s.spines.values(): sp.set_color(BORDER)
ax_s.set_title("Side-by-Side", color=WHITE, fontsize=10, pad=6)

rows = [
    ("Trades",      f"{len(norm_df):,}",
                    f"{len(herd_df):,}"),
    ("Hit Rate",    f"{(norm_df['trade_pnl']>0).mean():.1%}",
                    f"{(herd_df['trade_pnl']>0).mean():.1%}"),
    ("Mean P&L",    f"${norm_df['trade_pnl'].mean():.2f}",
                    f"${herd_df['trade_pnl'].mean():.2f}"),
    ("Total P&L",   f"${norm_df['trade_pnl'].sum():,.0f}",
                    f"${herd_df['trade_pnl'].sum():,.0f}"),
    ("Sharpe",      f"{sharpe(norm_df['trade_pnl']):.3f}",
                    f"{sharpe(herd_df['trade_pnl']):.3f}"),
    ("Max DD",      f"${max_dd(norm_df['trade_pnl'].cumsum()):,.0f}",
                    f"${max_dd(herd_df['trade_pnl'].cumsum()):,.0f}"),
    ("Avg Brier",   f"{norm_df['brier_window'].mean():.4f}",
                    f"{herd_df['brier_window'].mean():.4f}"),
    ("% of total",  f"{len(norm_df)/len(df):.1%}",
                    f"{len(herd_df)/len(df):.1%}"),
]
y = 0.93
ax_s.text(0.36, y + 0.03, "Normal", ha='center', va='top',
          color=NC, fontsize=9, fontweight='bold',
          transform=ax_s.transAxes)
ax_s.text(0.76, y + 0.03, "Herding", ha='center', va='top',
          color=HC, fontsize=9, fontweight='bold',
          transform=ax_s.transAxes)
for lbl, nv, hv in rows:
    y -= 0.105
    ax_s.text(0.05, y, lbl, ha='left', va='top',
              color=DIM, fontsize=8, transform=ax_s.transAxes)
    ax_s.text(0.36, y, nv, ha='center', va='top',
              color=NC, fontsize=8.5, fontweight='bold',
              transform=ax_s.transAxes)
    ax_s.text(0.76, y, hv, ha='center', va='top',
              color=HC, fontsize=8.5, fontweight='bold',
              transform=ax_s.transAxes)

add(fig, "Regime Comparison: Normal vs Herding")
CALIB_IDX = REGIME_IDX + 1


# ─────────────────────────────────────────────────────────────────────────────
# FRAME — Probability calibration (from trade records)
# ─────────────────────────────────────────────────────────────────────────────
print("Rendering calibration frame ...")

def reliability(tdf, opt_type):
    sub = tdf[tdf["option_type"] == opt_type].dropna(
        subset=["p_independent", "outcome"])
    bins = np.linspace(0, 1, 11)
    mp, fp, cnt = [], [], []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (sub["p_independent"] >= lo) & (sub["p_independent"] < hi)
        if mask.sum() < 10:
            continue
        mp.append(sub.loc[mask, "p_independent"].mean())
        fp.append(sub.loc[mask, "outcome"].mean())
        cnt.append(int(mask.sum()))
    bs  = ((sub["p_independent"] - sub["outcome"]) ** 2).mean()
    ece = sum(c / len(sub) * abs(p - f)
              for p, f, c in zip(mp, fp, cnt))
    return np.array(mp), np.array(fp), np.array(cnt), bs, ece

fig = plt.figure(figsize=(FW, FH), facecolor=BG)
gs  = GridSpec(1, 2, figure=fig, wspace=0.32,
               left=0.07, right=0.97, top=0.88, bottom=0.11)
fig.suptitle(
    "Probability Calibration — p_independent vs Actual ITM Rate\n"
    "(Computed from backtest trade records)",
    color=WHITE, fontsize=12, fontweight='bold', y=0.97)

for ci, (opt, col) in enumerate([("call", BLUE), ("put", PURPLE)]):
    mp, fp, cnt, bs, ece = reliability(df, opt)
    ax = fig.add_subplot(gs[0, ci])
    dark_ax(ax,
            f"{opt.capitalize()} Calibration\n"
            f"Brier={bs:.4f}  ECE={ece:.4f}  "
            f"(naive baseline Brier=0.25)",
            "Mean Predicted Probability",
            "Actual ITM Rate")
    ax.plot([0, 1], [0, 1], color=DIM, lw=1, ls='--',
            label="Perfect calibration")
    ax.bar(mp, fp, width=0.08, alpha=0.40, color=col,
           label="Actual ITM rate")
    ax.plot(mp, fp, 'o-', color=col, lw=1.5, ms=5,
            label=f"Model  Brier={bs:.4f}")
    # Bubble size ~ sample count
    ax.scatter(mp, fp, s=[c / 30 for c in cnt],
               color=col, alpha=0.3, zorder=5)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.legend(fontsize=8, labelcolor=WHITE,
              facecolor=PANEL, edgecolor=BORDER)

add(fig, "Probability Calibration")
BRIER_IDX = CALIB_IDX + 1


# ─────────────────────────────────────────────────────────────────────────────
# FRAME — Brier score trend over quarters
# ─────────────────────────────────────────────────────────────────────────────
print("Rendering Brier score trend ...")

fig = plt.figure(figsize=(FW, FH), facecolor=BG)
gs  = GridSpec(1, 2, figure=fig, wspace=0.32,
               left=0.07, right=0.97, top=0.88, bottom=0.14)
fig.suptitle("Brier Score Trend Over Backtest Windows",
             color=WHITE, fontsize=12, fontweight='bold', y=0.97)

for ci, (opt, col, odf) in enumerate([
        ("put",  PURPLE, put_df),
        ("call", BLUE,   call_df)]):
    bq = odf.groupby("quarter")["brier_window"].mean()
    xs = list(range(len(bq)))
    ax = fig.add_subplot(gs[0, ci])
    dark_ax(ax,
            f"{opt.capitalize()} Model Brier by Quarter",
            "Quarter", "Brier Score (lower = better)")
    ax.plot(xs, bq.values, color=col, lw=1.5, marker='o', ms=4)
    ax.fill_between(xs, bq.values, 0.25,
                    where=(bq.values < 0.25),
                    color=GREEN, alpha=0.15,
                    label="Better than naive")
    ax.axhline(0.25, color=RED, lw=1, ls='--',
               label="Naive baseline (0.25)")
    ax.axhline(bq.mean(), color=AMBER, lw=1, ls=':',
               label=f"Overall mean {bq.mean():.4f}")
    ax.set_xticks(xs)
    ax.set_xticklabels([str(q) for q in bq.index],
                       rotation=45, ha='right', fontsize=6.5)
    ax.set_ylim(0, 0.28)
    ax.legend(fontsize=8, labelcolor=WHITE,
              facecolor=PANEL, edgecolor=BORDER)

add(fig, "Brier Score Trend Over Time")
PNL_IDX = BRIER_IDX + 1


# ─────────────────────────────────────────────────────────────────────────────
# FRAME — Full P&L summary
# ─────────────────────────────────────────────────────────────────────────────
print("Rendering full P&L summary ...")

# Quarterly net P&L bar chart
q_pnl = df.groupby("quarter")["trade_pnl"].sum()

fig = plt.figure(figsize=(FW, FH), facecolor=BG)
gs  = GridSpec(2, 3, figure=fig, hspace=0.44, wspace=0.32,
               left=0.06, right=0.98, top=0.91, bottom=0.09)
fig.suptitle("Full Walk-Forward Backtest P&L Summary",
             color=WHITE, fontsize=12, fontweight='bold', y=0.97)

# Top row: full cumulative P&L (spans all 3 cols)
ax1 = fig.add_subplot(gs[0, :])
dark_ax(ax1, "Cumulative P&L (All Trades)", "Date", "P&L ($)")
ax1.plot(daily_cum["date"], daily_cum["cum_pnl"], color=BLUE, lw=1.5)
ax1.fill_between(daily_cum["date"], daily_cum["cum_pnl"], 0,
                 where=(daily_cum["cum_pnl"] >= 0),
                 color=GREEN, alpha=0.22)
ax1.fill_between(daily_cum["date"], daily_cum["cum_pnl"], 0,
                 where=(daily_cum["cum_pnl"] < 0),
                 color=RED, alpha=0.22)
ax1.axhline(0, color=DIM, lw=0.7)
ax1.tick_params(axis='x', labelrotation=30)

# Bottom-left: quarterly P&L bars
ax2 = fig.add_subplot(gs[1, 0])
dark_ax(ax2, "Quarterly Net P&L", "Quarter", "P&L ($)")
colors_q = [GREEN if v >= 0 else RED for v in q_pnl.values]
xs = range(len(q_pnl))
ax2.bar(xs, q_pnl.values, color=colors_q, alpha=0.85, ec=BORDER)
ax2.axhline(0, color=DIM, lw=0.7)
ax2.set_xticks(list(xs))
ax2.set_xticklabels([str(q) for q in q_pnl.index],
                    rotation=45, ha='right', fontsize=5.5)

# Bottom-middle: put P&L distribution
ax3 = fig.add_subplot(gs[1, 1])
dark_ax(ax3, f"Put P&L Distribution (n={len(put_df):,})",
        "P&L ($)", "Count")
lo = put_df["trade_pnl"].quantile(0.01)
hi = put_df["trade_pnl"].quantile(0.99)
ax3.hist(put_df["trade_pnl"].clip(lo, hi),
         bins=50, color=PURPLE, alpha=0.85, ec=BORDER)
ax3.axvline(0, color=WHITE, lw=0.8)
ax3.axvline(put_df["trade_pnl"].mean(), color=AMBER, lw=1.2, ls='--',
            label=f"Mean ${put_df['trade_pnl'].mean():.2f}")
ax3.legend(fontsize=7, labelcolor=DIM,
           facecolor=PANEL, edgecolor=BORDER)

# Bottom-right: edge distribution (p_independent - q_market)
ax4 = fig.add_subplot(gs[1, 2])
dark_ax(ax4, "Net Edge Distribution at Trade Entry",
        "net_edge", "Count")
ax4.hist(df["net_edge"].clip(
             df["net_edge"].quantile(0.01),
             df["net_edge"].quantile(0.99)),
         bins=50, color=TEAL, alpha=0.85, ec=BORDER)
ax4.axvline(0, color=WHITE, lw=0.8)
ax4.axvline(df["net_edge"].mean(), color=AMBER, lw=1.2, ls='--',
            label=f"Mean {df['net_edge'].mean():.3f}")
ax4.legend(fontsize=7, labelcolor=DIM,
           facecolor=PANEL, edgecolor=BORDER)

add(fig, "Full P&L Summary")
METRICS_IDX = PNL_IDX + 1


# ─────────────────────────────────────────────────────────────────────────────
# FRAME — Summary metrics table
# ─────────────────────────────────────────────────────────────────────────────
print("Rendering summary metrics table ...")

fig = plt.figure(figsize=(FW, FH), facecolor=BG)
ax  = fig.add_axes([0, 0, 1, 1], facecolor=BG)
ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_visible(False)
fig.text(0.5, 0.94, "Backtest Summary Metrics",
         ha='center', color=WHITE, fontsize=14, fontweight='bold')

rows = [
    ("Metric",
     "Put Options",
     "Call Options",
     "Notes"),
    ("N Trades",
     f"{len(put_df):,}",
     f"{len(call_df):,}",
     "Total trades executed"),
    ("Hit Rate",
     f"{(put_df['trade_pnl']>0).mean():.1%}",
     f"{(call_df['trade_pnl']>0).mean():.1%}",
     "% trades profitable"),
    ("Total P&L",
     f"${put_df['trade_pnl'].sum():,.0f}",
     f"${call_df['trade_pnl'].sum():,.0f}",
     "Cumulative P&L"),
    ("Sharpe Ratio",
     f"{sharpe(put_df['trade_pnl']):.3f}",
     f"{sharpe(call_df['trade_pnl']):.3f}",
     "Annualized (> 1.0 = good)"),
    ("Max Drawdown",
     f"${max_dd(put_df['cumulative_pnl']):,.0f}",
     f"${max_dd(call_df['cumulative_pnl']):,.0f}",
     "Peak-to-trough loss"),
    ("Avg Brier",
     f"{put_df['brier_window'].mean():.4f}",
     f"{call_df['brier_window'].mean():.4f}",
     "< 0.25 beats naive baseline"),
    ("Normal Regime",
     f"{(put_df['regime']=='normal').mean():.1%}",
     f"{(call_df['regime']=='normal').mean():.1%}",
     "Trades in normal market"),
    ("Herding Regime",
     f"{(put_df['regime']=='herding').mean():.1%}",
     f"{(call_df['regime']=='herding').mean():.1%}",
     "Trades in herding market"),
    ("Quarters tested",
     f"{put_df['quarter'].nunique()}",
     f"{call_df['quarter'].nunique()}",
     "2017 Q1 → 2020 Q4"),
]

col_x = [0.03, 0.30, 0.50, 0.68]
row_h = 0.072
y0    = 0.87

for ri, row in enumerate(rows):
    y  = y0 - ri * row_h
    bg = '#1c2333' if ri == 0 else ('#161b22' if ri % 2 == 0 else BG)
    r  = mpatches.FancyBboxPatch(
        (0.02, y - 0.048), 0.96, row_h - 0.004,
        boxstyle="square,pad=0", fc=bg, ec=BORDER, lw=0.5,
        transform=ax.transAxes)
    ax.add_patch(r)
    txt_colors = ([DIM, PURPLE, BLUE, DIM]
                  if ri > 0 else [WHITE] * 4)
    weights    = (['normal'] * 4 if ri > 0 else ['bold'] * 4)
    for ci, (txt, tc, cx) in enumerate(
            zip(row, txt_colors, col_x)):
        ax.text(cx + [0.26, 0.18, 0.16, 0.28][ci] / 2,
                y - 0.004, txt,
                ha='center', va='top',
                fontsize=9 if ri > 0 else 8.5,
                color=tc, fontweight=weights[ci],
                transform=ax.transAxes)

fig.text(0.5, 0.045,
         "Quarter-Kelly sizing  |  15% drawdown circuit breaker  |  "
         "2% normal / 8% herding min edge  |  $100K capital",
         ha='center', color=DIM, fontsize=8)
add(fig, "Backtest Summary Metrics")

print(f"\nTotal frames: {len(frames)}")


# ─────────────────────────────────────────────────────────────────────────────
# Build HTML player
# ─────────────────────────────────────────────────────────────────────────────
print("Building HTML ...")
TOTAL = len(frames)
f_js  = '[' + ','.join(f'"{f}"'  for f, _ in frames) + ']'
d_js  = '[' + ','.join(f'"{d}"'  for _, d in frames) + ']'

# Section jump indices
sections = [
    ("&#9679; Intro",         0),
    ("&#9660; Architecture",  1),
    ("&#9632; Walk-Forward",  2),
    ("&#9650; Regime",        REGIME_IDX),
    ("&#9670; Calibration",   CALIB_IDX),
    ("&#9654; Brier Trend",   BRIER_IDX),
    ("&#9733; P&L Summary",   PNL_IDX),
    ("&#9632; Metrics",       METRICS_IDX),
]
nav_btns = "\n    ".join(
    f'<button class="sec-btn" onclick="goTo({idx})">{lbl}</button>'
    for lbl, idx in sections
)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Deep Scholar -- Layer 2 Backtest Dashboard</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    background: #0d1117;
    margin: 0;
    font-family: monospace;
    color: #94a3b8;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px 10px;
  }}
  h1 {{
    color: #f1f5f9;
    font-size: 16px;
    margin: 0 0 8px;
    letter-spacing: 0.5px;
    text-align: center;
  }}
  #player {{
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 12px 14px;
    max-width: 1100px;
    width: 100%;
  }}
  #player img {{
    width: 100%;
    border-radius: 6px;
    display: block;
  }}
  #desc {{
    font-size: 11px;
    margin: 6px 0 3px;
    color: #94a3b8;
    letter-spacing: 0.3px;
  }}
  #section-nav {{
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
    margin: 7px 0 4px;
  }}
  .sec-btn {{
    background: #161b22;
    color: #94a3b8;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 4px 10px;
    cursor: pointer;
    font-size: 11px;
    font-family: monospace;
  }}
  .sec-btn:hover {{ background: #1c2333; color: #f1f5f9; }}
  #controls {{
    display: flex;
    align-items: center;
    gap: 7px;
    margin-top: 7px;
    flex-wrap: wrap;
  }}
  .btn {{
    background: #1c2333;
    color: #f1f5f9;
    border: 1px solid #30363d;
    border-radius: 5px;
    padding: 5px 13px;
    cursor: pointer;
    font-size: 13px;
    font-family: monospace;
  }}
  .btn:hover {{ background: #2563eb; border-color: #3b82f6; }}
  #slider {{
    flex: 1;
    min-width: 180px;
    accent-color: #2563eb;
  }}
  #speed {{ width: 90px; accent-color: #f59e0b; }}
  #speed-label {{ font-size: 11px; min-width: 44px; color: #fbbf24; }}
  #footer {{
    color: #334155;
    font-size: 10px;
    margin-top: 10px;
    text-align: center;
  }}
</style>
</head>
<body>
<h1>Deep Scholar &mdash; Layer 2 Walk-Forward Backtest Dashboard</h1>
<div id="player">
  <div id="desc">Frame 1/{TOTAL} | Introduction</div>
  <img id="img" src="data:image/png;base64,{frames[0][0]}" />
  <div id="section-nav">
    {nav_btns}
  </div>
  <div id="controls">
    <button class="btn" onclick="restart()">&#8676; Restart</button>
    <button class="btn" onclick="stepBack()">&#9664; Step</button>
    <button class="btn" id="play-btn" onclick="toggle()">&#9654; Play</button>
    <button class="btn" onclick="stepFwd()">Step &#9654;</button>
    <input type="range" id="slider" min="0" max="{TOTAL-1}"
           value="0" oninput="seek(this.value)" />
    <span style="font-size:11px;color:#64748b;">Speed:</span>
    <input type="range" id="speed" min="500" max="5000" step="250"
           value="2000" oninput="setSpeed(this.value)" />
    <span id="speed-label">Normal</span>
  </div>
</div>
<div id="footer">
  CS495 Deep Scholar &nbsp;|&nbsp; DeWayne Dantzler &nbsp;|&nbsp;
  Bellevue College Spring 2026 &nbsp;|&nbsp;
  github.com/dantzlerdc/CS495-Deep-Scholar
</div>

<script>
(function() {{
  const frames = {f_js};
  const descs  = {d_js};
  let cur = 0, timer = null, interval = 2000;

  function show(i) {{
    cur = Math.max(0, Math.min(i, frames.length - 1));
    document.getElementById('img').src =
      'data:image/png;base64,' + frames[cur];
    document.getElementById('desc').innerText =
      'Frame ' + (cur + 1) + '/{TOTAL}  |  ' + descs[cur];
    document.getElementById('slider').value = cur;
  }}

  function tick() {{ show((cur + 1) % frames.length); }}

  window.toggle = function() {{
    const btn = document.getElementById('play-btn');
    if (timer) {{
      clearInterval(timer); timer = null;
      btn.innerHTML = '&#9654; Play';
    }} else {{
      timer = setInterval(tick, interval);
      btn.innerHTML = '&#9646;&#9646; Pause';
    }}
  }};
  window.restart  = () => show(0);
  window.stepBack = () => show(cur - 1);
  window.stepFwd  = () => show(cur + 1);
  window.seek     = v  => show(parseInt(v));
  window.goTo     = i  => show(i);
  window.setSpeed = v  => {{
    interval = parseInt(v);
    const lbl = document.getElementById('speed-label');
    lbl.innerText = interval <= 750 ? 'Fast'
                  : interval <= 2500 ? 'Normal' : 'Slow';
    if (timer) {{ clearInterval(timer); timer = setInterval(tick, interval); }}
  }};
}})();
</script>
</body>
</html>"""

with open(OUT_HTML, "w") as fh:
    fh.write(html)
print(f"Saved -> {OUT_HTML}")
