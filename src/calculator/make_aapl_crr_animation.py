"""
make_aapl_crr_animation.py -- Animated CRR Binomial Tree on Real AAPL Contracts (PLAN2.md)

Selects two real AAPL contracts from the cross-model comparison:
  Contract A: herding regime, both L1 and L2 say market overprices
  Contract B: normal regime, both models say pricing is fair

For each contract, animates 5 phases:
  Phase 0: Contract profile
  Phase 1: Stock price lattice (forward pass)
  Phase 2: Terminal payoffs
  Phase 3: Backward induction (option values propagating back)
  Phase 4: Result -- V_model_rv vs V_market + L2 signal

The right-side info panel shows both Layer 1 and Layer 2 signals on every frame.

Output: aapl_crr_comparison.html
"""

import os
import sys
import base64
import io
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.gridspec import GridSpec
from matplotlib.font_manager import FontProperties

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "project"))
from market_data import load_prepared, CALL_FEATURES, PUT_FEATURES
from tree import price_american_option
from p_estimator import load as load_model, predict_p
from bias_detector import compute_atm_iv, compute_regime

R       = 0.02
N_PRICE = 50    # steps for actual pricing
N_VIZ   = 5    # steps for visualization tree (readable on screen)
OUT     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "dist", "interactive", "aapl_crr_comparison.html")


# ── CRR helpers ───────────────────────────────────────────────────────────────

def crr_full(S, K, sigma, T, option_type, N):
    """Return (price, S_lattice, V_lattice) for the visualization tree."""
    dt       = T / N
    u        = math.exp(sigma * math.sqrt(dt))
    d        = 1.0 / u
    p        = (math.exp(R * dt) - d) / (u - d)
    discount = math.exp(-R * dt)

    # Stock lattice: S_lat[i][j] = stock at step i, down-move j
    S_lat = [[S * (u ** (i - j)) * (d ** j) for j in range(i + 1)]
             for i in range(N + 1)]

    # Terminal payoffs
    if option_type == "call":
        V_terminal = [max(s - K, 0.0) for s in S_lat[N]]
    else:
        V_terminal = [max(K - s, 0.0) for s in S_lat[N]]

    V_lat = [None] * (N + 1)
    V_lat[N] = V_terminal[:]

    for i in range(N - 1, -1, -1):
        V_i = []
        for j in range(i + 1):
            cont    = discount * (p * V_lat[i + 1][j] + (1 - p) * V_lat[i + 1][j + 1])
            s_node  = S_lat[i][j]
            payoff  = max(s_node - K, 0.0) if option_type == "call" else max(K - s_node, 0.0)
            V_i.append(max(cont, payoff))
        V_lat[i] = V_i

    price_50, _ = price_american_option(S, K, R, sigma, T, N_PRICE, option_type)
    return price_50, S_lat, V_lat, u, d, p


def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# ── Contract selection ────────────────────────────────────────────────────────

def select_contracts(df):
    """
    Find one herding/overpriced contract (A) and one normal/fair contract (B).
    Both models are run on the same dataset used in layer1_vs_layer2.py.
    """
    print("  Building regime map ...")
    daily      = compute_atm_iv(df)
    daily_reg  = compute_regime(daily)
    regime_map = daily_reg.set_index("QUOTE_DATE")["regime"].to_dict()

    # Load Layer 2 models
    call_bundle = load_model("call")
    put_bundle  = load_model("put")

    # Filter valid put contracts (puts tend to show stronger vol premium for AAPL)
    mask = (
        (df["P_BID"] > 0) & (df["P_ASK"] > 0) &
        (df["P_IV"]  > 0.01) & (df["RV30"] > 0.01) &
        (df["DTE"]   >= 10)  & (df["DTE"]  <= 90) &
        (df["UNDERLYING_LAST"] > 0) & (df["STRIKE"] > 0)
    )
    pool = df[mask].copy()
    pool["regime"]  = pool["QUOTE_DATE"].map(regime_map).fillna("unknown")
    pool["V_market"] = (pool["P_BID"] + pool["P_ASK"]) / 2.0
    pool["T_years"]  = pool["DTE"] / 365.0

    # Moneyness filter: near-ATM
    pool["moneyness_abs"] = (pool["moneyness"] - 1.0).abs()
    pool = pool[(pool["moneyness"] >= 0.90) & (pool["moneyness"] <= 1.10)]
    pool = pool[pool["V_market"] > 0.50]

    # Layer 1 edge (CRR with RV30)
    print(f"  Computing CRR edges for {len(pool):,} candidates ...")
    pool = pool.sample(min(3000, len(pool)), random_state=7).copy()

    l1_edges = []
    for _, row in pool.iterrows():
        try:
            price, _ = price_american_option(
                row.UNDERLYING_LAST, row.STRIKE, R, row.RV30,
                row.T_years, N_PRICE, "put"
            )
            edge = (price - row.V_market) / row.V_market
        except Exception:
            edge = np.nan
        l1_edges.append(edge)

    pool["edge_L1"] = l1_edges
    pool = pool.dropna(subset=["edge_L1"])

    # Layer 2 edge
    feats       = PUT_FEATURES
    valid       = pool.dropna(subset=feats)
    X_raw       = valid[feats].values
    p_ind       = predict_p(put_bundle, X_raw)
    P_mid       = (valid["P_BID"] + valid["P_ASK"]) / 2.0
    q_market    = (P_mid / valid["STRIKE"]).clip(0, 1)
    valid       = valid.copy()
    valid["edge_L2"]        = p_ind - q_market.values
    valid["p_independent"]  = p_ind
    valid["q_market"]       = q_market.values
    pool = valid.copy()

    # Contract A: herding, both signals strongly negative
    crit_A = (
        (pool["regime"]  == "herding") &
        (pool["edge_L1"] < -0.10) &
        (pool["edge_L2"] < -0.02)
    )
    cands_A = pool[crit_A].copy()
    if len(cands_A) == 0:
        print("  Relaxing Contract A criteria ...")
        crit_A = (pool["edge_L1"] < -0.10) & (pool["edge_L2"] < -0.01)
        cands_A = pool[crit_A].copy()
    cands_A["score"] = cands_A["edge_L1"].abs() + cands_A["edge_L2"].abs() * 5
    contract_A = cands_A.nlargest(1, "score").iloc[0]

    # Contract B: normal, both signals near zero
    crit_B = (
        (pool["regime"]  == "normal") &
        (pool["edge_L1"].abs() < 0.08) &
        (pool["edge_L2"].abs() < 0.04)
    )
    cands_B = pool[crit_B].copy()
    if len(cands_B) == 0:
        print("  Relaxing Contract B criteria ...")
        cands_B = pool[(pool["edge_L1"].abs() < 0.12) & (pool["edge_L2"].abs() < 0.06)].copy()
    cands_B["score"] = -(cands_B["edge_L1"].abs() + cands_B["edge_L2"].abs())
    contract_B = cands_B.nlargest(1, "score").iloc[0]

    print(f"\n  Contract A: {contract_A.QUOTE_DATE}  K={contract_A.STRIKE:.0f}  "
          f"DTE={contract_A.DTE:.0f}  regime={contract_A.regime}")
    print(f"    edge_L1={contract_A.edge_L1:.4f}  edge_L2={contract_A.edge_L2:.4f}")
    print(f"  Contract B: {contract_B.QUOTE_DATE}  K={contract_B.STRIKE:.0f}  "
          f"DTE={contract_B.DTE:.0f}  regime={contract_B.regime}")
    print(f"    edge_L1={contract_B.edge_L1:.4f}  edge_L2={contract_B.edge_L2:.4f}")

    return contract_A, contract_B


# ── Frame renderers ───────────────────────────────────────────────────────────

COLORS = {
    "herding": "#DC2626", "normal": "#2563EB",
    "L1":      "#047857", "L2":     "#7C3AED",
    "up":      "#059669", "down":   "#DC2626",
    "itm":     "#D1FAE5", "otm":    "#FEE2E2",
    "bg":      "#F8FAFC",
}


def _info_panel(ax, contract, phase_label, price_rv=None):
    """Draw the right-side info panel onto ax."""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("#F8FAFC")

    regime = contract.get("regime", "?")
    reg_col = "#166534" if regime == "herding" else COLORS.get(regime, "#0D1F3C")

    def row(y, label, val, col="#0F172A", bold=False):
        ax.text(0.05, y, label, transform=ax.transAxes, fontsize=7.5,
                color="#0D1F3C", va="top", fontfamily="monospace")
        ax.text(0.95, y, val, transform=ax.transAxes, fontsize=7.5,
                color=col, va="top", ha="right",
                fontfamily="monospace",
                fontweight="bold" if bold else "normal")

    y = 0.97
    ax.text(0.5, y, "Contract Info", transform=ax.transAxes, fontsize=9,
            color="#166534", ha="center", va="top", fontweight="bold")
    y -= 0.07

    row(y, "Phase",    phase_label,                         bold=True); y -= 0.06
    row(y, "Type",     "PUT");                                           y -= 0.055
    row(y, "Date",     str(contract.get("QUOTE_DATE", "?"))[:10]); y -= 0.055
    row(y, "S",        f"${contract.UNDERLYING_LAST:.2f}");  y -= 0.055
    row(y, "K",        f"${contract.STRIKE:.2f}");           y -= 0.055
    row(y, "DTE",      f"{contract.DTE:.0f} days");          y -= 0.055
    row(y, "T",        f"{contract.T_years:.4f} yr");        y -= 0.055
    row(y, "RV30",     f"{contract.RV30:.4f}");              y -= 0.055
    row(y, "P_IV",     f"{contract.P_IV:.4f}");              y -= 0.055
    row(y, "V_market", f"${contract.V_market:.3f}");         y -= 0.055

    ax.axhline(y + 0.02, color="#94A3B8", lw=0.8, xmin=0.02, xmax=0.98)
    y -= 0.03

    edge_L1 = contract.edge_L1
    edge_L2 = contract.edge_L2

    # Layer 1
    ax.text(0.5, y, "Layer 1 — CRR", transform=ax.transAxes, fontsize=8,
            color=COLORS["L1"], ha="center", va="top", fontweight="bold"); y -= 0.065
    if price_rv is not None:
        row(y, "V_model_rv", f"${price_rv:.3f}", col=COLORS["L1"]); y -= 0.055
        col_e   = "#DC2626" if edge_L1 < 0 else "#059669"
        row(y, "edge_L1",   f"{edge_L1:+.4f}", col=col_e, bold=True); y -= 0.055
    else:
        row(y, "V_model_rv", "computing...", col="#6B7280"); y -= 0.055
        row(y, "edge_L1",    "—",            col="#6B7280"); y -= 0.055

    ax.axhline(y + 0.02, color="#94A3B8", lw=0.8, xmin=0.02, xmax=0.98)
    y -= 0.03

    # Layer 2
    ax.text(0.5, y, "Layer 2 — XGBoost", transform=ax.transAxes, fontsize=8,
            color=COLORS["L2"], ha="center", va="top", fontweight="bold"); y -= 0.065
    row(y, "p_indep",  f"{contract.p_independent:.4f}", col=COLORS["L2"]); y -= 0.055
    row(y, "q_market", f"{contract.q_market:.4f}");                         y -= 0.055
    col_e2  = "#DC2626" if edge_L2 < 0 else "#059669"
    row(y, "edge_L2",  f"{edge_L2:+.4f}", col=col_e2, bold=True); y -= 0.055

    ax.axhline(y + 0.02, color="#94A3B8", lw=0.8, xmin=0.02, xmax=0.98)
    y -= 0.03

    # Regime badge
    ax.text(0.5, y, f"Regime: {regime.upper()}", transform=ax.transAxes,
            fontsize=9, color=reg_col, ha="center", va="top", fontweight="bold")

    # Signal agreement
    y -= 0.08
    both_neg = edge_L1 < 0 and edge_L2 < 0
    both_pos = edge_L1 > 0 and edge_L2 > 0
    if both_neg:
        sig_text, sig_col = "BOTH: SELL SIGNAL", "#166534"
    elif both_pos:
        sig_text, sig_col = "BOTH: BUY SIGNAL",  "#059669"
    else:
        sig_text, sig_col = "MIXED SIGNAL",       "#F59E0B"
    ax.text(0.5, y, sig_text, transform=ax.transAxes, fontsize=8.5,
            color=sig_col, ha="center", va="top", fontweight="bold")


def render_phase0(contract, contract_label):
    """Intro frame: contract parameters table."""
    fig = plt.figure(figsize=(13, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    gs = GridSpec(1, 4, figure=fig, width_ratios=[3, 0.1, 1, 0.05])

    ax_main = fig.add_subplot(gs[0])
    ax_info = fig.add_subplot(gs[2])

    ax_main.set_facecolor(COLORS["bg"])
    ax_main.axis("off")

    color = "#166534" if contract.regime == "herding" else COLORS["normal"]
    regime_lbl = "HERDING REGIME — CROWD OVERPRICES" if contract.regime == "herding" \
        else "NORMAL REGIME — FAIR PRICING"

    ax_main.text(0.5, 0.93,
                 f"Contract {contract_label}  ·  {regime_lbl}",
                 transform=ax_main.transAxes, fontsize=13, fontweight="bold",
                 color=color, ha="center", va="top")
    ax_main.text(0.5, 0.84,
                 "CRR binomial tree will now be built for this real AAPL put option",
                 transform=ax_main.transAxes, fontsize=10, color="#0D1F3C",
                 ha="center", va="top")

    params = [
        ("Quote Date",   str(contract.QUOTE_DATE)[:10]),
        ("Underlying (S)", f"${contract.UNDERLYING_LAST:.2f}"),
        ("Strike (K)",   f"${contract.STRIKE:.2f}"),
        ("DTE",          f"{contract.DTE:.0f} days"),
        ("Time (T)",     f"{contract.T_years:.4f} years"),
        ("RV30 (σ)",     f"{contract.RV30:.4f}  ← used as sigma in CRR"),
        ("IV",           f"{contract.P_IV:.4f}"),
        ("V_market",     f"${contract.V_market:.3f}  (bid-ask mid)"),
        ("Risk-free r",  "2.00%  (constant 2016-2020 avg)"),
        ("CRR steps",    f"{N_PRICE} (pricing) / {N_VIZ} (visualization)"),
    ]
    y0 = 0.73
    for label, val in params:
        ax_main.text(0.12, y0, label + ":", transform=ax_main.transAxes,
                     fontsize=10, color="#1E293B", va="top", fontweight="bold")
        ax_main.text(0.55, y0, val, transform=ax_main.transAxes,
                     fontsize=10, color="#0F172A", va="top")
        y0 -= 0.068

    _info_panel(ax_info, contract, "Phase 0: Profile")
    ax_main.text(0.5, 0.03,
                 "Phase 0 of 4  |  Next: build stock price lattice (forward pass)",
                 transform=ax_main.transAxes, fontsize=8, color="#0D1F3C",
                 ha="center", va="bottom")
    fig.tight_layout()
    return fig_to_b64(fig)


def render_lattice(contract, contract_label, step_reveal):
    """Phase 1: stock lattice being revealed column by column."""
    price_rv, S_lat, V_lat, u, d, p = crr_full(
        contract.UNDERLYING_LAST, contract.STRIKE,
        contract.RV30, contract.T_years, "put", N_VIZ
    )

    fig = plt.figure(figsize=(13, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    gs = GridSpec(1, 4, figure=fig, width_ratios=[3, 0.1, 1, 0.05])
    ax_main = fig.add_subplot(gs[0])
    ax_info = fig.add_subplot(gs[2])
    ax_main.set_facecolor(COLORS["bg"])
    ax_main.axis("off")

    ax_main.set_xlim(-0.5, N_VIZ + 0.5)
    y_min = min(s for col in S_lat for s in col)
    y_max = max(s for col in S_lat for s in col)
    margin = (y_max - y_min) * 0.12
    ax_main.set_ylim(y_min - margin, y_max + margin)
    ax_main.axis("on")
    ax_main.set_facecolor(COLORS["bg"])
    ax_main.set_xlabel("Time step", fontsize=9)
    ax_main.set_ylabel("Stock Price ($)", fontsize=9)
    ax_main.set_title(
        f"Contract {contract_label}  ·  Stock Price Lattice (Forward Pass)\n"
        f"u={u:.4f}  d={d:.4f}  p*={p:.4f}  (N={N_VIZ} steps for visualization)",
        fontsize=10, fontweight="bold", color="#166534" if contract.regime=="herding" else COLORS["normal"]
    )
    ax_main.grid(alpha=0.2)

    for i in range(min(step_reveal + 1, N_VIZ + 1)):
        for j, s in enumerate(S_lat[i]):
            col = COLORS["up"] if j == 0 else COLORS["down"]
            ax_main.plot(i, s, "o", color=col, ms=8, zorder=3)
            ax_main.text(i + 0.08, s, f"${s:.1f}", fontsize=6.5, va="center",
                         color="#1E293B")
            if i > 0 and step_reveal >= i:
                if j > 0:
                    ax_main.plot([i-1, i], [S_lat[i-1][j-1], s], "-",
                                 color=COLORS["down"], lw=0.9, alpha=0.7)
                if j < len(S_lat[i-1]):
                    ax_main.plot([i-1, i], [S_lat[i-1][j], s], "-",
                                 color=COLORS["up"], lw=0.9, alpha=0.7)

    up_patch  = mpatches.Patch(color=COLORS["up"],   label="Up node")
    dn_patch  = mpatches.Patch(color=COLORS["down"],  label="Down node")
    ax_main.legend(handles=[up_patch, dn_patch], fontsize=8, loc="upper right")
    ax_main.set_xticks(range(N_VIZ + 1))

    _info_panel(ax_info, contract, f"Phase 1: Lattice\nstep {step_reveal}/{N_VIZ}")
    fig.tight_layout()
    return fig_to_b64(fig)


def render_payoffs(contract, contract_label):
    """Phase 2: terminal payoffs (ITM nodes highlighted)."""
    price_rv, S_lat, V_lat, u, d, p = crr_full(
        contract.UNDERLYING_LAST, contract.STRIKE,
        contract.RV30, contract.T_years, "put", N_VIZ
    )
    K = contract.STRIKE

    fig = plt.figure(figsize=(13, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    gs = GridSpec(1, 4, figure=fig, width_ratios=[3, 0.1, 1, 0.05])
    ax_main = fig.add_subplot(gs[0])
    ax_info = fig.add_subplot(gs[2])

    y_min = min(s for col in S_lat for s in col)
    y_max = max(s for col in S_lat for s in col)
    margin = (y_max - y_min) * 0.12
    ax_main.set_xlim(-0.5, N_VIZ + 0.5)
    ax_main.set_ylim(y_min - margin, y_max + margin)
    ax_main.set_facecolor(COLORS["bg"])
    ax_main.set_xlabel("Time step", fontsize=9)
    ax_main.set_ylabel("Stock Price ($)", fontsize=9)
    ax_main.set_title(
        f"Contract {contract_label}  ·  Terminal Payoffs  (K=${K:.0f})\n"
        "Green = ITM (early exercise has value)  |  Red = OTM (expires worthless)",
        fontsize=10, fontweight="bold"
    )
    ax_main.grid(alpha=0.2)

    # Draw all lattice edges
    for i in range(1, N_VIZ + 1):
        for j, s in enumerate(S_lat[i]):
            if j > 0:
                ax_main.plot([i-1, i], [S_lat[i-1][j-1], s], "-",
                             color="#94A3B8", lw=0.8, alpha=0.5)
            if j < len(S_lat[i-1]):
                ax_main.plot([i-1, i], [S_lat[i-1][j], s], "-",
                             color="#94A3B8", lw=0.8, alpha=0.5)

    # All interior nodes gray
    for i in range(N_VIZ):
        for s in S_lat[i]:
            ax_main.plot(i, s, "o", color="#CBD5E1", ms=7, zorder=3)

    # Terminal nodes colored by ITM/OTM, labeled with payoff
    for j, s in enumerate(S_lat[N_VIZ]):
        payoff = max(K - s, 0.0)
        itm    = payoff > 0
        col    = COLORS["up"] if itm else COLORS["down"]
        fcc    = COLORS["itm"] if itm else COLORS["otm"]
        ax_main.plot(N_VIZ, s, "s", color=col, ms=12, zorder=4,
                     markerfacecolor=fcc, markeredgewidth=1.5)
        ax_main.text(N_VIZ + 0.12, s,
                     f"S=${s:.1f}\nP=${payoff:.2f}", fontsize=6, va="center")

    # Strike line
    ax_main.axhline(K, color="#F59E0B", lw=1.2, ls="--", alpha=0.8, label=f"Strike K=${K:.0f}")
    ax_main.legend(fontsize=8, loc="upper right")
    ax_main.set_xticks(range(N_VIZ + 1))

    _info_panel(ax_info, contract, "Phase 2: Payoffs")
    fig.tight_layout()
    return fig_to_b64(fig)


def render_backprop(contract, contract_label, step_reveal):
    """Phase 3: backward induction revealing option values from right to left."""
    price_rv, S_lat, V_lat, u, d, p = crr_full(
        contract.UNDERLYING_LAST, contract.STRIKE,
        contract.RV30, contract.T_years, "put", N_VIZ
    )
    K = contract.STRIKE

    y_min  = min(s for col in S_lat for s in col)
    y_max  = max(s for col in S_lat for s in col)
    margin = (y_max - y_min) * 0.12

    # ── Final fully-revealed frame: v11 full-width design ────────────────────
    if step_reveal == N_VIZ:
        FONT_SIZE        = 7.5
        FONT_FAMILY      = "DejaVu Sans"
        V_mkt            = contract.V_market
        price_rv_50      = price_rv          # crr_full returns N_PRICE=50 price
        mkt_overprice_pct = (V_mkt - price_rv_50) / V_mkt * 100

        fig, ax = plt.subplots(figsize=(14, 8))
        fig.patch.set_facecolor(COLORS["bg"])
        ax.set_facecolor(COLORS["bg"])
        ax.set_xlim(-0.5, N_VIZ + 0.8)
        ax.set_ylim(y_min - margin * 1.4, y_max + margin * 0.5)
        ax.set_xlabel("Time step", fontsize=9)
        ax.set_ylabel("Stock Price ($)", fontsize=9)
        ax.set_title(
            f"Contract {contract_label}  ·  Backward Induction Complete — All V Values Revealed\n"
            f"p*={p:.4f}  |  CRR fair value (N=50): ${price_rv_50:.3f}  vs  Market: ${V_mkt:.3f}",
            fontsize=10, fontweight="bold", color="#1E3A5F"
        )
        ax.grid(alpha=0.2)

        # Tree edges
        for i in range(1, N_VIZ + 1):
            for j, s in enumerate(S_lat[i]):
                if j > 0:
                    ax.plot([i-1, i], [S_lat[i-1][j-1], s], "-",
                            color="#CBD5E1", lw=0.8, alpha=0.5)
                if j < len(S_lat[i-1]):
                    ax.plot([i-1, i], [S_lat[i-1][j], s], "-",
                            color="#CBD5E1", lw=0.8, alpha=0.5)

        # All nodes + V labels
        for i in range(N_VIZ + 1):
            for j, (s, v) in enumerate(zip(S_lat[i], V_lat[i])):
                payoff = max(K - s, 0.0)
                if i == N_VIZ:
                    itm = payoff > 0
                    fcc = COLORS["itm"] if itm else COLORS["otm"]
                    col = "#059669" if itm else "#DC2626"
                    ax.plot(i, s, "s", color=col, ms=12, zorder=4,
                            markerfacecolor=fcc, markeredgewidth=1.5)
                else:
                    ax.plot(i, s, "o", color="#7C3AED", ms=10, zorder=4)

                if i == 0 and j == 0:
                    ax.text(i + 0.07, s, f"V(N=50)=${price_rv_50:.3f}",
                            fontsize=6.5, va="center", color="#3730A3", fontweight="bold")
                else:
                    ax.text(i + 0.07, s, f"V=${v:.2f}",
                            fontsize=6, va="center", color="#3730A3")

        # Gold star above root + double-headed arrow
        root_s = S_lat[0][0]
        star_y = root_s + margin * 0.9
        ax.plot(0, star_y, marker="*", color="#F59E0B", markersize=11, zorder=7)
        ax.annotate("", xy=(0, root_s + 1.5), xytext=(0, star_y - 1.5),
                    arrowprops=dict(arrowstyle="<->", color="#DC2626", lw=1.8, zorder=8))

        # Callout box: market perspective, dark green bg, gold text
        callout_y = root_s - margin * 0.2
        ax.text(0.18, callout_y,
                f"★ Market charged  = ${V_mkt:.3f}\n"
                f"● CRR fair value  = ${price_rv_50:.3f}\n"
                f"Market overpriced by +{mkt_overprice_pct:.1f}%",
                fontsize=8, va="top", ha="center", color="#F59E0B", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#14532D",
                          edgecolor="white", linewidth=1.8, alpha=0.97), zorder=9)

        # Strike line
        ax.axhline(K, color="#F59E0B", lw=1.2, ls="--", alpha=0.7)

        # Symbol legend top-left
        legend_font    = FontProperties(family=FONT_FAMILY, size=FONT_SIZE)
        legend_handles = [
            mlines.Line2D([0],[0], marker="o", color="w", markerfacecolor="#7C3AED",
                          markersize=9, label="Tree node  V = option value (N=5)"),
            mlines.Line2D([0],[0], marker="o", color="w", markerfacecolor="#7C3AED",
                          markersize=9, label="Root  V(N=50) = accurate fair value"),
            mlines.Line2D([0],[0], marker="s", color="w", markerfacecolor="#D1FAE5",
                          markeredgecolor="#059669", markersize=9,
                          label="Leaf ITM: V = max(K−S, 0)"),
            mlines.Line2D([0],[0], marker="s", color="w", markerfacecolor="#FEE2E2",
                          markeredgecolor="#DC2626", markersize=9,
                          label="Leaf OTM: V = $0  (S > K)"),
            mlines.Line2D([0],[0], color="#F59E0B", lw=0, marker="*",
                          markerfacecolor="#F59E0B", markeredgecolor="#F59E0B",
                          markersize=9, label="Actual market premium (bid-ask mid)"),
            mlines.Line2D([0],[0], color="#F59E0B", lw=1.2, ls="--",
                          label=f"Strike K=${K:.0f}"),
        ]
        ax.legend(handles=legend_handles, loc="upper left",
                  prop=legend_font, framealpha=0.93, edgecolor="#CBD5E1", handlelength=1.2)

        # Contract info box bottom-left (matching font)
        expire_val = contract.get("EXPIRE_DATE", None)
        expire_str = str(expire_val)[:10] if expire_val is not None else f"DTE={contract.DTE:.0f}d"
        ax.text(0.01, 0.01,
                f"Contract\nAAPL  PUT\n"
                f"Expires: {contract.DTE:.0f} days ({expire_str})\n"
                f"Bid ${contract.P_BID:.2f} / Ask ${contract.P_ASK:.2f}\n"
                f"Strike K=${K:.0f}\n"
                f"S=${contract.UNDERLYING_LAST:.2f}  (Stock Price)",
                transform=ax.transAxes,
                fontsize=FONT_SIZE, fontfamily=FONT_FAMILY,
                va="bottom", ha="left", color="#1E293B",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                          edgecolor="#CBD5E1", alpha=0.95))

        ax.set_xticks(range(N_VIZ + 1))
        fig.tight_layout()
        return fig_to_b64(fig)

    # ── Intermediate frames: GridSpec + info panel layout ────────────────────
    fig = plt.figure(figsize=(13, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    gs = GridSpec(1, 4, figure=fig, width_ratios=[3, 0.1, 1, 0.05])
    ax_main = fig.add_subplot(gs[0])
    ax_info = fig.add_subplot(gs[2])

    ax_main.set_xlim(-0.5, N_VIZ + 0.5)
    ax_main.set_ylim(y_min - margin, y_max + margin)
    ax_main.set_facecolor(COLORS["bg"])
    ax_main.set_xlabel("Time step", fontsize=9)
    ax_main.set_ylabel("Stock Price ($)", fontsize=9)
    ax_main.set_title(
        f"Contract {contract_label}  ·  Backward Induction (step {step_reveal} of {N_VIZ})\n"
        f"V values propagate right→left  |  p*={p:.4f}",
        fontsize=10, fontweight="bold"
    )
    ax_main.grid(alpha=0.2)

    # Draw edges
    for i in range(1, N_VIZ + 1):
        for j, s in enumerate(S_lat[i]):
            if j > 0:
                ax_main.plot([i-1, i], [S_lat[i-1][j-1], s], "-",
                             color="#CBD5E1", lw=0.8, alpha=0.5)
            if j < len(S_lat[i-1]):
                ax_main.plot([i-1, i], [S_lat[i-1][j], s], "-",
                             color="#CBD5E1", lw=0.8, alpha=0.5)

    # Reveal from right: columns N_VIZ down to N_VIZ - step_reveal
    first_revealed = N_VIZ - step_reveal
    for i in range(N_VIZ + 1):
        if i >= first_revealed:
            for j, (s, v) in enumerate(zip(S_lat[i], V_lat[i])):
                ax_main.plot(i, s, "o", color="#7C3AED", ms=10, zorder=4)
                ax_main.text(i + 0.1, s, f"V=${v:.2f}", fontsize=6,
                             va="center", color="#3730A3")
        else:
            for s in S_lat[i]:
                ax_main.plot(i, s, "o", color="#CBD5E1", ms=7, zorder=3)

    ax_main.axhline(K, color="#F59E0B", lw=1.2, ls="--", alpha=0.7,
                    label=f"Strike K=${K:.0f}")
    ax_main.legend(fontsize=8, loc="upper right")
    ax_main.set_xticks(range(N_VIZ + 1))

    _info_panel(ax_info, contract, f"Phase 3: Backprop\nstep {step_reveal}/{N_VIZ}")
    fig.tight_layout()
    return fig_to_b64(fig)


def render_result(contract, contract_label):
    """Phase 4: result panel comparing V_model_rv vs V_market + both signals."""
    price_rv, _, _, _, _, _ = crr_full(
        contract.UNDERLYING_LAST, contract.STRIKE,
        contract.RV30, contract.T_years, "put", N_VIZ
    )

    fig = plt.figure(figsize=(13, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    gs = GridSpec(1, 4, figure=fig, width_ratios=[3, 0.1, 1, 0.05])
    ax_main = fig.add_subplot(gs[0])
    ax_info = fig.add_subplot(gs[2])
    ax_main.set_facecolor(COLORS["bg"])
    ax_main.axis("off")

    color = "#166534" if contract.regime == "herding" else COLORS["normal"]
    ax_main.text(0.5, 0.95,
                 f"Contract {contract_label}  ·  Result",
                 transform=ax_main.transAxes, fontsize=13, fontweight="bold",
                 color=color, ha="center", va="top")

    V_mkt   = contract.V_market
    edge_L1 = contract.edge_L1
    edge_L2 = contract.edge_L2

    # Price bar chart
    pct_err = (price_rv - V_mkt) / V_mkt * 100   # same as edge_L1 * 100
    err_col = "#DC2626" if pct_err < 0 else "#059669"

    fig.subplots_adjust(left=0.02, right=0.99, top=0.96, bottom=0.06)
    ax_bar = fig.add_axes([0.08, 0.54, 0.52, 0.32])
    categories = ["V_market", "V_model_rv"]
    vals       = [V_mkt, price_rv]
    bar_colors = ["#64748B", COLORS["L1"]]
    bars = ax_bar.bar(categories, vals, color=bar_colors, alpha=0.80, width=0.42)

    # Value labels above each bar — raised to clear the gold star
    for bar, v in zip(bars, vals):
        ax_bar.text(bar.get_x() + bar.get_width() / 2, v + max(vals) * 0.06,
                    f"${v:.3f}", ha="center", va="bottom",
                    fontsize=10, fontweight="bold")

    # Gold star on the V_market bar
    mkt_bar = bars[0]
    ax_bar.plot(mkt_bar.get_x() + mkt_bar.get_width() / 2, V_mkt,
                marker="*", color="#F59E0B", markersize=18, zorder=5,
                label=f"Actual market price  ${V_mkt:.3f}")

    # Horizontal dashed line at V_market level
    ax_bar.axhline(V_mkt, color="#F59E0B", lw=1.4, ls="--", alpha=0.85, zorder=4)

    # Double-headed arrow + % error annotation between the two bars
    x0 = bars[0].get_x() + bars[0].get_width()
    x1 = bars[1].get_x()
    x_mid = (x0 + x1) / 2
    y_lo  = min(V_mkt, price_rv)
    y_hi  = max(V_mkt, price_rv)
    ax_bar.annotate("", xy=(x_mid, y_hi), xytext=(x_mid, y_lo),
                    arrowprops=dict(arrowstyle="<->", color=err_col, lw=1.8))
    ax_bar.text(x_mid + 0.04, (y_lo + y_hi) / 2,
                f"{pct_err:+.1f}%\nerror",
                color=err_col, fontsize=9, fontweight="bold", va="center")

    ax_bar.set_ylabel("Option Price ($)", fontsize=9)
    ax_bar.set_title(
        f"Predicted vs Actual  ·  % error = {pct_err:+.2f}%",
        fontsize=9, fontweight="bold", color=err_col
    )
    ax_bar.set_ylim(0, max(vals) * 1.50)
    ax_bar.legend(fontsize=7.5, loc="upper left")
    ax_bar.grid(axis="y", alpha=0.3)

    # Edge summary text — no blank spacers, compact spacing to stay in bounds
    col_L1 = "#DC2626" if edge_L1 < 0 else "#059669"
    col_L2 = "#DC2626" if edge_L2 < 0 else "#059669"

    lines = [
        ("Layer 1 edge",    f"{edge_L1:+.4f}  ({edge_L1*100:+.1f}%)", col_L1),
        ("  Interpretation", "market OVERPRICES" if edge_L1 < 0 else "market UNDERPRICES", col_L1),
        ("Layer 2 edge",    f"{edge_L2:+.4f}", col_L2),
        ("  p_independent", f"{contract.p_independent:.4f}", COLORS["L2"]),
        ("  q_market",      f"{contract.q_market:.4f}",      "#0D1F3C"),
        ("  Interpretation", "market OVERPRICES" if edge_L2 < 0 else "market UNDERPRICES", col_L2),
        ("Agreement",
         ("BOTH SELL — strong signal" if edge_L1 < 0 and edge_L2 < 0 else
          "BOTH BUY  — strong signal" if edge_L1 > 0 and edge_L2 > 0 else
          "MIXED — models disagree"),
         "#DC2626" if (edge_L1 < 0 and edge_L2 < 0) else "#059669"),
        ("Regime", contract.regime.upper(), color),
    ]

    y0 = 0.36
    for label, val, c in lines:
        ax_main.text(0.07, y0, label + (":" if label else ""),
                     transform=ax_main.transAxes, fontsize=8.5,
                     color="#0D1F3C", va="top", fontweight="bold")
        ax_main.text(0.52, y0, val, transform=ax_main.transAxes,
                     fontsize=8.5, color=c, va="top", fontweight="bold")
        y0 -= 0.050

    # Footer pinned to the very bottom of the figure
    fig.text(0.38, 0.02, "Phase 4 of 4  |  Contract complete",
             fontsize=8, color="#0D1F3C", ha="center", va="bottom")

    _info_panel(ax_info, contract, "Phase 4: Result", price_rv=price_rv)
    return fig_to_b64(fig)


def render_comparison_summary(contract_A, contract_B):
    """Final frame: side-by-side summary of both contracts."""
    price_A, _, _, _, _, _ = crr_full(
        contract_A.UNDERLYING_LAST, contract_A.STRIKE,
        contract_A.RV30, contract_A.T_years, "put", N_VIZ
    )
    price_B, _, _, _, _, _ = crr_full(
        contract_B.UNDERLYING_LAST, contract_B.STRIKE,
        contract_B.RV30, contract_B.T_years, "put", N_VIZ
    )

    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    fig.suptitle(
        "Cross-Model Comparison — Both Contracts\n"
        "Same Question, Two Independent Methods",
        fontsize=13, fontweight="bold"
    )

    for ax, contract, price_rv, lbl in [
        (axes[0], contract_A, price_A, "Contract A"),
        (axes[1], contract_B, price_B, "Contract B"),
    ]:
        ax.set_facecolor(COLORS["bg"])
        ax.axis("off")

        color  = "#166534" if contract.regime == "herding" else COLORS["normal"]
        e_L1   = contract.edge_L1
        e_L2   = contract.edge_L2
        col_L1 = "#DC2626" if e_L1 < 0 else "#059669"
        col_L2 = "#DC2626" if e_L2 < 0 else "#059669"

        ax.text(0.5, 0.97, lbl, transform=ax.transAxes, fontsize=12,
                fontweight="bold", color=color, ha="center", va="top")
        ax.text(0.5, 0.90, contract.regime.upper() + " REGIME",
                transform=ax.transAxes, fontsize=10, color=color,
                ha="center", va="top", fontweight="bold")

        rows = [
            ("Date",       str(contract.QUOTE_DATE)[:10],           "#0F172A"),
            ("S",          f"${contract.UNDERLYING_LAST:.2f}",      "#0F172A"),
            ("K",          f"${contract.STRIKE:.2f}",               "#0F172A"),
            ("DTE",        f"{contract.DTE:.0f} days",              "#0F172A"),
            ("V_market",   f"${contract.V_market:.3f}",             "#0F172A"),
            ("V_model_rv", f"${price_rv:.3f}",                      COLORS["L1"]),
            ("edge_L1",    f"{e_L1:+.4f}  ({e_L1*100:+.1f}%)",    col_L1),
            ("p_indep",    f"{contract.p_independent:.4f}",         COLORS["L2"]),
            ("q_market",   f"{contract.q_market:.4f}",              "#0D1F3C"),
            ("edge_L2",    f"{e_L2:+.4f}",                         col_L2),
        ]
        y0 = 0.80
        for label, val, c in rows:
            ax.text(0.08, y0, label + ":", transform=ax.transAxes,
                    fontsize=8.5, color="#0D1F3C", va="top", fontweight="bold")
            ax.text(0.55, y0, val, transform=ax.transAxes,
                    fontsize=8.5, color=c, va="top", fontweight="bold")
            y0 -= 0.058

        verdict = ("BOTH: SELL SIGNAL" if e_L1 < 0 and e_L2 < 0 else
                   "BOTH: BUY SIGNAL"  if e_L1 > 0 and e_L2 > 0 else
                   "MIXED SIGNAL")
        vcol   = "#166534" if e_L1 < 0 and e_L2 < 0 else (
                 "#059669" if e_L1 > 0 and e_L2 > 0 else "#F59E0B")
        ax.text(0.5, y0 - 0.03, verdict, transform=ax.transAxes,
                fontsize=11, color=vcol, ha="center", va="top", fontweight="bold")

    fig.tight_layout()
    return fig_to_b64(fig)


# ── Tooltip glossary (keyed by frame index as string) ─────────────────────────

_PROFILE_TERMS = [
    {"term": "S (Underlying)",  "def": "Current AAPL stock price at the quote date. S₀ is the root node of the binomial tree — all future stock paths branch from here."},
    {"term": "K (Strike)",      "def": "The agreed exercise price. A put is In-The-Money (ITM) when S < K, meaning the holder can sell stock at K above the current market price."},
    {"term": "DTE",             "def": "Days To Expiration — calendar days remaining until the option expires and any unexercised value is lost."},
    {"term": "T (Time)",        "def": "Time to expiry in years (= DTE ÷ 365). The CRR model divides T into N discrete steps of length Δt = T/N."},
    {"term": "RV30 (σ)",   "def": "30-day Realized Volatility — annualized standard deviation of daily log-returns over the past 30 days. Used as σ in CRR instead of implied vol."},
    {"term": "IV (Implied Vol)","def": "Implied Volatility — the market’s forward-looking vol embedded in the option premium. Often inflated above RV30 in herding regimes, signaling crowd overbidding."},
    {"term": "V_market",        "def": "Option market price = (bid + ask) ÷ 2. This is the actual premium a buyer pays — the ground-truth price the CRR model is compared against."},
    {"term": "Risk-free r",     "def": "Risk-free interest rate used to discount future payoffs. Set to 2% — approximate average 3-month T-bill rate over 2016–2020."},
    {"term": "CRR",             "def": "Cox-Ross-Rubinstein (1979) binomial lattice model. Builds a recombining stock-price tree forward, then backward-inducts option values accounting for early exercise."},
    {"term": "HERDING REGIME",  "def": "Market condition where ATM IV significantly exceeds RV30. Indicates crowd overbidding — option premiums are above their statistical fair value."},
    {"term": "NORMAL REGIME",   "def": "Market condition where IV ≈ RV. Options are fairly priced; CRR and XGBoost both expect minimal exploitable edge."},
]

_RESULT_TERMS = [
    {"term": "V_market",        "def": "Actual market premium (bid–ask midpoint) — what a trader paid for this contract."},
    {"term": "V_model_rv",      "def": "CRR fair-value estimate using RV30 as σ with N=50 steps. The model’s view of what the option is theoretically worth."},
    {"term": "Layer 1 edge",    "def": "(V_model_rv − V_market) / V_market. Negative = market charges more than fair value (overpriced). The core Layer 1 trading signal."},
    {"term": "Layer 2 edge",    "def": "XGBoost signal = p_independent − q_market. ML-based estimate of mispricing using historical feature patterns."},
    {"term": "p_independent",   "def": "XGBoost’s estimated probability this put expires ITM. Trained on 4 years of AAPL option outcomes — independent of current market price."},
    {"term": "q_market",        "def": "Market-implied ITM probability = put mid-price ÷ strike. Reflects the crowd’s consensus on ITM likelihood."},
    {"term": "Agreement",       "def": "BOTH SELL: CRR and XGBoost both detect overpricing — strongest signal. MIXED: models disagree — no trade recommended."},
    {"term": "Regime",          "def": "HERDING: IV ≫ RV, crowd overbids, both models detect edge. NORMAL: IV ≈ RV, efficient pricing, minimal edge."},
]

_SUMMARY_TERMS = [
    {"term": "V_model_rv",      "def": "CRR fair value (N=50, σ=RV30). Compared to V_market to compute Layer 1 edge."},
    {"term": "edge_L1",         "def": "(V_model_rv − V_market) / V_market. Negative = CRR finds market overprices this option."},
    {"term": "p_indep",         "def": "XGBoost-estimated ITM probability. Trained on historical AAPL outcomes, independent of market prices."},
    {"term": "q_market",        "def": "Market-implied ITM probability = put premium ÷ strike. The crowd’s consensus on ITM odds."},
    {"term": "edge_L2",         "def": "p_independent − q_market. Negative = market overestimates ITM probability relative to historical base rates."},
    {"term": "HERDING REGIME",  "def": "Crowd-driven IV premium over RV. Both CRR and XGBoost detect systematic overpricing; strongest trading signal when both agree."},
    {"term": "NORMAL REGIME",   "def": "IV ≈ RV; efficient pricing. Both models find minimal edge — NO TRADE across both layers."},
]

# Populated in main() once frame indices are known
GLOSSARY = {}

# ── Image hotspot overlays (% coordinates over the rendered PNG) ───────────────
# l/t/w/h are left/top/width/height as % of the displayed image size.
# Slides 0 & 14: render_phase0  (figsize 13×7, GridSpec 3:0.1:1:0.05, tight_layout)
# Slides 13 & 27: render_result  (figsize 13×7, subplots_adjust l=0.02 r=0.99 t=0.96 b=0.06)
# Slide 28: render_comparison_summary (figsize 14×7, subplots 1×2, tight_layout)

_PROFILE_PARAMS = [
    # Parameter rows — narrow width (label text only)
    {"l":  8, "t": 20, "w": 18, "h":  6,
     "label": "Quote Date",
     "tip": "The calendar date when this option contract's market data was captured from the exchange."},
    {"l":  8, "t": 26, "w": 18, "h":  6,
     "label": "Underlying (S)",
     "tip": "Current AAPL stock price at the quote date. S0 is the root node of the CRR binomial tree — all future price paths branch from this starting value."},
    {"l":  8, "t": 32, "w": 18, "h":  6,
     "label": "Strike (K)",
     "tip": "The agreed exercise price of the put option. The put is In-The-Money (ITM) when the stock price S falls below K — the holder profits by selling stock at K above the current market price."},
    {"l":  8, "t": 38, "w": 18, "h":  6,
     "label": "DTE (Days To Expiration)",
     "tip": "Calendar days remaining until the option contract expires. After expiry, any unexercised intrinsic value is permanently lost."},
    {"l":  8, "t": 44, "w": 18, "h":  6,
     "label": "Time (T)",
     "tip": "Time to expiry expressed in years (= DTE / 365). The CRR model divides T into N discrete time steps of length dt = T/N."},
    {"l":  8, "t": 50, "w": 18, "h":  5,
     "label": "RV30 — sigma input to CRR",
     "tip": "30-day Realized Volatility: annualized standard deviation of AAPL daily log-returns over the past 30 days. Used as sigma in the CRR formula instead of implied vol, so the model's fair value is independent of the market price being tested."},
    {"l":  8, "t": 55, "w": 18, "h":  5,
     "label": "IV (Implied Volatility)",
     "tip": "Implied Volatility backed out from the market option price. When IV is significantly above RV30, the market is pricing in more uncertainty than history justifies — a hallmark of the herding regime."},
    {"l":  8, "t": 60, "w": 18, "h":  5,
     "label": "V_market",
     "tip": "Market price of the option = (bid + ask) / 2. The actual premium a buyer pays — the ground-truth price the CRR model's fair value estimate is tested against."},
    {"l":  8, "t": 65, "w": 18, "h":  5,
     "label": "Risk-free r",
     "tip": "Risk-free interest rate used to discount future option payoffs to present value. Fixed at 2% — the approximate average 3-month T-bill rate over the 2016-2020 study period."},
    {"l":  8, "t": 70, "w": 18, "h":  5,
     "label": "CRR Steps (N)",
     "tip": "Number of time steps in the binomial tree. N=50 gives accurate pricing (finer lattice). N=5 is used for on-screen visualization so the tree fits readably."},
]

# Title hotspot for slide 0 — herding regime (centered title, ~44% wide in image)
_PROFILE_SPOTS_A = [
    {"l": 12, "t":  5, "w": 44, "h":  8, "flip": True,
     "label": "Herding Regime",
     "tip": "HERDING REGIME: Implied Volatility (IV) significantly exceeds 30-day Realized Volatility (RV30). Crowd participants overbid option premiums — paying for more uncertainty than history justifies. Both CRR and XGBoost models detect systematic overpricing, producing the strongest combined BOTH SELL signal."},
] + _PROFILE_PARAMS

# Title hotspot for slide 14 — normal regime (shorter title, ~40% wide in image)
_PROFILE_SPOTS_B = [
    {"l": 14, "t":  5, "w": 40, "h":  8, "flip": True,
     "label": "Normal Regime",
     "tip": "NORMAL REGIME — FAIR PRICING: Implied Volatility (IV) approximately equals 30-day Realized Volatility (RV30). The market prices options efficiently — premiums reflect historical uncertainty without systemic overbidding. Both CRR and XGBoost find minimal detectable edge. This is a NO TRADE condition."},
] + _PROFILE_PARAMS

_RESULT_SPOTS = [
    # Bar x-axis label hotspots — positioned at the bottom of the chart where the
    # text labels "V_market" and "V_model_rv" appear (image_t ≈ 37-44%).
    # Left label (V_market) at image_l ≈ 14-28%; right label (V_model_rv) at ≈ 42-56%.
    {"l": 14, "t": 37, "w": 14, "h":  7,
     "label": "V_market",
     "tip": "V_market: the actual market option price = (bid + ask) / 2. The real premium paid by a buyer for this AAPL put contract — the ground-truth price that the CRR model's fair value is tested against."},
    {"l": 42, "t": 37, "w": 14, "h":  7,
     "label": "V_model_rv",
     "tip": "(CRR Model Price using Realized Volatility): fair value of this put option computed by the Cox-Ross-Rubinstein binomial tree using RV30 (30-day realized volatility) as sigma instead of implied volatility. Using RV30 makes the model price fully independent of the market price being tested — a true out-of-sample estimate of fair value."},
    # Text rows — computed from figure geometry: step=3.9% per row in image space.
    # Rows at image_t: L1edge≈51, L1interp≈55, L2edge≈59, p_indep≈63, q_mkt≈67,
    #                  L2interp≈71, Agreement≈75, Regime≈78.  h=4 keeps each zone tight.
    {"l":  5, "t": 50, "w": 14, "h":  4,
     "label": "Layer 1 edge",
     "tip": "(V_model_rv - V_market) / V_market. Negative = market charges MORE than CRR fair value (overpriced). Positive = market underprices. The primary Layer 1 CRR trading signal."},
    {"l":  5, "t": 54, "w": 14, "h":  4,
     "label": "Layer 1 Interpretation",
     "tip": "OVERPRICES: market premium exceeds CRR fair value — sell signal. UNDERPRICES: market charges below fair value — buy signal."},
    {"l":  5, "t": 58, "w": 14, "h":  4,
     "label": "Layer 2 edge",
     "tip": "XGBoost ML signal = p_independent - q_market. An independent model-based estimate of mispricing using historical AAPL option features. Negative = crowd overbids relative to model."},
    {"l":  5, "t": 62, "w": 14, "h":  4,
     "label": "p_independent",
     "tip": "XGBoost classifier's estimated probability this put expires In-The-Money. Trained on 4 years of historical AAPL option outcomes — fully independent of current market prices."},
    {"l":  5, "t": 66, "w": 14, "h":  4,
     "label": "q_market",
     "tip": "Market-implied ITM probability = put mid-price / strike. Reflects the collective crowd consensus on whether this option will expire in-the-money."},
    {"l":  5, "t": 70, "w": 14, "h":  4,
     "label": "Layer 2 Interpretation",
     "tip": "OVERPRICES: p_indep is below q_market — crowd overestimates ITM chance. UNDERPRICES: p_indep exceeds q_market — crowd underestimates ITM chance."},
    {"l":  5, "t": 74, "w": 14, "h":  3,
     "label": "Signal Agreement",
     "tip": "BOTH SELL: CRR and XGBoost both detect overpricing — strongest combined signal. BOTH BUY: both detect underpricing. MIXED: models disagree — no trade recommended."},
    {"l":  5, "t": 77, "w": 14, "h":  4,
     "label": "Regime",
     "tip": "HERDING: IV significantly exceeds RV30 — crowd overbidding detected by both models. NORMAL: IV ≈ RV30 — efficient pricing, minimal detectable edge across both layers."},
]

# Slide 28 layout: figsize 14×7, 1×2 subplots, tight_layout + suptitle.
# Suptitle pushes axes top to ~fig_y 0.82. Each panel is ~50% of image width.
# Rows start at axes_y=0.80, step −0.058 → image spacing ≈5% per row.
# Rows 1-4 (Date/S/K/DTE) get no hotspot — they are identifying info only.
# Rows 5-10 (V_market…edge_L2) mapped to image_t ≈ 50-75%.
# Left panel label text at image_x ≈ 6%, right panel at ≈56%.
_SUMMARY_SPOTS = [
    # Left panel — Contract A (herding)
    # Header: "Contract A" + "HERDING REGIME" at image_t≈12% and 18%.
    # Width narrowed to label text width only (~22% centered at ~24%).
    {"l": 13, "t": 10, "w": 22, "h": 12,
     "label": "Contract A — Herding Regime",
     "tip": "HERDING REGIME: IV significantly exceeds RV30. Crowd overbidding inflates premiums above CRR fair value. Both models detect systematic overpricing — the strongest trading signal."},
    # Identifying rows — image_t: Date≈27, S≈32, K≈38, DTE≈43  (step≈5.2%)
    {"l":  2, "t": 26, "w": 10, "h":  5,
     "label": "Date (A)",
     "tip": "The calendar date when Contract A's market data was captured from the exchange."},
    {"l":  2, "t": 31, "w": 10, "h":  5,
     "label": "Underlying S (A)",
     "tip": "AAPL stock price at the Contract A quote date. S₀ is the root node of the CRR binomial tree — all future price paths branch from this value."},
    {"l":  2, "t": 36, "w": 10, "h":  5,
     "label": "Strike K (A)",
     "tip": "Exercise price of Contract A put. The put is In-The-Money (ITM) when AAPL stock price S falls below K — holder profits by selling at K above the current market price."},
    {"l":  2, "t": 41, "w": 10, "h":  5,
     "label": "DTE (A)",
     "tip": "Days To Expiration for Contract A. After expiry, any unexercised intrinsic value is permanently lost."},
    # Trading signal rows — confirmed correct at these positions
    {"l":  2, "t": 45, "w": 14, "h":  5,
     "label": "V_market (A)",
     "tip": "Market price of Contract A put (bid-ask midpoint). In herding regime, this is inflated above CRR fair value."},
    {"l":  2, "t": 50, "w": 14, "h":  5,
     "label": "V_model_rv (A)",
     "tip": "CRR fair value using RV30 as sigma with N=50 steps. Represents the model's estimate of what Contract A is truly worth."},
    {"l":  2, "t": 55, "w": 14, "h":  5,
     "label": "edge_L1 (A)",
     "tip": "(V_model_rv - V_market) / V_market. Strongly negative in herding regime — market significantly overprices relative to CRR fair value."},
    {"l":  2, "t": 60, "w": 14, "h":  5,
     "label": "p_indep (A)",
     "tip": "XGBoost-estimated ITM probability for Contract A. Based on historical AAPL patterns — independent of current market prices."},
    {"l":  2, "t": 65, "w": 14, "h":  5,
     "label": "q_market (A)",
     "tip": "Market-implied ITM probability for Contract A = put premium / strike. In herding regime, crowd inflates this above historical base rates."},
    {"l":  2, "t": 70, "w": 14, "h":  5,
     "label": "edge_L2 (A)",
     "tip": "p_independent - q_market for Contract A. Negative = crowd overestimates ITM chance. Combined with negative edge_L1: strong BOTH SELL signal."},
    # Right panel — Contract B (normal)
    # Header centered at image_l≈75%; width narrowed same as left panel.
    {"l": 63, "t": 10, "w": 22, "h": 12,
     "label": "Contract B — Normal Regime",
     "tip": "NORMAL REGIME: IV approximately equals RV30. Efficient pricing — both CRR and XGBoost find minimal edge. NO TRADE condition for this contract."},
    {"l": 52, "t": 26, "w": 10, "h":  5,
     "label": "Date (B)",
     "tip": "The calendar date when Contract B's market data was captured from the exchange."},
    {"l": 52, "t": 31, "w": 10, "h":  5,
     "label": "Underlying S (B)",
     "tip": "AAPL stock price at the Contract B quote date. Normal regime — IV ≈ RV30, indicating efficient pricing at this moment."},
    {"l": 52, "t": 36, "w": 10, "h":  5,
     "label": "Strike K (B)",
     "tip": "Exercise price of Contract B put. Near-ATM in the normal regime — market prices reflect historical base rates accurately."},
    {"l": 52, "t": 41, "w": 10, "h":  5,
     "label": "DTE (B)",
     "tip": "Days To Expiration for Contract B. Longer DTE than Contract A, reflecting a different market moment."},
    {"l": 52, "t": 45, "w": 14, "h":  5,
     "label": "V_market (B)",
     "tip": "Market price of Contract B put (bid-ask midpoint). Close to CRR fair value in normal regime."},
    {"l": 52, "t": 50, "w": 14, "h":  5,
     "label": "V_model_rv (B)",
     "tip": "CRR fair value for Contract B using RV30 as sigma, N=50 steps. Near V_market in normal regime — confirms efficient pricing."},
    {"l": 52, "t": 55, "w": 14, "h":  5,
     "label": "edge_L1 (B)",
     "tip": "(V_model_rv - V_market) / V_market for Contract B. Near zero in normal regime — market aligns with CRR fair value."},
    {"l": 52, "t": 60, "w": 14, "h":  5,
     "label": "p_indep (B)",
     "tip": "XGBoost-estimated ITM probability for Contract B. Should closely match q_market in a normal pricing regime."},
    {"l": 52, "t": 65, "w": 14, "h":  5,
     "label": "q_market (B)",
     "tip": "Market-implied ITM probability for Contract B. Reflects fair crowd consensus in normal conditions."},
    {"l": 52, "t": 70, "w": 14, "h":  5,
     "label": "edge_L2 (B)",
     "tip": "p_independent - q_market for Contract B. Near zero — ML model and market agree on ITM probability. Confirms NO TRADE."},
]

HOTSPOTS = {
    "0":  _PROFILE_SPOTS_A,
    "13": _RESULT_SPOTS,
    "14": _PROFILE_SPOTS_B,
    "27": _RESULT_SPOTS,
    "28": _SUMMARY_SPOTS,
}


# ── HTML assembly ─────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AAPL CRR Binomial Tree — Layer 1 vs Layer 2</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0F172A;
          color: #E2E8F0; margin: 0; padding: 0; }}
  h1   {{ text-align: center; font-size: 1.1rem; padding: 12px 0 4px;
          color: #38BDF8; margin: 0; }}
  .subtitle {{ text-align: center; font-size: 0.78rem; color: #94A3B8;
               margin-bottom: 8px; }}
  #img-wrapper {{ position: relative; max-width: 96%; margin: 0 auto 6px;
                  display: block; }}
  #frame-img   {{ display: block; width: 100%;
                  border-radius: 6px; border: 1px solid #1E293B; }}
  #hotspot-layer {{ position: absolute; top: 0; left: 0; right: 0; bottom: 0;
                    pointer-events: none; }}
  .hotspot {{ position: absolute; cursor: help; pointer-events: auto; }}
  .htip {{ display: none; position: absolute; bottom: 105%; left: 0;
           background: #0F172A; border: 1px solid #38BDF8; color: #E2E8F0;
           padding: 8px 12px; border-radius: 7px; font-size: 0.74rem;
           width: 280px; z-index: 500; line-height: 1.6;
           pointer-events: none; white-space: normal; }}
  .htip strong {{ display: block; margin-bottom: 4px; color: #38BDF8;
                  font-size: 0.77rem; }}
  .hotspot:hover .htip {{ display: block; }}
  .controls  {{ display: flex; align-items: center; justify-content: center;
                gap: 8px; padding: 6px 12px; flex-wrap: wrap; }}
  button {{ background: #1E40AF; color: white; border: none; border-radius: 5px;
            padding: 6px 14px; cursor: pointer; font-size: 0.82rem; }}
  button:hover {{ background: #2563EB; }}
  .jump-btn {{ background: #7C3AED; }}
  .jump-btn:hover {{ background: #6D28D9; }}
  input[type=range] {{ width: 220px; accent-color: #38BDF8; }}
  select {{ background: #1E293B; color: #E2E8F0; border: 1px solid #334155;
            border-radius: 4px; padding: 4px 8px; font-size: 0.82rem; }}
  #frame-label {{ font-size: 0.8rem; color: #94A3B8; min-width: 180px;
                  text-align: center; }}
  #counter {{ font-size: 0.78rem; color: #64748B; }}
</style>
</head>
<body>
<h1>AAPL CRR Binomial Tree Animation — Layer 1 vs Layer 2 (PLAN2.md)</h1>
<div class="subtitle">
  Contract A (herding regime) · Contract B (normal regime) ·
  Both models evaluated on the same real AAPL put options
</div>

<div id="img-wrapper">
  <img id="frame-img" src="" alt="animation frame">
  <div id="hotspot-layer"></div>
</div>

<div class="controls">
  <button onclick="prevFrame()">&#9664; Prev</button>
  <button onclick="togglePlay()" id="play-btn">&#9654; Play</button>
  <button onclick="nextFrame()">Next &#9654;</button>
  <input type="range" id="slider" min="0" max="{max_frame}" value="0"
         oninput="goTo(parseInt(this.value))">
  <span id="counter">0 / {max_frame}</span>
  <select id="speed-sel" onchange="updateSpeed()">
    <option value="2000">Slow</option>
    <option value="1200" selected>Normal</option>
    <option value="600">Fast</option>
  </select>
  <button class="jump-btn" onclick="goTo({jump_A})">&#9654; Contract A</button>
  <button class="jump-btn" onclick="goTo({jump_B})">&#9654; Contract B</button>
  <button class="jump-btn" onclick="goTo({jump_cmp})">&#9654; Summary</button>
</div>
<div class="controls">
  <span id="frame-label">Loading...</span>
</div>

<script>
const frames   = {frames_json};
const labels   = {labels_json};
const hotspots = {hotspots_json};
let current    = 0;
let playing    = false;
let timer      = null;
let delay      = 1200;

function hesc(s) {{
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

function updateHotspots(i) {{
  var layer = document.getElementById('hotspot-layer');
  var spots = hotspots[String(i)] || [];
  var html = '';
  for (var j = 0; j < spots.length; j++) {{
    var s = spots[j];
    var tipStyle = s.flip ? ' style="bottom:auto;top:110%;"' : '';
    html += '<div class="hotspot" style="left:' + s.l + '%;top:' + s.t + '%;width:' + s.w + '%;height:' + s.h + '%">'
          + '<span class="htip"' + tipStyle + '><strong>' + hesc(s.label) + '</strong>' + hesc(s.tip) + '</span>'
          + '</div>';
  }}
  layer.innerHTML = html;
}}

function show(i) {{
  current = Math.max(0, Math.min(i, frames.length - 1));
  document.getElementById('frame-img').src = 'data:image/png;base64,' + frames[current];
  document.getElementById('frame-label').textContent = labels[current];
  document.getElementById('slider').value = current;
  document.getElementById('counter').textContent = current + ' / ' + (frames.length - 1);
  updateHotspots(current);
}}

function nextFrame() {{ show(current + 1); }}
function prevFrame() {{ show(current - 1); }}
function goTo(i)     {{ show(i); }}

function togglePlay() {{
  playing = !playing;
  document.getElementById("play-btn").textContent = playing ? "⏸ Pause" : "▶ Play";
  if (playing) advance();
  else {{ clearTimeout(timer); }}
}}

function advance() {{
  if (!playing) return;
  show(current + 1 < frames.length ? current + 1 : 0);
  timer = setTimeout(advance, delay);
}}

function updateSpeed() {{
  delay = parseInt(document.getElementById("speed-sel").value);
}}

show(0);
</script>
</body>
</html>
"""


def build_frames(contract_A, contract_B):
    frames = []
    labels = []

    def add(b64, label):
        frames.append(b64)
        labels.append(label)

    jump_A = 0

    # ── Contract A ────────────────────────────────────────────────────────────
    add(render_phase0(contract_A, "A"), "A · Phase 0: Contract Profile")
    for step in range(N_VIZ + 1):
        add(render_lattice(contract_A, "A", step),
            f"A · Phase 1: Lattice step {step}/{N_VIZ}")
    add(render_payoffs(contract_A, "A"), "A · Phase 2: Terminal Payoffs")
    for step in range(1, N_VIZ + 1):
        add(render_backprop(contract_A, "A", step),
            f"A · Phase 3: Backward Induction step {step}/{N_VIZ}")
    add(render_result(contract_A, "A"), "A · Phase 4: Result")

    jump_B = len(frames)

    # ── Contract B ────────────────────────────────────────────────────────────
    add(render_phase0(contract_B, "B"), "B · Phase 0: Contract Profile")
    for step in range(N_VIZ + 1):
        add(render_lattice(contract_B, "B", step),
            f"B · Phase 1: Lattice step {step}/{N_VIZ}")
    add(render_payoffs(contract_B, "B"), "B · Phase 2: Terminal Payoffs")
    for step in range(1, N_VIZ + 1):
        add(render_backprop(contract_B, "B", step),
            f"B · Phase 3: Backward Induction step {step}/{N_VIZ}")
    add(render_result(contract_B, "B"), "B · Phase 4: Result")

    jump_cmp = len(frames)

    # ── Comparison summary ────────────────────────────────────────────────────
    add(render_comparison_summary(contract_A, contract_B),
        "Cross-Model Summary: A vs B")

    return frames, labels, jump_A, jump_B, jump_cmp


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import json

    print("Loading AAPL dataset (10% sample) ...")
    df = load_prepared(sample_frac=0.10)
    print(f"  {len(df):,} rows loaded")

    print("\nSelecting contracts ...")
    contract_A, contract_B = select_contracts(df)

    print("\nRendering frames ...")
    frames, labels, jump_A, jump_B, jump_cmp = build_frames(contract_A, contract_B)
    print(f"  {len(frames)} frames rendered")

    html = HTML_TEMPLATE.format(
        max_frame     = len(frames) - 1,
        jump_A        = jump_A,
        jump_B        = jump_B,
        jump_cmp      = jump_cmp,
        frames_json   = json.dumps(frames),
        labels_json   = json.dumps(labels),
        hotspots_json = json.dumps(HOTSPOTS),
    )

    with open(OUT, "w") as f:
        f.write(html)
    print(f"\n  Saved -> {OUT}")
    print("Done.")


if __name__ == "__main__":
    main()
