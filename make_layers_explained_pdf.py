from fpdf import FPDF
import os

OUT   = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "CRR-Pipeline-Layers-Explained.pdf")

TITLE  = "CRR-Pipeline-Layers-Explained"
GITHUB = "github.com/dantzlerdc/CS495-Deep-Scholar"

# ── Colors ────────────────────────────────────────────────────────────────────
HDR_BG   = (26,  58, 109)
BLUE_TTL = (37,  99, 235)
L1_BG    = (20,  83,  45)   # dark green -- Layer 1
L2_BG    = (124,  58, 160)  # purple     -- Layer 2
SHARED   = (37,  99, 200)   # blue       -- shared concepts
CODE_BG  = (240, 242, 245)
CODE_TXT = (45,  50,  60)
BODY_TXT = (25,  25,  25)
GRAY_FT  = (110, 110, 110)
TBL_HDR  = (26,  58, 109)
TBL_R1   = (240, 244, 252)
TBL_R2   = (255, 255, 255)
WHITE    = (255, 255, 255)


class PDF(FPDF):
    def header(self):
        self.set_fill_color(*HDR_BG)
        self.rect(0, 0, 210, 13, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        self.set_xy(6, 2.5)
        self.cell(0, 8, TITLE)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY_FT)
        self.cell(0, 10, f"Page {self.page_no()} | {GITHUB}", align="C")


def h1(pdf, text):
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*BLUE_TTL)
    pdf.cell(0, 9, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def h2(pdf, text, color=HDR_BG):
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*color)
    pdf.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")


def body(pdf, text):
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*BODY_TXT)
    pdf.multi_cell(0, 5.5, text, align="J")
    pdf.ln(1)


def bullet(pdf, items, color=BODY_TXT):
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*color)
    for item in items:
        pdf.set_x(18)
        pdf.multi_cell(0, 5.5, "- " + item, align="L")
    pdf.ln(1)


def layer_card(pdf, layer_num, label, bg, tagline, items):
    pdf.set_fill_color(*bg)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"  {layer_num}  {label}",
             new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*bg)
    pdf.cell(0, 5, tagline, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    bullet(pdf, items)
    pdf.ln(2)


def module_row(pdf, module, description, output, layer_col):
    pdf.set_fill_color(*layer_col)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(42, 7, "  " + module, border=1, fill=True)
    pdf.set_fill_color(*TBL_R1)
    pdf.set_text_color(*BODY_TXT)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.cell(88, 7, description, border=1, fill=True)
    pdf.cell(50, 7, output, border=1, fill=True)
    pdf.ln()


def comparison_table(pdf):
    hdrs   = ["",               "Layer 1",                      "Layer 2"]
    widths = [42, 74, 74]

    pdf.set_fill_color(*TBL_HDR)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    for text, w in zip(hdrs, widths):
        pdf.cell(w, 7, text, border=1, fill=True)
    pdf.ln()

    rows = [
        ("p comes from",
         "CRR no-arbitrage formula",
         "XGBoost trained on 5 yrs of AAPL data"),
        ("q comes from",
         "AMD market bid-ask mid",
         "AAPL bid-ask mid at each historical date"),
        ("Data",
         "4 AMD contracts (one moment in time)",
         "47,578 AAPL rows (2016-2020)"),
        ("Method",
         "Mathematical / no-arbitrage",
         "Machine learning / empirical"),
        ("Edge signal",
         "(V_model - V_market) / V_market",
         "p_independent - q_market after costs"),
        ("Sizing",
         "Full / half / quarter Kelly",
         "Quarter Kelly (backtest conservatism)"),
        ("Risk controls",
         "VaR limit, drawdown halt",
         "VaR 5%, drawdown halt 15%"),
        ("Output",
         "Greeks, edge, kelly.csv, simulation.csv",
         "call/put_model.pkl, pnl_curve.png, trades.csv"),
    ]

    for i, (label, l1, l2) in enumerate(rows):
        bg = TBL_R1 if i % 2 == 0 else TBL_R2
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*HDR_BG)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.cell(widths[0], 7, label, border=1, fill=True)
        pdf.set_text_color(*BODY_TXT)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.cell(widths[1], 7, l1, border=1, fill=True)
        pdf.set_text_color(*L2_BG)
        pdf.cell(widths[2], 7, l2, border=1, fill=True)
        pdf.ln()
    pdf.ln(3)


# ── Build PDF ─────────────────────────────────────────────────────────────────
pdf = PDF(orientation="P", unit="mm", format="A4")
pdf.set_auto_page_break(auto=True, margin=18)
pdf.set_margins(15, 18, 15)

# ── Page 1 ────────────────────────────────────────────────────────────────────
pdf.add_page()
pdf.ln(6)
pdf.set_font("Helvetica", "B", 20)
pdf.set_text_color(*HDR_BG)
pdf.multi_cell(0, 10, "CRR Pipeline Layers Explained", align="C")
pdf.ln(3)
pdf.set_font("Helvetica", "I", 11)
pdf.set_text_color(*BLUE_TTL)
pdf.multi_cell(0, 6,
    "Two parallel pipelines -- same conceptual framework, different methods and data",
    align="C")
pdf.ln(8)

h1(pdf, "Overview")
body(pdf,
    "The Deep Scholar project has two layers that share the same core concept -- "
    "edge = p - q and Kelly position sizing -- but they are independent pipelines "
    "that arrive at p using completely different approaches. Layer 2 does NOT build "
    "on top of Layer 1; they are parallel implementations of the same economic idea.")
pdf.ln(2)

# Shared concept highlight box
pdf.set_fill_color(230, 240, 255)
pdf.set_draw_color(*SHARED)
pdf.rect(15, pdf.get_y(), 180, 22, "DF")
pdf.set_xy(20, pdf.get_y() + 3)
pdf.set_font("Helvetica", "B", 10)
pdf.set_text_color(*SHARED)
pdf.cell(0, 6, "Shared Concept in Both Layers:", new_x="LMARGIN", new_y="NEXT")
pdf.set_x(20)
pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(*BODY_TXT)
pdf.multi_cell(170, 5.5,
    "edge = p - q  |  Trade when edge > transaction costs  |  "
    "Size with Kelly criterion  |  Halt on drawdown limit")
pdf.ln(10)

layer_card(pdf, "Layer 1", "CRR Theoretical Pricing Pipeline", L1_BG,
    "One AMD contract snapshot -- mathematical / no-arbitrage",
    [
        "Builds the CRR binomial tree to compute V_model (theoretical fair price)",
        "Computes Greeks: delta, gamma, theta, vega from the tree",
        "Computes mispricing edge = (V_model - V_market) / V_market",
        "Sizes the position with full / half / quarter Kelly criterion",
        "Runs Monte Carlo simulation of P&L over many paths",
        "Data: 4 AMD contracts from a single moment in time (Fidelity tickets)",
        "Method: Mathematical -- CRR no-arbitrage formula",
    ])

layer_card(pdf, "Layer 2", "ML Empirical Pricing Pipeline", L2_BG,
    "5 years of AAPL historical options data -- machine learning / empirical",
    [
        "Does NOT use the CRR binomial tree",
        "Trains XGBoost to estimate p_independent (probability option expires ITM)",
        "Detects herding regimes from RV-IV spread (bias_detector.py)",
        "Subtracts real transaction costs to get net edge (micro_cost.py)",
        "Calibrates model probabilities with Platt scaling (calibration.py)",
        "Applies regime-conditional trade policy: normal 2%, herding 8% min edge",
        "Runs walk-forward backtest: 12-month train, 3-month test windows",
        "Data: 47,578 AAPL rows (2016-2020) -- historical outcomes",
        "Method: Machine learning -- XGBoost + Platt scaling calibration",
    ])

# ── Page 2 ────────────────────────────────────────────────────────────────────
pdf.add_page()
h1(pdf, "How Each Layer Computes p and q")

h2(pdf, "Layer 1: p from the CRR Formula", L1_BG)
pdf.ln(1)
body(pdf,
    "The CRR risk-neutral probability p* is derived mathematically from the no-arbitrage "
    "condition. It is not a forecast -- it is the unique probability that makes the "
    "discounted option price a martingale:")
pdf.set_fill_color(*CODE_BG)
pdf.set_font("Courier", "", 9)
pdf.set_text_color(*CODE_TXT)
for line in [
    "u = exp(sigma * sqrt(dt))       # up factor",
    "d = 1 / u                        # down factor",
    "p* = (exp(r*dt) - d) / (u - d)  # risk-neutral probability",
    "V_model = backward_induction(p*, u, d, K, S0, N)",
    "edge = (V_model - V_market) / V_market",
]:
    pdf.set_x(15)
    pdf.cell(0, 5.5, "  " + line, new_x="LMARGIN", new_y="NEXT", fill=True)
pdf.ln(3)

h2(pdf, "Layer 2: p from XGBoost Trained on Historical Outcomes", L2_BG)
pdf.ln(1)
body(pdf,
    "p_independent is an empirical estimate of the physical probability the option "
    "expires in the money, trained on 5 years of actual AAPL expiration outcomes. "
    "It is NOT derived from the no-arbitrage formula:")
pdf.set_fill_color(*CODE_BG)
pdf.set_font("Courier", "", 9)
pdf.set_text_color(*CODE_TXT)
for line in [
    "features = [moneyness, log_dte, IV, RV30,",
    "            rv_iv_spread, half_spread, log_volume]",
    "label    = 1 if option expired ITM else 0   # historical outcome",
    "",
    "model = XGBoost + CalibratedClassifierCV(cv=3, method='sigmoid')",
    "model.fit(X_train, y_train)   # 38,062 training rows",
    "",
    "p_independent = model.predict_proba(X_test)[:, 1]",
    "q_market      = option_mid / strike   # market-implied probability proxy",
    "raw_edge      = p_independent - q_market",
    "net_edge      = raw_edge - transaction_costs",
]:
    pdf.set_x(15)
    pdf.cell(0, 5.5, "  " + line, new_x="LMARGIN", new_y="NEXT", fill=True)
pdf.ln(4)

h1(pdf, "Side-by-Side Comparison")
pdf.ln(1)
comparison_table(pdf)

h2(pdf, "Key Insight: Same Question, Different Answers", SHARED)
pdf.ln(1)
body(pdf,
    "Both layers ask: 'Is the market pricing this option correctly?' Layer 1 answers "
    "using the theoretical no-arbitrage price -- if the market deviates from what the "
    "CRR formula says it should cost, there is an edge. Layer 2 answers using historical "
    "evidence -- if the ML model's predicted ITM probability differs from what the market "
    "implies, there is an edge. They are two independent methods of finding the same thing.")

# ── Page 3 ────────────────────────────────────────────────────────────────────
pdf.add_page()
h1(pdf, "Module Reference: What Each File Produces")
pdf.ln(1)

# Header row
pdf.set_fill_color(*TBL_HDR)
pdf.set_text_color(*WHITE)
pdf.set_font("Helvetica", "B", 9)
pdf.cell(42, 7, "Module", border=1, fill=True)
pdf.cell(88, 7, "What it does", border=1, fill=True)
pdf.cell(50, 7, "Key output", border=1, fill=True)
pdf.ln()

l1_modules = [
    ("data.py",       "Loads AMD contract params from config.yaml",       "S, K, r, sigma, T, N"),
    ("tree.py",       "Builds CRR binomial lattice, backward induction",  "V_model (fair price)"),
    ("greeks.py",     "Numerical Greeks from tree perturbation",           "delta, gamma, theta, vega"),
    ("edge.py",       "Mispricing: (V_model - V_market) / V_market",      "edges.csv"),
    ("kelly.py",      "f* = (p*b - q) / b position sizing",               "kelly.csv"),
    ("simulation.py", "Monte Carlo P&L simulation over many paths",       "simulation.csv, plots"),
]

l2_modules = [
    ("market_data.py",  "Load AAPL CSV, compute RV30, label ITM/OTM",      "Prepared DataFrame"),
    ("p_estimator.py",  "Train XGBoost + Platt scaling on ITM outcomes",   "call/put_model.pkl"),
    ("bias_detector.py","RV-IV spread, iv_mom, regime classification",     "regime_analysis.png"),
    ("micro_cost.py",   "Round-trip cost: spread + fee + slippage",        "net_edge per trade"),
    ("calibration.py",  "Brier score, ECE, reliability diagram",           "calibration_curve.png"),
    ("policy.py",       "Regime-gated TRADE / NO TRADE decision",          "Signal + Kelly sizing"),
    ("backtest.py",     "Walk-forward 12-mo train / 3-mo test windows",    "pnl_curve.png, trades.csv"),
]

for module, desc, output in l1_modules:
    module_row(pdf, module, desc, output, L1_BG)

pdf.set_fill_color(230, 230, 230)
pdf.set_text_color(*BODY_TXT)
pdf.set_font("Helvetica", "BI", 8)
pdf.cell(180, 5, "  -- Layer 2 modules below --", border=0, fill=True)
pdf.ln()

for module, desc, output in l2_modules:
    module_row(pdf, module, desc, output, L2_BG)

pdf.ln(4)
h1(pdf, "Potential Integration Point (Not Yet Implemented)")
body(pdf,
    "The two layers are currently independent. One natural extension would be to use "
    "the CRR model price as an additional feature inside the Layer 2 XGBoost model -- "
    "feeding the theoretical edge (V_model - V_market) / V_market as a feature column "
    "alongside moneyness, IV, and RV. This would let the ML model learn when the "
    "no-arbitrage signal is more or less reliable depending on market regime. "
    "As built today, Layer 1 runs on AMD data and Layer 2 runs on AAPL data; "
    "integrating them would require a common dataset with both theoretical and "
    "empirical signals computed for the same contracts.")

pdf.output(OUT)
print(f"Saved -> {OUT}")
