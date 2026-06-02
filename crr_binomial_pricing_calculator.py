"""CRR Binomial Pricing Calculator — Interactive Streamlit App."""

import base64
import sys
import time
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent / "project"))
from greeks import compute_greeks
from kelly import _edge_to_win_prob, kelly_fractions
from simulation import simulate_pnl
from tree import price_american_option

# ── page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CRR Binomial Pricing Calculator",
    page_icon="📊",
    layout="wide",
)

# ── color palette (CS495 Capstone presentation) ────────────────────────────────
BG          = "#0E1117"   # Streamlit near-black (unchanged)
NAVY_DARK   = "#0B2041"   # deep navy — legend panels
NAVY_MID    = "#163A8C"   # medium navy — primary blue (CRR Model, SELL, HERDING)
SKY_BLUE    = "#3A7BD5"   # bright accent — convergence, ref lines, spines
LABEL_BLUE  = "#88B8E8"   # labels
DESC_BLUE   = "#C8DCF0"   # description / secondary text
FOREST      = "#145A22"   # forest green — BUY, NORMAL, positive edge, Full Kelly
BURNT_ORG   = "#7A1E00"   # burnt orange — accent
GOLD        = "#F57F17"   # gold — Market, ref lines, signal headings, lightning icon
DEEP_RED    = "#C62828"   # deep red — negative edge
MAROON      = "#880E4F"   # maroon — strongest OTM
SILVER      = "#546E7A"   # silvergray — NO TRADE, COMPRESSION

# ── sidebar + button theme (CSS injection — Streamlit widgets) ────────────────
st.markdown(
    """
    <style>
    /* ───── Sidebar background → medium gray (max-specificity) ───── */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] > div > div,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {
        background-color: #3F454C !important;
    }
    /* Sidebar section headings (st.header, st.subheader) → white */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4 {
        color: white !important;
    }
    /* Sidebar widget labels → light blue */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #C8DCF0 !important;
    }

    /* ───── Primary button (Calculate) → navy with sky-blue border ───── */
    .stButton button[kind="primary"] {
        background-color: #163A8C !important;
        border-color: #3A7BD5 !important;
        color: white !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #1E4DB8 !important;
        border-color: #88B8E8 !important;
    }

    /* ───── Slider thumb → gold ──────────────────────────────────────
       Aggressively target every nesting level Streamlit 1.57 / BaseWeb
       might render. The thumb may be either the [role="slider"] node
       itself OR a child div. All bases covered with !important. */
    div[role="slider"],
    div[role="slider"] > div,
    .stSlider div[role="slider"],
    .stSlider div[role="slider"] > div,
    section [role="slider"],
    section [role="slider"] > div {
        background: #F57F17 !important;
        background-color: #F57F17 !important;
        background-image: none !important;
        border-color: white !important;
        box-shadow: 0 0 0 1px #F57F17 !important;
    }
    /* Slider numbers (min / max tick labels + current value) → white
       on the gray sidebar. Brute-force every child of .stSlider, then
       re-pin the widget label back to descblue for hierarchy. */
    section[data-testid="stSidebar"] .stSlider,
    section[data-testid="stSidebar"] .stSlider * {
        color: white !important;
    }
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stSlider label * {
        color: #C8DCF0 !important;
    }
    /* Slider "current value" bubble shown above the thumb */
    div[data-baseweb="slider"] [data-baseweb="tooltip"],
    div[data-baseweb="slider"] [data-baseweb="tooltip"] > div {
        background-color: #163A8C !important;
        color: white !important;
    }

    /* ───── Selectbox dropdown chevron (▾) → white ────────────────────
       Match Option Type / Action arrows to the white input-text color
       (was rendering as black against the dark navy field). */
    section[data-testid="stSidebar"] [data-baseweb="select"] svg,
    section[data-testid="stSidebar"] .stSelectbox svg {
        fill: white !important;
        color: white !important;
    }

    /* ───── Number-input field background → dark navy ───── */
    .stNumberInput input,
    .stTextInput input,
    div[data-baseweb="input"] input,
    div[data-baseweb="select"] > div {
        background-color: #1E2737 !important;
        color: white !important;
    }
    /* Number-input +/- buttons → match field background */
    .stNumberInput button {
        background-color: #1E2737 !important;
        border-color: #3A7BD5 !important;
        color: #C8DCF0 !important;
    }
    .stNumberInput button:hover {
        background-color: #163A8C !important;
    }

    /* ───── Page caption → navy blue, italic ──────────────────────────
       Applies to the subtitle under "CRR Binomial Pricing Calculator". */
    [data-testid="stCaptionContainer"],
    .stCaption,
    .stCaption p {
        color: #163A8C !important;
        font-style: italic !important;
    }

    /* ───── "About this screen" expander cards ────────────────────────
       Reusable styled block placed inside st.expander on each tab. */
    .about-box {
        background: #F8FAFC;
        border-left: 4px solid #3A7BD5;
        padding: 16px 20px;
        border-radius: 6px;
        margin: 4px 0 8px 0;
        line-height: 1.55;
        color: #1A1A2E;
    }
    .about-box .section-label {
        color: #163A8C;
        font-weight: bold;
        font-size: 1.02rem;
        margin: 12px 0 4px 0;
    }
    .about-box .section-label:first-child {
        margin-top: 0;
    }
    .about-box p {
        margin: 0 0 10px 0;
    }
    .about-box p:last-child {
        margin-bottom: 0;
    }
    .about-box code {
        background: #EEF2F7;
        padding: 1px 5px;
        border-radius: 3px;
        color: #163A8C;
        font-family: 'SF Mono', Menlo, monospace;
        font-size: 0.93em;
    }
    .about-box em {
        color: #475569;
    }

    /* ───── Expander header button ("About this screen") → navy + white ─
       Targets the clickable summary element of st.expander. */
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] details > summary,
    .streamlit-expanderHeader {
        background-color: #163A8C !important;
        color: white !important;
        border-radius: 6px !important;
        padding: 10px 14px !important;
    }
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] summary div,
    .streamlit-expanderHeader p {
        color: white !important;
        font-weight: bold !important;
    }
    [data-testid="stExpander"] summary svg {
        fill: white !important;
        color: white !important;
    }
    /* Hover state — slightly lighter navy */
    [data-testid="stExpander"] summary:hover {
        background-color: #1E4DB8 !important;
    }

    /* ───── Greeks table — navy header, white text ────────────────────
       Custom HTML table styled via .greeks-table class (Streamlit's
       st.dataframe renders to canvas in 1.57+ and can't be CSS-styled). */
    table.greeks-table {
        width: 100%;
        border-collapse: collapse;
        margin: 0.5rem 0 1rem 0;
        font-size: 0.95rem;
    }
    table.greeks-table thead th {
        background-color: #163A8C;
        color: white;
        font-weight: bold;
        padding: 10px 14px;
        text-align: left;
        border: 1px solid white;
    }
    table.greeks-table tbody td {
        padding: 10px 14px;
        border: 1px solid #E0E0E0;
        background-color: white;
        color: #1A1A2E;
    }
    table.greeks-table tbody tr:nth-child(even) td {
        background-color: #F5F7FA;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("CRR Binomial Pricing Calculator")
st.caption(
    "Cox-Ross-Rubinstein American option pricer · Kelly Criterion sizing · "
    "Monte Carlo simulation  |  Works for any ticker  ·  No dividends assumed"
)

# ── sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Contract Parameters")

    ticker = st.text_input("Ticker (for RV30 lookup)", value="AAPL").strip().upper()

    c1, c2 = st.columns(2)
    option_type = c1.selectbox("Option Type", ["put", "call"])
    action      = c2.selectbox("Action",      ["buy", "sell"])

    S        = st.number_input("Underlying Price (S $)",  value=200.00, min_value=1.0,    step=0.50,  format="%.2f")
    K        = st.number_input("Strike Price (K $)",      value=200.00, min_value=1.0,    step=0.50,  format="%.2f")
    V_market = st.number_input("Market Price (V_market)", value=10.00,  min_value=0.01,   step=0.10,  format="%.2f")
    iv       = st.number_input("Implied Volatility (IV)", value=0.30,   min_value=0.01,   max_value=5.0, step=0.01, format="%.4f")

    st.divider()
    DTE = st.number_input("Days to Expiration (DTE)", value=30,      min_value=1,   max_value=730)
    r   = st.number_input("Risk-free Rate (r)",       value=0.053,   min_value=0.0, max_value=0.20, step=0.001, format="%.3f")
    N   = st.number_input("CRR Steps (N)",            value=100,     min_value=10,  max_value=500,  step=10)

    st.divider()
    st.subheader("Kelly Parameters")
    capital  = st.number_input("Capital ($)",           value=100_000, min_value=1_000,  step=1_000)
    min_edge = st.number_input("Min Edge Threshold",    value=0.02,    min_value=0.001,  max_value=0.50, step=0.005, format="%.3f")

    st.divider()
    st.subheader("Tree Animation")
    N_disp     = st.slider("Display Steps (N)", min_value=4, max_value=12, value=7)
    anim_speed = st.slider("Speed (sec/step)",  min_value=0.05, max_value=1.0, value=0.25, step=0.05)

    run_btn = st.button("Calculate", type="primary", use_container_width=True)

T = float(DTE) / 365.0


# ── RV30 fetch ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_rv(tkr: str) -> dict | None:
    try:
        hist = yf.Ticker(tkr).history(period="6mo")["Close"]
        if hist.empty:
            return None
        log_ret = np.log(hist / hist.shift(1)).dropna()
        return {
            "rv30": float(log_ret.tail(30).std() * np.sqrt(252)),
            "rv60": float(log_ret.tail(60).std() * np.sqrt(252)),
        }
    except Exception:
        return None


# ── tree helpers ───────────────────────────────────────────────────────────────
def _build_display_tree(S, K, r, sigma, T, N_d, opt_type):
    """Full CRR tree for N_d steps used only for visualization."""
    dt = T / N_d
    u  = np.exp(sigma * np.sqrt(dt))
    d  = 1.0 / u
    p  = (np.exp(r * dt) - d) / (u - d)
    disc = np.exp(-r * dt)

    stock = {(i, j): S * (u ** (i - j)) * (d ** j)
             for i in range(N_d + 1) for j in range(i + 1)}

    option = {}
    for j in range(N_d + 1):
        ST = stock[(N_d, j)]
        option[(N_d, j)] = max(ST - K, 0) if opt_type == "call" else max(K - ST, 0)

    early = set()
    for i in range(N_d - 1, -1, -1):
        for j in range(i + 1):
            Sn = stock[(i, j)]
            intr = max(Sn - K, 0) if opt_type == "call" else max(K - Sn, 0)
            cont = disc * (p * option[(i + 1, j)] + (1 - p) * option[(i + 1, j + 1)])
            option[(i, j)] = max(intr, cont)
            if intr > cont and intr > 0:
                early.add((i, j))

    return stock, option, early


def _draw_tree(stock, option, early, N_d, fwd_up_to, bwd_from, opt_type):
    """Render one frame of the binomial tree."""
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    ax.set_facecolor("#0E1117")
    fig.patch.set_facecolor("#0E1117")
    # Equal aspect so plt.Circle renders as a true circle, not an oval
    ax.set_aspect("equal", adjustable="box")

    def pos(i, j):
        # 2× horizontal spacing makes data coords nearly square (x ≈ y range)
        return 2 * i, i - 2 * j

    # Branch direction is (2, ±1); unit vector magnitude = √5
    r5 = np.sqrt(5.0)
    # node_r must be large enough that the label text fits inside the circle
    node_r = max(0.65, 0.85 - N_d * 0.025)
    trim_x = node_r * 2.0 / r5   # line trim along x at each end
    trim_y = node_r * 1.0 / r5   # line trim along y at each end

    # Edges — trimmed to start/end exactly at each circle's perimeter
    for i in range(min(fwd_up_to, N_d)):
        for j in range(i + 1):
            x0, y0 = pos(i, j)
            x1 = 2 * (i + 1)
            # Correct target y: pos(i+1, j)[1] and pos(i+1, j+1)[1]
            y_up = (i + 1) - 2 * j
            y_dn = (i + 1) - 2 * (j + 1)
            ax.plot([x0 + trim_x, x1 - trim_x], [y0 + trim_y, y_up - trim_y],
                    color="#475569", lw=1.2, zorder=1)
            ax.plot([x0 + trim_x, x1 - trim_x], [y0 - trim_y, y_dn + trim_y],
                    color="#475569", lw=1.2, zorder=1)

    # Nodes
    fsize = max(5.5, 9.5 - N_d * 0.4)

    for i in range(min(fwd_up_to + 1, N_d + 1)):
        for j in range(i + 1):
            x, y = pos(i, j)
            show_opt = (i >= bwd_from)
            is_early = (i, j) in early and show_opt

            if i == 0:
                color = "#B45309"           # root — gold
            elif show_opt:
                color = "#7C3AED" if is_early else "#065F46"   # purple = early exercise, green = hold
            else:
                color = "#1E40AF"           # blue = stock price node

            circ = plt.Circle((x, y), node_r, color=color, zorder=3,
                               ec="#94A3B8", lw=0.6)
            ax.add_patch(circ)

            label = (f"${option[(i, j)]:.2f}" if show_opt
                     else f"${stock[(i, j)]:.0f}")
            ax.text(x, y, label, ha="center", va="center",
                    fontsize=fsize, color="white", fontweight="bold", zorder=4)

    # Axis styling
    ax.set_xlim(-1.2, 2 * N_d + 1.2)
    ax.set_ylim(-N_d - 1.5, N_d + 1.5)
    ax.set_xticks([2 * k for k in range(N_d + 1)])
    ax.set_xticklabels([str(round(k * DTE / N_d)) for k in range(N_d + 1)])
    ax.set_xlabel("Days from Today  →", color="#CBD5E1", fontsize=12)
    ax.set_ylabel("Binomial Tree Levels  (↑ up / ↓ down)", color="#CBD5E1", fontsize=10)
    phase = ("← Backward induction: option values"
             if bwd_from <= N_d else "Forward pass: stock prices")
    ax.set_title(
        f"CRR Binomial Tree  |  {opt_type.upper()}  K=${K:.0f}  |  "
        f"N={N_d} display steps\n{phase}",
        color="white", fontsize=13,
    )
    ax.tick_params(colors="white", labelcolor="white")
    for sp in ax.spines.values():
        sp.set_edgecolor("#1E293B")

    patches = [
        mpatches.Patch(color="#B45309",  label="Root  t = 0"),
        mpatches.Patch(color="#1E40AF",  label="Stock price"),
        mpatches.Patch(color="#065F46",  label="Hold — continuation value wins"),
        mpatches.Patch(color="#7C3AED",  label="Early exercise — intrinsic value wins"),
    ]
    ax.legend(handles=patches, loc="upper left", fontsize=7,
              facecolor="#1E293B", labelcolor="white", edgecolor="#475569",
              handlelength=1.0, handleheight=0.7, borderpad=0.4, labelspacing=0.3)

    plt.tight_layout()
    return fig


# ── dark-theme matplotlib helper ───────────────────────────────────────────────
def _dark_fig(w=7, h=4):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.tick_params(colors=DESC_BLUE)
    for sp in ax.spines.values():
        sp.set_edgecolor(SKY_BLUE)
        sp.set_alpha(0.45)
    return fig, ax


# ── "About this screen" descriptions for each tab (collapsible expanders) ────
# Each block uses the .about-box CSS class defined in the page-level style.
# Content sourced from CS495_Capstone_Research_Report.pdf and the Project 6 spec.

ABOUT_PRICING = """
<div class='about-box'>
  <p class='section-label'>What this shows.</p>
  <p>The Cox–Ross–Rubinstein American binomial pricer applied to your sidebar contract:
  <strong>Model vs Market</strong> (CRR fair value <code>V_model</code> vs market premium
  <code>V_market</code>), <strong>Convergence</strong> of <code>V_model</code> as lattice
  depth <code>N</code> grows, and the <strong>Early Exercise Boundary</strong>
  <code>S*</code> below which exercising an American put dominates holding.</p>

  <p class='section-label'>Why it matters.</p>
  <p>Pricing accuracy is hypothesis <strong>H1</strong> of the research — every downstream
  decision (edge detection, regime classification, Kelly sizing) assumes <code>V_model</code>
  is calibrated. The boundary panel is the analytic capability that justifies the CRR
  lattice over the closed-form Black–Scholes model for American options.</p>

  <p class='section-label'>Research link.</p>
  <p>Implements <em>§3.4.1 — Layer 1: CRR Pricing Engine</em>, validated in
  <em>§4.2–§4.4</em> of the capstone report. Maps to Project 6's "true <code>p</code>
  estimator" deliverable.</p>
</div>
"""

ABOUT_GREEKS = """
<div class='about-box'>
  <p class='section-label'>What this shows.</p>
  <p>The five standard option Greeks — <strong>Δ</strong> (Delta), <strong>Γ</strong>
  (Gamma), <strong>Θ</strong> (Theta), <strong>ν</strong> (Vega), <strong>ρ</strong>
  (Rho) — plus <strong>σ</strong> (IV, implied volatility input). Greeks are computed via
  centered finite differences over the full <code>N=100</code>-step CRR lattice. The table
  provides plain-English interpretation of each Greek's per-unit effect.</p>

  <p class='section-label'>Why it matters.</p>
  <p>Greeks decompose how the option price responds to changes in spot, volatility, time,
  and interest rates — the standard tool for hedging and risk decomposition. Validating
  model Greeks against the platform-reported Fidelity values (target: ±10% per Greek)
  confirms the lattice's partial derivatives are correctly computed.</p>

  <p class='section-label'>Research link.</p>
  <p>Implements <em>§3.4.2 — Layer 1: Greeks</em>, validated in <em>§4.2.2 — Break-Even
  and Greeks Validation</em>. Supports Project 6's "risk controls" and "decision theory"
  requirements.</p>
</div>
"""

ABOUT_EDGE_SIGNAL = """
<div class='about-box'>
  <p class='section-label'>What this shows.</p>
  <p>The mispricing <strong>edge</strong> = <code>(V_model − V_market) / V_market</code>,
  expressed as a percentage; a categorical <strong>trade signal</strong> (BUY / SELL /
  NO TRADE) gated by the min-edge threshold; and the <strong>volatility regime</strong>
  (NORMAL / HERDING / COMPRESSION) derived from the IV/RV30 ratio. The horizontal gauge
  shows the edge magnitude with the no-trade zone shaded.</p>

  <p class='section-label'>Why it matters.</p>
  <p>This is the bridge from pricing to trading. The regime card surfaces the project's
  central finding: in the <strong>herding regime</strong>, two completely independent
  models (CRR and XGBoost) agree on mispricing direction
  (Pearson <strong>r=0.413, p=2.4×10⁻¹⁰</strong>), while in the normal regime correlation
  is statistically zero — a Simpson's Paradox-type result.</p>

  <p class='section-label'>The Layer-2 XGBoost classifier.</p>
  <p>The CRR engine (Layer 1) is a deterministic no-arbitrage pricer. Layer 2 trains a
  <strong>gradient-boosted decision tree ensemble</strong> (XGBoost 2.0) on 47,578
  historical AAPL contracts (2016–2020) to predict the <em>binary</em> ITM/OTM expiration
  outcome. Crucially, the L2 model uses <strong>realized 30-day volatility (RV30) in place
  of implied volatility</strong> as its volatility feature — making it mathematically and
  informationally independent of Layer 1. XGBoost was chosen over logistic regression
  (too rigid for nonlinear interactions like moneyness × DTE) and neural networks (overkill
  for this dataset size, harder to calibrate). Feature importances by gain:
  <strong>moneyness 38%</strong>, DTE 24%, RV-IV spread 17%, volume/OI ratio 11%, bid-ask
  spread 10%. The classifier is calibrated via <strong>Platt scaling</strong> on a
  held-out validation fold, producing a <strong>Brier score of 0.211</strong> — below the
  0.25 naive baseline (always predict 0.5) and below the market-implied benchmark.</p>

  <p class='section-label'>Cross-validation insight.</p>
  <p>Because L1 and L2 share <em>no inputs and no training signal</em>, their strong
  herding-regime correlation cannot be a calibration artifact. It is direct evidence that
  both models independently detect the same crowd-overpricing bias — the strongest result
  of the research.</p>

  <p class='section-label'>Research link.</p>
  <p>Implements <em>§3.4.3 (Edge)</em>, <em>§3.4.5 (Layer 2 — Independent Probability
  Estimator)</em>, <em>§3.4.6 (Crowd Bias Detector)</em>; cross-validation result in
  <em>§4.7</em>, feature importance in <em>§4.9</em>, Brier validation in
  <em>§4.10.2</em>. Maps to Project 6's "majority bettor / Bet-AI crowd bias detector"
  deliverable.</p>
</div>
"""

ABOUT_KELLY = """
<div class='about-box'>
  <p class='section-label'>What this shows.</p>
  <p>Position sizing recommendations under three variants of the <strong>Kelly
  Criterion</strong>: <strong>Full Kelly</strong> (<code>f* = (p·b − q)/b</code>),
  <strong>Half Kelly</strong> (<code>f*/2</code>), and <strong>Quarter Kelly</strong>
  (<code>f*/4</code>). The bar chart visualizes each fraction as a percentage of capital;
  the table translates fractions into dollar amounts based on your sidebar capital.</p>

  <p class='section-label'>Why it matters.</p>
  <p>The Kelly Criterion (Kelly, 1956; Thorp, 1969) is the mathematically optimal answer to
  "given an edge, how much should I bet?" Full Kelly maximizes long-run growth but exhibits
  high variance; fractional Kelly (MacLean et al., 2010) trades a modest expected-growth
  reduction for substantially lower drawdown — the practical default for any real position
  sizer.</p>

  <p class='section-label'>Layer-2 connection.</p>
  <p>The win probability <code>p</code> used to compute <code>f*</code> can be derived
  either from the CRR edge (Layer 1, the source in this calculator) or from the
  <strong>XGBoost classifier's calibrated probability</strong>
  <code>p̂_model</code> (Layer 2). The classifier provides a <em>direct</em>
  probability estimate rather than an inferred one — useful when the market price diverges
  materially from the model. In the walk-forward backtest, half-Kelly sizing applied to
  L2's calibrated probability produced the <strong>$2.9M cumulative P&amp;L</strong>
  result reported on the Monte Carlo tab.</p>

  <p class='section-label'>Research link.</p>
  <p>Implements <em>§3.4.3 — Mispricing Edge and Kelly Sizing</em>. Tests hypothesis
  <strong>H3</strong> in <em>§4.8</em>: fractional Kelly outperforms full Kelly in
  risk-adjusted backtest.</p>
</div>
"""

ABOUT_MONTE_CARLO = """
<div class='about-box'>
  <p class='section-label'>What this shows.</p>
  <p>A <strong>Monte Carlo simulation</strong> of 1,000 hypothetical trades drawn from the
  empirical edge distribution (seed=42), with cumulative profit-and-loss curves overlaid
  for the three Kelly sizing variants. The summary table reports hit rate, total P&amp;L,
  max drawdown, and the annualized Sharpe ratio for each variant.</p>

  <p class='section-label'>Why it matters.</p>
  <p>A single-trade edge means little; persistent positive expected value across many
  trades is what matters. This Monte Carlo isolates the Layer-1 pipeline's behavior in
  isolation. The full <strong>Layer-1 + Layer-2 walk-forward backtest</strong> — applying
  the CRR pricer, the XGBoost classifier, the regime detector, and the microstructure cost
  filter chronologically to four years of out-of-sample AAPL data — produces
  <strong>$2.9M cumulative P&amp;L</strong> with <strong>max drawdown &lt;15%</strong>,
  the project's headline empirical result.</p>

  <p class='section-label'>Layer-2's role in the backtest.</p>
  <p>XGBoost's calibrated probability <code>p̂_model</code> (Brier 0.211, well-calibrated
  in the 0.3–0.7 range) drives the position-entry filter: only contracts where both L1 and
  L2 agree on direction <em>and</em> exceed the regime-conditional edge threshold trigger
  a trade. The regime detector raises that threshold from 2% to 8% in herding mode,
  throttling the policy to high-conviction trades — which is exactly when the cross-model
  agreement is strongest.</p>

  <p class='section-label'>Research link.</p>
  <p>Implements <em>§3.4.4 — Layer 1: Monte Carlo Simulation</em>; full walk-forward
  result in <em>§4.8 / Figure 7</em>, statistical validation in <em>§4.10.3</em>. Maps to
  Project 6's "backtesting and simulation" deliverable.</p>
</div>
"""

ABOUT_TREE = """
<div class='about-box'>
  <p class='section-label'>What this shows.</p>
  <p>An animated visualization of the <strong>CRR binomial lattice</strong> at a small
  display step count (N=5–12 for clarity; actual pricing uses your sidebar N).
  <strong>Phase 1 (forward)</strong> builds the stock price tree — each node moves up by
  <code>u = e^(σ√Δt)</code> or down by <code>d = 1/u</code>.
  <strong>Phase 2 (backward induction)</strong> replaces stock prices with option values,
  highlighting <strong>early-exercise nodes in purple</strong> where intrinsic value beats
  continuation.</p>

  <p class='section-label'>Why it matters.</p>
  <p>The lattice is the central algorithm of the pricing engine, but normally invisible.
  This animation makes the math transparent and auditable: a user can see exactly how
  <code>V_model</code> is constructed from terminal payoffs back to today.</p>

  <p class='section-label'>Research link.</p>
  <p>Visualizes <em>§2.2 (CRR foundational equations)</em> and <em>§3.4.1 (backward
  induction)</em>. Supports the <strong>transparency</strong> significance argument in
  <em>§1.4</em>.</p>
</div>
"""

# ── tabs (always rendered so the User's Guide is reachable on first load) ─────
tabs = st.tabs(["📈 Pricing", "🔢 Greeks", "🎯 Edge & Signal",
                "💰 Kelly Sizing", "🎲 Monte Carlo", "🌳 Tree Animation",
                "📖 User's Guide"])

# ── User's Guide tab — always populated, independent of Calculate ─────────────
with tabs[6]:
    st.markdown(
        "Full reference manual for the CRR Binomial Pricing Calculator. "
        "Use the download button below for a local copy, or scroll the "
        "embedded viewer to read inline."
    )

    guide_path = Path(__file__).parent / "Users-Guide-CRR-Binomial-Pricing-Calculator.pdf"

    if guide_path.exists():
        pdf_bytes = guide_path.read_bytes()

        st.download_button(
            label="📥  Download User's Guide (PDF)",
            data=pdf_bytes,
            file_name=guide_path.name,
            mime="application/pdf",
            type="primary",
        )

        b64 = base64.b64encode(pdf_bytes).decode()
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{b64}" '
            f'width="100%" height="900" '
            f'style="border:1px solid #334155;border-radius:6px;margin-top:12px"></iframe>',
            unsafe_allow_html=True,
        )
    else:
        st.error(
            f"User's Guide PDF not found at `{guide_path}`. "
            "Ensure the file lives in the same directory as this script."
        )

# ── calculation ────────────────────────────────────────────────────────────────
if run_btn or "results" in st.session_state:

    if run_btn:
        with st.spinner("Pricing …"):
            rv_data    = fetch_rv(ticker)
            mdl_price, boundary = price_american_option(S, K, r, iv, T, int(N), option_type)
            greeks_out = compute_greeks(S, K, r, iv, T, int(N), option_type)

            edge     = (mdl_price - V_market) / V_market
            edge_pct = edge * 100

            # Kelly
            if abs(edge) < min_edge:
                p_win  = 0.50
                fracs  = {"f_full": 0.0, "f_half": 0.0, "f_quarter": 0.0}
                signal = "NO TRADE"
                sig_reason = "Edge is below the minimum threshold — market pricing looks efficient"
            else:
                p_win = _edge_to_win_prob(edge, action)
                fracs = kelly_fractions(p_win)
                if action == "buy" and edge > 0:
                    signal     = "BUY"
                    sig_reason = "Model price > market price — contract appears underpriced"
                elif action == "sell" and edge < 0:
                    signal     = "SELL"
                    sig_reason = "Model price < market price — contract appears overpriced"
                else:
                    signal     = "NO TRADE"
                    sig_reason = "Direction mismatch — edge favours the opposite action"

            # Regime
            rv30 = rv_data["rv30"] if rv_data else None
            if rv30:
                ratio = iv / rv30
                if ratio > 1.2:
                    regime       = "HERDING"
                    regime_color = BURNT_ORG
                    regime_desc  = (f"IV / RV30 = {ratio:.2f}  —  Crowd overbidding inflates "
                                    f"premiums above CRR fair value")
                elif ratio < 0.8:
                    regime       = "COMPRESSION"
                    regime_color = SKY_BLUE
                    regime_desc  = (f"IV / RV30 = {ratio:.2f}  —  Market is underpricing "
                                    f"volatility relative to recent history")
                else:
                    regime       = "NORMAL"
                    regime_color = FOREST
                    regime_desc  = (f"IV / RV30 = {ratio:.2f}  —  Efficient pricing, premiums "
                                    f"reflect historical uncertainty without systemic overbidding")
            else:
                regime       = "UNKNOWN"
                regime_color = SILVER
                regime_desc  = "Could not fetch RV30 — verify ticker symbol and internet connection"

            # Convergence curve
            steps_cv = [5, 10, 25, 50, 100, 150, 200]
            prices_cv = [price_american_option(S, K, r, iv, T, n, option_type)[0]
                         for n in steps_cv]

            # Monte Carlo
            sim_out = {}
            for vname, fkey in [("Full Kelly", "f_full"),
                                 ("Half Kelly", "f_half"),
                                 ("Quarter Kelly", "f_quarter")]:
                fval = fracs[fkey]
                if fval > 0:
                    sim_out[vname] = simulate_pnl(p_win, fval, capital)

            st.session_state["results"] = dict(
                mdl_price=mdl_price, boundary=boundary, greeks=greeks_out,
                edge=edge, edge_pct=edge_pct,
                signal=signal, sig_reason=sig_reason,
                p_win=p_win, fracs=fracs,
                rv30=rv30, rv_data=rv_data,
                regime=regime, regime_color=regime_color, regime_desc=regime_desc,
                steps_cv=steps_cv, prices_cv=prices_cv,
                sim_out=sim_out,
            )

    res       = st.session_state["results"]
    mdl_price = res["mdl_price"]
    greeks_g  = res["greeks"]
    fracs     = res["fracs"]
    p_win     = res["p_win"]
    signal    = res["signal"]
    rv30      = res["rv30"]

    # ════════════════════════════════════════════════════════════════════
    # Tab 1 — Pricing
    # ════════════════════════════════════════════════════════════════════
    with tabs[0]:
        with st.expander("About this screen"):
            st.markdown(ABOUT_PRICING, unsafe_allow_html=True)
        pct_err = (mdl_price - V_market) / V_market * 100
        m1, m2, m3 = st.columns(3)
        m1.metric("CRR Model Price",  f"${mdl_price:.4f}")
        m2.metric("Market Price",      f"${V_market:.4f}")
        m3.metric("% Error",           f"{pct_err:+.2f}%")

        left, right = st.columns(2)

        with left:
            fig, ax = _dark_fig(5, 4)
            bars = ax.bar(["CRR Model", "V_market"], [mdl_price, V_market],
                          color=[NAVY_MID, GOLD], width=0.5)
            for b, v in zip(bars, [mdl_price, V_market]):
                ax.text(b.get_x() + b.get_width() / 2, v + V_market * 0.01,
                        f"${v:.2f}", ha="center", va="bottom",
                        color="white", fontweight="bold", fontsize=10)
            ax.set_ylabel("Price ($)", color=LABEL_BLUE)
            ax.set_title(f"Model vs Market  —  {option_type.upper()}  K=${K:.0f}",
                         color="white")
            ax.yaxis.label.set_color(LABEL_BLUE)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        with right:
            fig, ax = _dark_fig(5, 4)
            ax.plot(res["steps_cv"], res["prices_cv"], "o-", color=SKY_BLUE, lw=2)
            ax.axhline(V_market, color=GOLD, ls="--", lw=1.5,
                       label=f"V_market = ${V_market:.2f}")
            ax.set_xlabel("Steps (N)", color=LABEL_BLUE)
            ax.set_ylabel("CRR Price ($)", color=LABEL_BLUE)
            ax.set_title("CRR Convergence vs Step Count", color="white")
            ax.yaxis.label.set_color(LABEL_BLUE)
            ax.xaxis.label.set_color(LABEL_BLUE)
            ax.legend(facecolor=NAVY_DARK, labelcolor="white",
                      edgecolor=SKY_BLUE, fontsize=9)
            ax.grid(True, alpha=0.2)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        if option_type == "put":
            st.subheader("Early Exercise Boundary")
            boundary = res["boundary"]
            valid    = ~np.isnan(boundary)
            if np.any(valid):
                dt   = T / int(N)
                days = np.arange(int(N) + 1) * dt * 365
                fig, ax = _dark_fig(10, 3.5)
                ax.plot(days[valid], boundary[valid], ".", markersize=2, color=GOLD)
                ax.axhline(S, color=SKY_BLUE, ls="--", lw=1.5,
                           label=f"Current S = ${S:.2f}")
                ax.set_xlabel("Days from today", color=LABEL_BLUE)
                ax.set_ylabel("Critical S* ($)", color=LABEL_BLUE)
                ax.set_title(
                    "Early Exercise Boundary  —  exercise the put when S falls below S*",
                    color="white")
                ax.xaxis.label.set_color(LABEL_BLUE)
                ax.yaxis.label.set_color(LABEL_BLUE)
                ax.legend(facecolor=NAVY_DARK, labelcolor="white",
                          edgecolor=SKY_BLUE, fontsize=9)
                ax.grid(True, alpha=0.2)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

    # ════════════════════════════════════════════════════════════════════
    # Tab 2 — Greeks
    # ════════════════════════════════════════════════════════════════════
    with tabs[1]:
        with st.expander("About this screen"):
            st.markdown(ABOUT_GREEKS, unsafe_allow_html=True)
        g = greeks_g
        g1, g2, g3, g4, g5, g6 = st.columns(6)
        g1.metric("Delta (Δ)", f"{g['delta']:.4f}",
                  help="Change in option price per $1 move in S")
        g2.metric("Gamma (Γ)", f"{g['gamma']:.4f}",
                  help="Change in Delta per $1 move in S")
        g3.metric("Theta (Θ) /day", f"{g['theta']:.4f}",
                  help="Option value decay per calendar day")
        g4.metric("Vega (ν)", f"{g['vega']:.4f}",
                  help="Price change per 1 vol-point (0.01) move in IV")
        g5.metric("Rho (ρ)", f"{g['rho']:.4f}",
                  help="Price change per 100 basis points (bps) change in risk-free rate")
        g6.metric("IV (σ)", f"{iv:.4f}",
                  help="Implied Volatility input — annualized expectation of price variation")

        st.divider()
        greeks_df = pd.DataFrame([
            {"Greek": "Delta (Δ)",   "Value": round(g["delta"], 6),
             "Interpretation": f"${g['delta']:+.4f} per $1 move in underlying"},
            {"Greek": "Gamma (Γ)",   "Value": round(g["gamma"], 6),
             "Interpretation": f"Delta shifts by {g['gamma']:+.4f} per $1 move in underlying"},
            {"Greek": "Theta (Θ)",   "Value": round(g["theta"], 6),
             "Interpretation": f"${g['theta']:+.4f} per calendar day (time decay)"},
            {"Greek": "Vega (ν)",    "Value": round(g["vega"], 6),
             "Interpretation": f"${g['vega']:+.4f} per 1 vol-point (0.01) move in IV"},
            {"Greek": "Rho (ρ)",     "Value": round(g["rho"], 6),
             "Interpretation": f"${g['rho']:+.4f} per 100 basis points (bps) change in r (risk-free rate)"},
            {"Greek": "IV (σ)",      "Value": round(iv, 6),
             "Interpretation": "Implied Volatility — market's annualized expectation of price variation"},
        ])
        st.markdown(
            greeks_df.to_html(index=False, classes="greeks-table", border=0,
                              escape=False),
            unsafe_allow_html=True,
        )

    # ════════════════════════════════════════════════════════════════════
    # Tab 3 — Edge & Signal
    # ════════════════════════════════════════════════════════════════════
    with tabs[2]:
        with st.expander("About this screen"):
            st.markdown(ABOUT_EDGE_SIGNAL, unsafe_allow_html=True)
        e1, e2, e3 = st.columns(3)
        e1.metric("Edge", f"{res['edge_pct']:+.3f}%")
        e2.metric("IV",   f"{iv:.2%}")
        e3.metric("RV30", f"{rv30:.2%}" if rv30 else "N/A")

        # ── Signal banner — compact size matching the regime card ─────────
        sig_colors = {"BUY": FOREST, "NO TRADE": SILVER, "SELL": NAVY_MID}
        st.markdown(
            f"<div style='padding:14px;border-radius:8px;margin:8px 0;"
            f"background:{sig_colors.get(signal, SILVER)};text-align:center'>"
            f"<strong style='color:white;font-size:1.05rem'>{signal}</strong><br>"
            f"<span style='color:{DESC_BLUE}'>{res['sig_reason']}</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        # ── Edge gauge bar (now between banner and regime card) ───────────
        fig, ax = _dark_fig(10, 4.2)
        ep = res["edge_pct"]
        ax.barh(["Edge"], [ep],
                color=DEEP_RED if ep < 0 else FOREST, height=0.35)
        min_line = ax.axvline(-min_edge * 100, color=GOLD, ls="--", lw=1.5,
                              label=f"Min edge ± {min_edge*100:.1f}%")
        ax.axvline( min_edge * 100, color=GOLD, ls="--", lw=1.5)
        nt_zone = ax.axvspan(-min_edge * 100, min_edge * 100,
                             color="#7C3AED", alpha=0.30,
                             label="NO-TRADE zone")
        ax.set_xlabel("Edge %")
        legend_handles = [
            mpatches.Patch(facecolor=FOREST,   label="Positive edge (undervalued)"),
            mpatches.Patch(facecolor=DEEP_RED, label="Negative edge (overvalued)"),
            min_line,
            nt_zone,
        ]
        # Legend below the chart so it doesn't overlap the bar
        ax.legend(handles=legend_handles, facecolor=NAVY_DARK, labelcolor="white",
                  edgecolor=SKY_BLUE, fontsize=9, ncol=2,
                  loc="upper center", bbox_to_anchor=(0.5, -0.30),
                  frameon=True)
        # Axis labels + tick labels → white (per user)
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        for lbl in ax.get_xticklabels() + ax.get_yticklabels():
            lbl.set_color("white")
        plt.subplots_adjust(bottom=0.28)
        st.pyplot(fig)
        plt.close()

        # ── Regime card — now below the plot (per user) ───────────────────
        if rv30:
            rc = res["regime_color"]
            icon = "⚡" if res["regime"] == "HERDING" else ""
            st.markdown(
                f"<div style='padding:14px;border-radius:8px;margin:8px 0;"
                f"background:{rc};"
                f"display:flex;justify-content:space-between;align-items:center'>"
                f"<div>"
                f"<strong style='color:white;font-size:1.05rem'>"
                f"{res['regime']} REGIME</strong><br>"
                f"<span style='color:white'>{res['regime_desc']}</span>"
                f"</div>"
                f"<div style='font-size:28px;color:{GOLD};font-weight:bold;"
                f"padding-left:12px'>{icon}</div>"
                "</div>",
                unsafe_allow_html=True,
            )

    # ════════════════════════════════════════════════════════════════════
    # Tab 4 — Kelly Sizing
    # ════════════════════════════════════════════════════════════════════
    with tabs[3]:
        with st.expander("About this screen"):
            st.markdown(ABOUT_KELLY, unsafe_allow_html=True)
        st.metric("Win Probability (p_win)", f"{p_win:.4f}",
                  help="Derived from CRR edge: p = clip(0.5 + edge/2, 0.01, 0.99)")

        # ── Bar chart FIRST (plot above table per user) ─────────────────
        fig, ax = _dark_fig(8, 3.5)
        variants = ["Full Kelly", "Half Kelly", "Quarter Kelly"]
        vals     = [fracs["f_full"] * 100, fracs["f_half"] * 100, fracs["f_quarter"] * 100]
        bars = ax.bar(variants, vals,
                      color=[FOREST, NAVY_MID, GOLD], width=0.45)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.002,
                    f"{v:.2f}%", ha="center", va="bottom",
                    color="white", fontweight="bold")
        ax.set_ylabel("Fraction of Capital (%)", color=GOLD)
        ax.set_title("Kelly Position Sizing  —  f* = (p·b − q) / b", color="white")
        ax.yaxis.label.set_color(GOLD)
        ax.xaxis.label.set_color(GOLD)
        for lbl in ax.get_xticklabels() + ax.get_yticklabels():
            lbl.set_color(GOLD)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # ── Kelly fractions table BELOW the plot, styled like Greeks ─────
        kelly_rows = []
        for vname, fkey in [("Full Kelly", "f_full"),
                             ("Half Kelly", "f_half"),
                             ("Quarter Kelly", "f_quarter")]:
            fv = fracs[fkey]
            kelly_rows.append({
                "Variant":        vname,
                "Fraction (f*)":  f"{fv:.4f}",
                "% of Capital":   f"{fv*100:.2f}%",
                "Dollar Amount":  f"${fv * capital:,.2f}",
                "Trade Signal":   signal,
            })
        kelly_df = pd.DataFrame(kelly_rows)
        st.markdown(
            kelly_df.to_html(index=False, classes="greeks-table", border=0,
                             escape=False),
            unsafe_allow_html=True,
        )

        if all(fracs[k] == 0 for k in ["f_full", "f_half", "f_quarter"]):
            st.info(
                "All Kelly fractions = 0  —  edge is below the minimum threshold. "
                "No position recommended."
            )

    # ════════════════════════════════════════════════════════════════════
    # Tab 5 — Monte Carlo
    # ════════════════════════════════════════════════════════════════════
    with tabs[4]:
        with st.expander("About this screen"):
            st.markdown(ABOUT_MONTE_CARLO, unsafe_allow_html=True)
        sim_out = res["sim_out"]
        if not sim_out:
            st.info(
                "No simulation to run — all Kelly fractions are 0 (NO TRADE). "
                "Increase edge or lower the min_edge threshold to see results."
            )
        else:
            vcols = {"Full Kelly":    FOREST,
                     "Half Kelly":    NAVY_MID,
                     "Quarter Kelly": GOLD}

            fig, ax = _dark_fig(10, 4.5)
            for vname, stats in sim_out.items():
                ax.plot(stats["cum_pnl"],
                        color=vcols.get(vname, "gray"), lw=1.5,
                        label=f"{vname}  (Sharpe = {stats['sharpe_annualized']:.2f})")
            ax.axhline(0, color="white", lw=0.8, alpha=0.35)
            ax.set_xlabel("Trades", color="white")
            ax.set_ylabel("Cumulative Profit and Loss ($)", color="white")
            ax.set_title(
                f"Monte Carlo Profit and Loss Simulation  —  1 000 trades  |  p_win = {p_win:.3f}",
                color="white")
            ax.xaxis.label.set_color("white")
            ax.yaxis.label.set_color("white")
            for lbl in ax.get_xticklabels() + ax.get_yticklabels():
                lbl.set_color("white")
            ax.legend(facecolor=NAVY_DARK, labelcolor="white",
                      edgecolor=SKY_BLUE, fontsize=9)
            ax.grid(True, alpha=0.15)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            sim_rows = []
            for vname, stats in sim_out.items():
                sim_rows.append({
                    "Variant":       vname,
                    "Hit Rate":      f"{stats['hit_rate']:.2%}",
                    "Total P&L":     f"${stats['total_pnl']:,.2f}",
                    "Max Drawdown":  f"${stats['max_drawdown']:,.2f}",
                    "Ann. Sharpe":   f"{stats['sharpe_annualized']:.3f}",
                })
            sim_df = pd.DataFrame(sim_rows)
            st.markdown(
                sim_df.to_html(index=False, classes="greeks-table", border=0,
                               escape=False),
                unsafe_allow_html=True,
            )

    # ════════════════════════════════════════════════════════════════════
    # Tab 6 — Tree Animation
    # ════════════════════════════════════════════════════════════════════
    with tabs[5]:
        with st.expander("About this screen"):
            st.markdown(ABOUT_TREE, unsafe_allow_html=True)
        st.markdown(
            f"Displaying **N = {N_disp}** step tree for illustration  "
            f"_(actual pricing uses N = {int(N)})_"
        )
        st.caption(
            "Gold = root  ·  Blue = stock price  ·  "
            "Green = hold (continuation wins)  ·  Purple = early exercise (intrinsic wins)"
        )

        anim_btn    = st.button("▶  Animate Tree", type="primary")
        tree_slot   = st.empty()

        stock_t, option_t, early_t = _build_display_tree(
            S, K, r, iv, T, N_disp, option_type
        )

        if anim_btn:
            # Phase 1 — forward: reveal stock price nodes left → right
            for fwd in range(N_disp + 1):
                fig = _draw_tree(stock_t, option_t, early_t, N_disp,
                                 fwd_up_to=fwd, bwd_from=N_disp + 1,
                                 opt_type=option_type)
                tree_slot.pyplot(fig)
                plt.close()
                time.sleep(anim_speed)

            # Phase 2 — backward: flip to option values right → left
            for bwd in range(N_disp, -1, -1):
                fig = _draw_tree(stock_t, option_t, early_t, N_disp,
                                 fwd_up_to=N_disp, bwd_from=bwd,
                                 opt_type=option_type)
                tree_slot.pyplot(fig)
                plt.close()
                time.sleep(anim_speed)
        else:
            # Static view — full stock price tree
            fig = _draw_tree(stock_t, option_t, early_t, N_disp,
                             fwd_up_to=N_disp, bwd_from=N_disp + 1,
                             opt_type=option_type)
            tree_slot.pyplot(fig)
            plt.close()

else:
    # No results yet — leave the User's Guide tab populated and drop a
    # placeholder into each of the six calculation tabs.
    for i in range(6):
        with tabs[i]:
            st.info(
                "Enter your contract parameters in the sidebar and click "
                "**Calculate** to populate this tab."
            )
