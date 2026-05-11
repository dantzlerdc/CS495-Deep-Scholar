from fpdf import FPDF
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "CRR-Binomial-Pricing-Build-Sequence.pdf")

TITLE    = "CRR-Binomial-Pricing-Build-Sequence"
SUBTITLE = "PLAN2.md -- Layer 1 (Done) and Layer 2 (New) Implementation Guide"
GITHUB   = "github.com/dantzlerdc/CS495-Deep-Scholar"

# ── Colors ────────────────────────────────────────────────────────────────────
HDR_BG    = (26,  58, 109)
BLUE_TTL  = (37,  99, 235)
BLUE_IT   = (29, 100, 200)
STEP_BG   = (37,  99, 200)
DONE_BG   = (20,  83,  45)   # dark green -- Layer 1 (done)
NEW_BG    = (124,  58, 160)  # purple -- Layer 2 (new)
CODE_BG   = (240, 242, 245)
CODE_TXT  = (45,  50,  60)
BODY_TXT  = (25,  25,  25)
GRAY_FT   = (110, 110, 110)
TBL_HDR   = (26,  58, 109)
TBL_R1    = (240, 244, 252)
TBL_R2    = (255, 255, 255)
WHITE     = (255, 255, 255)
GOLD      = (180, 130,  10)
GREEN_TXT = (20,  83,  45)


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


def section_head(pdf, text):
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*BODY_TXT)
    pdf.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")


def body(pdf, text):
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*BODY_TXT)
    pdf.multi_cell(0, 5.5, text, align="J")
    pdf.ln(1)


def bullet(pdf, text):
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*BODY_TXT)
    pdf.set_x(18)
    pdf.multi_cell(0, 5.5, "- " + text, align="L")


def code_block(pdf, lines):
    pdf.set_fill_color(*CODE_BG)
    pdf.set_font("Courier", "", 8.5)
    pdf.set_text_color(*CODE_TXT)
    for line in lines:
        if line == "":
            pdf.ln(2)
        else:
            pdf.set_x(15)
            pdf.cell(0, 5.5, "  " + line, new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(2)


def kv(pdf, label, value, label_col=(37, 99, 235), val_col=(25, 25, 25)):
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*label_col)
    pdf.cell(42, 6, label)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*val_col)
    pdf.multi_cell(0, 6, value)


def step_card(pdf, step_num, module, tagline, layer_done, what, depends, note=None):
    """Render one build-step card."""
    # Card header bar -- color indicates layer
    bg = DONE_BG if layer_done else NEW_BG
    tag = "Layer 1 -- Already Built" if layer_done else "Layer 2 -- New"
    pdf.set_fill_color(*bg)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 9, f"  {step_num}  {module}", new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(1)

    # Tag line (italic)
    pdf.set_font("Helvetica", "BI", 9)
    pdf.set_text_color(*bg)
    pdf.cell(0, 5, tagline, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Status badge
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*bg)
    pdf.cell(22, 5.5, "Status: ")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*BODY_TXT)
    pdf.cell(0, 5.5, tag, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    section_head(pdf, "What it does")
    body(pdf, what)

    section_head(pdf, "Depends on")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*BODY_TXT)
    pdf.multi_cell(0, 5.5, depends)
    pdf.ln(1)

    if note:
        pdf.set_fill_color(*CODE_BG)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(80, 60, 20)
        pdf.set_x(15)
        pdf.multi_cell(0, 5.5, "  Note: " + note, fill=True)
        pdf.ln(1)

    pdf.ln(3)


def make_pdf():
    pdf = PDF()
    pdf.set_margins(15, 22, 15)
    pdf.set_auto_page_break(True, margin=18)

    # ── Page 1: Overview ──────────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*BLUE_TTL)
    pdf.cell(0, 10, TITLE, new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, SUBTITLE, new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 5, GITHUB, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    pdf.set_draw_color(190, 195, 210)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)

    # Color key
    section_head(pdf, "Color Key")
    pdf.set_fill_color(*DONE_BG)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(55, 6, "  Layer 1 -- Already Built", fill=True)
    pdf.cell(5, 6, "")
    pdf.set_fill_color(*NEW_BG)
    pdf.cell(55, 6, "  Layer 2 -- New (to build)", fill=True)
    pdf.ln(5)

    # Overview paragraph
    section_head(pdf, "Overview")
    body(pdf,
        "PLAN2.md defines a two-layer pipeline. Layer 1 (the CRR pricing engine) is "
        "fully implemented -- all six stages run today via 'make run'. Layer 2 adds the "
        "components required by Project 6 that are absent from the original pipeline: an "
        "independent probability estimator, a crowd bias/regime detector, a microstructure "
        "cost model, probability calibration, a trade policy engine, and a walk-forward "
        "backtest runner. Build Layer 2 in the step order below -- each module depends on "
        "the one before it."
    )

    # Build order summary table
    section_head(pdf, "Recommended Build Order")
    col_w = [18, 48, 40, 74]
    headers = ["Step", "Module", "Status", "Purpose"]
    rows = [
        ("0", "make run",          "Done",    "Confirm Layer 1 pipeline executes end-to-end"),
        ("1", "market_data.py",    "New",     "Layer 2 data feed: IV surface, volume, OI, spread"),
        ("2", "p_estimator.py",    "New",     "ML independent probability model (core gap)"),
        ("3", "bias_detector.py",  "New",     "Regime classifier: normal vs. herding crowd"),
        ("4", "micro_cost.py",     "New",     "Fee / spread / slippage cost filter"),
        ("5", "calibration.py",    "New",     "Brier score + calibration curve validation"),
        ("6", "policy.py",         "New",     "Combined regime-conditional trade decision"),
        ("7", "backtest.py",       "New",     "Walk-forward historical backtest + dashboard plots"),
    ]

    pdf.set_fill_color(*TBL_HDR)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border=1, fill=True)
    pdf.ln()

    for idx, (step, mod, status, purpose) in enumerate(rows):
        is_done = status == "Done"
        pdf.set_fill_color(*(TBL_R1 if idx % 2 == 0 else TBL_R2))
        pdf.set_text_color(*BODY_TXT)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(col_w[0], 6.5, step, border=1, fill=True)
        pdf.set_font("Courier", "", 9)
        pdf.cell(col_w[1], 6.5, mod, border=1, fill=True)
        pdf.set_font("Helvetica", "B", 9)
        txt_col = GREEN_TXT if is_done else NEW_BG
        pdf.set_text_color(*txt_col)
        pdf.cell(col_w[2], 6.5, status, border=1, fill=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*BODY_TXT)
        pdf.cell(col_w[3], 6.5, purpose, border=1, fill=True)
        pdf.ln()

    pdf.ln(4)

    # Prerequisites
    section_head(pdf, "Prerequisites Before Starting Layer 2")
    prereqs = [
        ("Historical option chain data",
         "p_estimator.py needs labeled ITM/OTM outcomes. Use the Kaggle AAPL "
         "dataset (kylegraupe/aapl-options-data-2016-2020) as a proxy if live AMD "
         "history is unavailable. Document the substitution in the report."),
        ("scikit-learn and XGBoost installed",
         "Run: .venv/bin/python3 -m pip install scikit-learn xgboost lightgbm"),
        ("Layer 1 passing cleanly",
         "The backtest uses CRR pricing as a comparison benchmark. tree.py must "
         "produce V_model within 0.005% of V_market before Layer 2 begins."),
    ]
    for label, desc in prereqs:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*BLUE_TTL)
        pdf.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
        body(pdf, desc)

    # ── Pages 2-9: One step per page ──────────────────────────────────────────
    pdf.add_page()
    pdf.ln(10)

    step_card(
        pdf,
        step_num="Step 0",
        module="make run  (Layer 1 verification)",
        tagline="Confirm all six CRR pipeline stages execute before starting Layer 2.",
        layer_done=True,
        what=(
            "Runs the full six-stage CRR pipeline end-to-end: data ingestion (data.py), "
            "CRR pricing (tree.py), Greeks (greeks.py), mispricing edge (edge.py), Kelly "
            "sizing (kelly.py), and Monte Carlo simulation (simulation.py). All outputs "
            "are written to project/outputs/ as CSV files and PNG plots. If this command "
            "completes without errors, Layer 1 is your foundation and Layer 2 build can begin."
        ),
        depends=(
            "config.yaml -- AMD option chain parameters (S, K, r, IV, T, N)\n"
            ".venv active -- all Layer 1 dependencies installed via 'make setup'"
        ),
        note="Run from the repo root. If it fails, fix Layer 1 before touching Layer 2.",
    )

    code_block(pdf, [
        "make setup   # first-time only: create .venv and install dependencies",
        "make run     # execute all six pipeline stages",
    ])

    pdf.add_page()
    pdf.ln(10)

    step_card(
        pdf,
        step_num="Step 1",
        module="market_data.py",
        tagline="Layer 2 data feed -- IV surface, volume, open interest, bid-ask spread.",
        layer_done=False,
        what=(
            "Fetches the additional market data that Layer 2 needs but Layer 1 does not "
            "collect: the full implied volatility surface across multiple strikes and "
            "expiries, option volume, open interest, and bid-ask spread. These are the raw "
            "inputs for the probability estimator (Step 2), the regime detector (Step 3), "
            "and the microstructure cost model (Step 4). All data is appended to the "
            "existing pandas DataFrame produced by data.py."
        ),
        depends=(
            "data.py -- existing Layer 1 data module (market_data.py extends it)\n"
            "yfinance -- already installed; no new dependencies needed for this step"
        ),
        note=(
            "Everything else in Layer 2 depends on this module. Build and validate it "
            "before writing any other Layer 2 code."
        ),
    )

    section_head(pdf, "Key Functions to Implement")
    code_block(pdf, [
        "fetch_iv_surface(ticker, expiries)   -- returns IV grid (strike x expiry)",
        "fetch_volume_oi(ticker, expiry)      -- returns volume and open interest per strike",
        "fetch_bid_ask_spread(ticker, expiry) -- returns mid-price and half-spread per strike",
        "build_layer2_df(cfg, base_df)        -- merges all Layer 2 features into one DataFrame",
    ])

    pdf.add_page()
    pdf.ln(10)

    step_card(
        pdf,
        step_num="Step 2",
        module="p_estimator.py",
        tagline="Independent ML probability model -- the core gap from PLAN.md.",
        layer_done=False,
        what=(
            "Trains a gradient boosting classifier (XGBoost or LightGBM) on historical "
            "option outcomes. Each training example is a historical option contract; the "
            "label is 1 (expired ITM) or 0 (expired OTM). Features include moneyness "
            "(S/K), days-to-expiry, the RV-IV spread, volume/OI ratio, and bid-ask spread. "
            "The model outputs p_independent -- a probability that does NOT use the market "
            "price as an input. This is what makes it a genuine independent predictor. "
            "After training, Platt scaling or isotonic regression is applied so that "
            "p_independent=0.70 actually means the option expires ITM 70% of the time. "
            "The calibrated output feeds directly into edge_independent = p_independent - q_market."
        ),
        depends=(
            "market_data.py -- for feature data (Step 1 must be complete)\n"
            "Historical labeled data -- Kaggle AAPL dataset or AMD chain snapshots\n"
            "scikit-learn, XGBoost/LightGBM -- install before this step"
        ),
        note=(
            "This is the most important new module. The original CRR pipeline has "
            "edge ~ 0% because IV is solved FROM the market price. p_estimator.py breaks "
            "that circularity by forecasting p from features, not from market IV."
        ),
    )

    section_head(pdf, "Key Functions to Implement")
    code_block(pdf, [
        "build_features(df)                   -- engineers feature matrix from Layer 2 DataFrame",
        "train_p_model(X_train, y_train)       -- fits gradient boosting; returns model",
        "calibrate_p(model, X_cal, y_cal)      -- Platt scaling / isotonic regression",
        "predict_p_independent(model, X)       -- returns calibrated p_independent per ticket",
        "compute_edge_independent(p, q_market) -- returns edge_independent = p - q_market",
    ])

    pdf.add_page()
    pdf.ln(10)

    step_card(
        pdf,
        step_num="Step 3",
        module="bias_detector.py",
        tagline="Crowd regime classifier -- normal vs. herding market conditions.",
        layer_done=False,
        what=(
            "Computes behavioral bias indicators from the IV surface and volume data, then "
            "classifies each trading day into one of two regimes. "
            "Normal regime: the crowd is approximately rational; IV tracks realized volatility "
            "closely; trade any edge above the 2% minimum threshold. "
            "Herding regime: the crowd is systematically biased; IV is detached from RV; "
            "vol premium is large and persistent; raise the minimum edge threshold to 8% "
            "and trade only high-conviction signals. "
            "Three primary indicators are used: (1) RV-IV spread -- the difference between "
            "implied volatility and 30-day realized volatility; (2) IV momentum -- the "
            "3-day and 5-day rate of change in at-the-money IV; (3) volume/OI ratio -- "
            "abnormal option flow relative to open interest as a herding proxy."
        ),
        depends=(
            "market_data.py -- IV surface, volume, OI (Step 1)\n"
            "p_estimator.py -- p_independent used to confirm mispricing persistence (Step 2)"
        ),
        note="Regime thresholds (5% / 10% RV-IV spread) should be validated on historical data.",
    )

    section_head(pdf, "Regime Logic")
    code_block(pdf, [
        "RV_IV_spread   = IV_implied - RV_30d",
        "Normal regime  : abs(RV_IV_spread) < 5%  -- min edge threshold = 2%",
        "Herding regime : RV_IV_spread > 10%       -- min edge threshold = 8%",
    ])

    pdf.add_page()
    pdf.ln(10)

    step_card(
        pdf,
        step_num="Step 4",
        module="micro_cost.py",
        tagline="Fee, spread, and slippage cost model -- edge net of transaction costs.",
        layer_done=False,
        what=(
            "Calculates the true net edge after subtracting all transaction costs from the "
            "raw edge signal. Costs modeled: bid-ask spread (half-spread paid on entry and "
            "exit), brokerage fee ($0.65 per contract at Fidelity), and slippage (price "
            "impact when order size is large relative to daily volume). The key output is "
            "edge_net -- the edge that actually survives into your P&L after costs. The "
            "policy in Step 6 gates trade entry on edge_net > min_edge_threshold. An "
            "additional VaR constraint rejects any trade where the Kelly-sized position "
            "would exceed 5% of capital at risk. A drawdown circuit breaker halts all "
            "trading if cumulative losses exceed 15% of starting capital."
        ),
        depends=(
            "market_data.py -- bid-ask spread data per strike (Step 1)\n"
            "edge.py -- raw CRR edge (Layer 1, already built)\n"
            "p_estimator.py -- edge_independent (Step 2)"
        ),
        note="Can be built in parallel with Step 3 -- does not depend on bias_detector.py.",
    )

    section_head(pdf, "Net Edge Formula")
    code_block(pdf, [
        "cost = (0.5 * bid_ask_spread + fee_per_share + slippage) / V_market",
        "edge_net = edge_independent - cost",
        "Trade only when: edge_net > min_edge_threshold (regime-conditional)",
    ])

    pdf.add_page()
    pdf.ln(10)

    step_card(
        pdf,
        step_num="Step 5",
        module="calibration.py",
        tagline="Brier score and calibration curve -- validate p_independent accuracy.",
        layer_done=False,
        what=(
            "Evaluates whether p_independent from Step 2 is trustworthy. A model that "
            "outputs p=0.70 should be correct 70% of the time. Calibration.py measures "
            "this using two tools. The Brier score is the mean squared error between "
            "predicted probabilities and actual outcomes (lower is better; a naive "
            "baseline of always predicting 0.50 scores 0.25). The reliability diagram "
            "bins predictions into deciles and plots mean predicted probability versus "
            "actual outcome frequency -- a well-calibrated model falls on the diagonal. "
            "The Expected Calibration Error (ECE) summarizes the reliability diagram as "
            "a single number. All three metrics are reported in the research report "
            "Section 6. The calibration curve PNG is saved to project/outputs/."
        ),
        depends=(
            "p_estimator.py -- trained and calibrated model + held-out test set (Step 2)"
        ),
        note=(
            "The Brier score baseline is 0.25 (naive 50/50 prediction). "
            "The model must beat this to demonstrate any predictive value."
        ),
    )

    section_head(pdf, "Key Metrics")
    code_block(pdf, [
        "Brier score  = mean((p_pred - outcome)^2)   # baseline = 0.25; lower is better",
        "ECE          = mean(|mean_pred - mean_actual|) per probability bin",
        "Output: calibration_curve.png -> project/outputs/",
    ])

    pdf.add_page()
    pdf.ln(10)

    step_card(
        pdf,
        step_num="Step 6",
        module="policy.py",
        tagline="Regime-conditional trade decision engine -- where all layers connect.",
        layer_done=False,
        what=(
            "Combines the outputs of all prior Layer 2 modules into a single trade "
            "decision per ticket. For each option contract the policy asks: (1) Is the "
            "regime normal or herding? (sets the edge threshold). (2) Does edge_net "
            "exceed the regime-appropriate threshold? (3) Does the Kelly-sized position "
            "pass the VaR and drawdown constraints? If all three conditions are met, the "
            "policy emits a TRADE signal with the full/half/quarter-Kelly dollar "
            "position. Otherwise it emits NO TRADE. This is the direct analog of the "
            "Kalshi-style trading policy described in Project 6 Section 2."
        ),
        depends=(
            "bias_detector.py -- regime label (Step 3)\n"
            "micro_cost.py    -- edge_net (Step 4)\n"
            "kelly.py         -- Kelly fraction (Layer 1, already built)"
        ),
        note="This is the capstone of Layer 2 -- all prior steps feed into it.",
    )

    section_head(pdf, "Decision Logic")
    code_block(pdf, [
        "min_edge = 0.02 if regime == 'normal' else 0.08   # regime-conditional",
        "if edge_net > min_edge and kelly_position <= var_limit:",
        "    signal = TRADE   # with dollar_full / dollar_half / dollar_quarter",
        "else:",
        "    signal = NO_TRADE",
    ])

    pdf.add_page()
    pdf.ln(10)

    step_card(
        pdf,
        step_num="Step 7",
        module="backtest.py",
        tagline="Walk-forward historical backtest runner and experiment dashboard.",
        layer_done=False,
        what=(
            "Applies policy.py to historical option chain data in a walk-forward loop: "
            "train on the first N months, test on the next month, then roll the window "
            "forward. For each test period, records the trade signal, the Kelly position, "
            "and the realized P&L (did the option expire ITM or OTM?). Aggregates results "
            "across all windows and computes P&L distribution, annualized Sharpe ratio, "
            "maximum drawdown, hit rate, and Brier score. Saves three plots to "
            "project/outputs/: pnl_curve.png (cumulative P&L over the backtest), "
            "regime_analysis.png (RV-IV spread and regime state over time), and a "
            "summary comparison of full/half/quarter-Kelly equity curves."
        ),
        depends=(
            "policy.py       -- trade decision for each contract (Step 6)\n"
            "calibration.py  -- Brier score for backtest window (Step 5)\n"
            "Historical labeled data -- same dataset used to train p_estimator.py"
        ),
        note=(
            "Build this last. It is the experiment you report in the research report "
            "Section 6 (backtest results) and present on Slide 5 of the final presentation."
        ),
    )

    section_head(pdf, "Key Output Metrics")
    code_block(pdf, [
        "P&L distribution    -- histogram of trade-level profits and losses",
        "Sharpe ratio        -- annualized (P&L mean / P&L std * sqrt(252))",
        "Max drawdown        -- largest peak-to-trough cumulative loss",
        "Hit rate            -- fraction of trades where model direction was correct",
        "Brier score         -- probability calibration accuracy on backtest outcomes",
        "Outputs: pnl_curve.png, regime_analysis.png -> project/outputs/",
    ])

    # ── Final page: prerequisites checklist ───────────────────────────────────
    pdf.add_page()
    pdf.ln(10)

    pdf.set_fill_color(*STEP_BG)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 9, "  Prerequisites Checklist Before Starting Layer 2",
             new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(4)

    prereqs = [
        ("Historical option chain data",
         "p_estimator.py requires labeled ITM/OTM outcomes at expiry. Use the "
         "Kaggle AAPL options dataset (kylegraupe/aapl-options-data-2016-2020) as a "
         "structural proxy if AMD chain history is unavailable. Document the data "
         "substitution explicitly in the research report limitations section."),
        ("scikit-learn and XGBoost installed",
         "Run the command below from the repo root before starting Step 2."),
        ("Layer 1 passing cleanly",
         "The walk-forward backtest (Step 7) uses CRR pricing as a comparison "
         "benchmark. tree.py must produce V_model within 0.005% of V_market. "
         "Run 'make run' and confirm outputs/model_vs_market.png shows near-zero "
         "error before starting Layer 2."),
        ("Project/outputs directory writable",
         "Steps 5 and 7 write PNG files to project/outputs/. Verify the directory "
         "exists and is writable: ls project/outputs/"),
    ]

    for label, desc in prereqs:
        section_head(pdf, label)
        body(pdf, desc)

    section_head(pdf, "Install Layer 2 Dependencies")
    code_block(pdf, [
        ".venv/bin/python3 -m pip install scikit-learn xgboost lightgbm",
    ])

    pdf.ln(2)
    pdf.set_draw_color(190, 195, 210)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    section_head(pdf, "Build Command Quick Reference")
    code_block(pdf, [
        "# Step 0 -- verify Layer 1",
        "make run",
        "",
        "# Steps 1-7 -- Layer 2 (run from repo root, in order)",
        ".venv/bin/python3 project/market_data.py",
        ".venv/bin/python3 project/p_estimator.py",
        ".venv/bin/python3 project/bias_detector.py",
        ".venv/bin/python3 project/micro_cost.py",
        ".venv/bin/python3 project/calibration.py",
        ".venv/bin/python3 project/policy.py",
        ".venv/bin/python3 project/backtest.py",
        "",
        "# Rebuild PDF deliverables",
        ".venv/bin/python3 make_crr_pdf.py",
        ".venv/bin/python3 make_pipeline_components_pdf.py",
        ".venv/bin/python3 make_build_sequence_pdf.py",
        "",
        "# Rebuild HTML animation",
        ".venv/bin/python3 crr_binomial_pricing_amd_html.py",
    ])

    # ── Layer 2 complete run sequence ─────────────────────────────────────────
    pdf.add_page()
    pdf.ln(6)

    # Header banner
    pdf.set_fill_color(*DONE_BG)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "  Layer 2 -- All Modules Built: Complete Run Sequence",
             new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*BODY_TXT)
    pdf.multi_cell(0, 5.5,
        "All seven Layer 2 modules are written and ready to run. Execute the steps below "
        "in order from the repo root. Each step depends on the one before it. "
        "Steps 2 and 7 take the longest (model training and walk-forward backtest).",
        align="J")
    pdf.ln(3)

    # Step table
    col_w2 = [18, 52, 52, 58]
    headers2 = ["Step", "Command", "Output file(s)", "What it produces"]
    step_rows = [
        ("0",
         "make run",
         "outputs/*.csv, *.png",
         "Verify Layer 1: CRR pricing, Greeks, edge, Kelly, Monte Carlo"),
        ("1",
         "python3 project/market_data.py",
         "(DataFrame in memory)",
         "Load AAPL dataset, compute RV, label ITM/OTM, engineer features"),
        ("2",
         "python3 project/p_estimator.py",
         "outputs/call_model.pkl\noutputs/put_model.pkl",
         "Train and calibrate gradient boosting probability models"),
        ("3",
         "python3 project/bias_detector.py",
         "outputs/regime_analysis.png",
         "Classify normal vs herding regime; plot RV-IV spread over time"),
        ("4",
         "python3 project/micro_cost.py",
         "(console report)",
         "Verify net edge after spread, fee, slippage on AMD tickets"),
        ("5",
         "python3 project/calibration.py",
         "outputs/calibration_curve.png",
         "Brier score + reliability diagram for call and put models"),
        ("6",
         "python3 project/policy.py",
         "(console report)",
         "Regime-conditional trade decision for each AMD ticket"),
        ("7",
         "python3 project/backtest.py",
         "outputs/pnl_curve.png\noutputs/backtest_trades.csv",
         "Walk-forward backtest: P&L, Sharpe, drawdown, hit rate"),
    ]

    pdf.set_fill_color(*TBL_HDR)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8)
    for i, h in enumerate(headers2):
        pdf.cell(col_w2[i], 7, h, border=1, fill=True)
    pdf.ln()

    for idx, (step, cmd, out, purpose) in enumerate(step_rows):
        is_layer1 = (step == "0")
        pdf.set_fill_color(*(TBL_R1 if idx % 2 == 0 else TBL_R2))
        pdf.set_text_color(*BODY_TXT)

        # step number -- color coded
        step_col = DONE_BG if is_layer1 else (20, 83, 45)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*step_col)
        pdf.cell(col_w2[0], 6, step, border=1, fill=True)

        # command
        pdf.set_font("Courier", "", 7.5)
        pdf.set_text_color(*CODE_TXT)
        pdf.cell(col_w2[1], 6, cmd.replace("python3 ", ""), border=1, fill=True)

        # output
        pdf.set_font("Courier", "", 7.5)
        pdf.set_text_color(80, 40, 120)
        pdf.cell(col_w2[2], 6, out.split("\n")[0], border=1, fill=True)

        # purpose
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*BODY_TXT)
        pdf.cell(col_w2[3], 6, purpose, border=1, fill=True)
        pdf.ln()

    pdf.ln(4)
    pdf.set_draw_color(190, 195, 210)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    section_head(pdf, "Full Run -- Copy and Paste")
    code_block(pdf, [
        "# Layer 1 (already built)",
        "make run",
        "",
        "# Layer 2 -- run in order from repo root",
        ".venv/bin/python3 project/market_data.py",
        ".venv/bin/python3 project/p_estimator.py",
        ".venv/bin/python3 project/bias_detector.py",
        ".venv/bin/python3 project/micro_cost.py",
        ".venv/bin/python3 project/calibration.py",
        ".venv/bin/python3 project/policy.py",
        ".venv/bin/python3 project/backtest.py",
    ])

    pdf.ln(2)
    pdf.set_draw_color(190, 195, 210)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    section_head(pdf, "Expected Output Files After Full Run")
    out_rows = [
        ("project/outputs/call_model.pkl",        "Calibrated call probability model (XGBoost + Platt scaling)"),
        ("project/outputs/put_model.pkl",         "Calibrated put probability model (XGBoost + Platt scaling)"),
        ("project/outputs/regime_analysis.png",   "ATM IV vs RV30, RV-IV spread, and regime state over time"),
        ("project/outputs/calibration_curve.png", "Reliability diagram + Brier score for call and put models"),
        ("project/outputs/pnl_curve.png",         "Cumulative P&L and trade P&L distribution (walk-forward backtest)"),
        ("project/outputs/backtest_trades.csv",   "Full trade log: date, regime, edge, outcome, P&L per trade"),
        ("project/outputs/model_vs_market.png",   "Layer 1: CRR V_model vs V_market for all four AMD tickets"),
        ("project/outputs/convergence.png",       "Layer 1: CRR price convergence as N increases"),
        ("project/outputs/kelly_fractions.png",   "Layer 1: full / half / quarter-Kelly dollar positions"),
        ("project/outputs/early_exercise_boundary.png", "Layer 1: AMD put early exercise boundary S* over time"),
    ]

    col_ow = [72, 108]
    pdf.set_fill_color(*TBL_HDR)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(col_ow[0], 6.5, "File", border=1, fill=True)
    pdf.cell(col_ow[1], 6.5, "Description", border=1, fill=True)
    pdf.ln()

    for idx, (fname, desc) in enumerate(out_rows):
        pdf.set_fill_color(*(TBL_R1 if idx % 2 == 0 else TBL_R2))
        pdf.set_font("Courier", "", 7.5)
        pdf.set_text_color(80, 40, 120)
        pdf.cell(col_ow[0], 6, fname.replace("project/outputs/", "outputs/"),
                 border=1, fill=True)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*BODY_TXT)
        pdf.cell(col_ow[1], 6, desc, border=1, fill=True)
        pdf.ln()

    pdf.output(OUT)
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    make_pdf()
