# PLAN2.md

<!-- ============================================================
     PLAN2.md -- Full project blueprint combining:
       (A) The existing AMD CRR + Kelly pipeline from PLAN.md
       (B) The missing Project 6 components identified in the gap
           analysis: independent p-estimator, crowd bias detector,
           microstructure-aware trading policy, probability
           calibration, and ethics section.

     HOW TO READ THIS FILE
     ---------------------
     Each major section has an HTML comment block (like this one)
     that explains:
       - What the section covers
       - Why it is required by Project 6
       - How it connects to the rest of the pipeline

     The deliverable artifacts at the bottom (PDFs + HTML animation)
     are identical to PLAN.md -- nothing already built is removed.
     New work is additive.
     ============================================================ -->

## Project Overview

**Title:** Profit-Maximizing Model for Prediction Markets Under Crowd (Majority) Betting
**Author:** DeWayne Dantzler
**Course:** CS495 Deep Scholar — Capstone Project 6
**Date:** April 27, 2026 (revised May 2026)

<!-- ============================================================
     OVERVIEW COMMENT
     ----------------
     Project 6 asks for a profit-maximizing policy in a Kalshi-
     style binary prediction market. The strategy in this plan is
     to use AMD American equity options as the target instrument
     because:
       1. Real, live market data is available (Fidelity order book).
       2. The CRR binomial model produces a rigorous theoretical
          price (V_model) that can be compared to market price
          (V_market) to generate an edge signal -- exactly the
          p - q edge framework Project 6 requires.
       3. Options pricing is a superset of binary contract pricing:
          all the Kelly, edge, and simulation machinery carries over
          directly.
     The plan explicitly bridges both frames: the CRR model is the
     "true p" estimator engine; the behavioral overlay and
     microstructure layers are added on top.
     ============================================================ -->

### Description

Prediction markets (like Kalshi) aggregate crowd beliefs into prices, but prices are not always
"perfect probabilities." Market prices can reflect behavioral biases, herding, and liquidity
effects, especially when a large share of participants follow similar heuristics or "BetAI"-style
signals.

This project implements a two-layer pipeline:

**Layer 1 — CRR Pricing Engine (equity options analog)**
Build a six-stage quantitative pipeline for AMD equity options using the Cox-Ross-Rubinstein
(CRR) binomial model (American-style, no dividends, N=100 steps). The pipeline prices options,
computes Greeks, measures the signed mispricing edge (V_model − V_market) / V_market, and sizes
trades using the Kelly Criterion (full, half, quarter variants). A Monte Carlo simulation
evaluates P&L across 1,000 hypothetical trades.

**Layer 2 — Prediction Market Extension**
On top of the pricing engine, add the components required by Project 6 but absent from the
original pipeline: an independent probability estimator (ML model), a crowd behavioral bias
detector with regime-conditional policy, a microstructure-aware cost model (fees, spreads,
slippage), and probability calibration (Brier score + calibration curves).

The combined system produces a "playbook" for detecting and exploiting mispricing in markets
where crowd behavior creates structural, predictable bias.

---

## Scope and Constraints

<!-- ============================================================
     SCOPE COMMENT
     -------------
     Scope defines what is IN and what is OUT of the model.
     This is important for a capstone because it sets honest
     boundaries -- the research report must acknowledge these
     limits. Project 6 explicitly asks for a limitations section
     in the report.
     ============================================================ -->

- **American options only.** All four AMD contracts (buy/sell call, buy/sell put) are treated
  as American-style. Early exercise capability is required at every node. European-style
  pricing is excluded.

- **No dividends (Layer 1 — known limitation).** The CRR binomial tree uses the standard
  risk-neutral probability formula `p = (exp(r*dt) - d) / (u - d)` with no continuous
  dividend yield adjustment. This was scoped to AMD, which pays negligible dividends.
  When Layer 1 is applied to the AAPL Kaggle dataset for cross-layer comparison, the
  missing dividend term causes measurable systematic pricing error: puts are underpriced
  by a mean of **-10.76%** and calls are overpriced by **+6.58%** relative to market
  prices (measured across 1,500 sampled contracts per type, 2016–2020). AAPL's dividend
  yield over this period was approximately 0.6–1.0% annually. The correct fix would add
  a yield term `q` to the CRR up/down factors (`u = exp((r - q)*dt + sigma*sqrt(dt))`),
  but this is outside the AMD-scoped project boundary. The pricing error is documented
  here as a known, quantified limitation rather than silently corrected, consistent with
  the research report's limitations section (Section 7).

- **Binary event analog.** AMD options are treated as a proxy for binary prediction market
  contracts: the option either expires ITM (like a $1 resolution) or OTM (like a $0
  resolution). This framing allows direct application of the Kalshi-style edge framework.

- **Simulation only.** This is a research + simulation project, not live trading. All P&L
  figures are hypothetical. Responsible risk controls (max drawdown limits, fractional Kelly)
  are enforced throughout.

- **Ethics disclaimer.** Results must not be interpreted as guaranteed profits. All edge
  estimates are model-dependent and subject to IV calibration assumptions. An explicit
  ethics / responsible trading section is included in the research report.

---

## Architecture: Two-Layer Pipeline

<!-- ============================================================
     ARCHITECTURE COMMENT
     --------------------
     This diagram shows how Layer 1 (the original AMD CRR
     pipeline) and Layer 2 (the new prediction market extensions)
     connect to each other. Each box corresponds to a code module.
     The arrow direction shows data flow. Understanding this flow
     is essential for writing the "Pipeline Stages" section of
     the research report.
     ============================================================ -->

```
LAYER 1: CRR Pricing Engine
─────────────────────────────────────────────────────────────────
 config.yaml ──► data.py ──► tree.py ──► greeks.py
                                 │
                                 ▼
                             edge.py ──► kelly.py ──► simulation.py
                                              │
                                              ▼
                                          main.py (orchestrator)

LAYER 2: Prediction Market Extensions (new)
─────────────────────────────────────────────────────────────────
 market_data.py    -- fetch IV surface, volume, open interest
       │
       ▼
 p_estimator.py   -- ML model: independent "true p" estimate
       │
       ▼
 bias_detector.py -- crowd regime classifier (normal vs herding)
       │
       ▼
 micro_cost.py    -- fee/spread/slippage model
       │
       ▼
 calibration.py   -- Brier score, calibration curves
       │
       ▼
 policy.py        -- regime-conditional trade entry/exit policy
       │
       ▼
 backtest.py      -- unified P&L + regime backtest runner
```

---

## Tasks

<!-- ============================================================
     TASKS COMMENT
     -------------
     Tasks are organized into eight phases. Phases 1-6 map
     directly to the original PLAN.md structure (with corrections
     to phase ordering). Phases 7-8 are new and cover the Project
     6 components not present in PLAN.md.

     Checkbox syntax: [ ] = not started, [x] = complete.
     ============================================================ -->

### Phase 1: Data Collection & Cleaning

<!-- Covers the "Data ingestion / cleaning" code repository
     deliverable required by Project 6. Also addresses the
     original PLAN.md Phase 1 and Phase 3 tasks (merged here
     to fix the ordering inconsistency in the original plan). -->

- [x] Download AMD option chain inputs from Yahoo Finance (spot price, IV, Greeks)
- [x] Fetch 6-month AMD daily closing prices for realized volatility (rv30, rv60) via yfinance
- [x] Store all inputs in a structured pandas DataFrame with exact collection timestamp
- [x] Extract the six Greeks: IV, Delta, Gamma, Theta, Vega, Rho into a pandas DataFrame
- [ ] Collect IV surface data (multiple strikes and expiries) for regime feature engineering
- [ ] Download or synthesize historical option chain snapshots for backtesting (kaggle.com/datasets/kylegraupe/aapl-options-data-2016-2020 as proxy if AMD history unavailable)
- [ ] Document data provenance, collection date, and any survivorship bias risks

### Phase 2: CRR Pricing Engine (Layer 1)

<!-- This is the core of PLAN.md. The CRR engine produces V_model,
     which is this project's "true p" pricing benchmark. It is
     the analog of the probability model required in Project 6
     Section 1. Completing this phase fulfills the "pricing
     validation within ±5%" requirement. -->

- [x] Implement CRR American binomial tree (tree.py, N=100, vectorized NumPy)
- [x] Validate V_model against Fidelity observed AMD premiums and Greeks within ±5%
- [x] Compute signed mispricing edge: edge = (V_model − V_market) / V_market (edge.py)
- [x] Map early exercise boundary S* for AMD American puts at every time step
- [x] Apply Kelly Criterion (full, half, quarter-Kelly) to translate edge into dollar positions (kelly.py)
- [x] Run Monte Carlo P&L simulation: Sharpe, max drawdown, hit rate across 1,000 trades (simulation.py)
- [ ] Sensitivity analysis: quantify edge and Kelly fraction stability under perturbations to IV, r, T

### Phase 3: Independent Probability Estimator (Layer 2 — new)

<!-- PROJECT 6 REQUIREMENT: Section 1 — "A probability model (true p estimator)"
     This is the biggest gap in the original PLAN.md. The CRR model calibrates
     IV FROM the market price (edge ~ 0% by construction). To find genuine
     mispricing the project needs an INDEPENDENT estimate of true p that does
     not use market price as input.

     The approach here:
       - Use historical realized volatility (rv30, rv60) as the independent
         IV forecast instead of market-implied IV.
       - Also train a logistic regression / gradient boosting model on
         engineered features (moneyness, time decay, RV-IV spread, volume)
         to predict whether an option is mispriced relative to realized moves.
       - Calibrate the model probability output (Platt scaling / isotonic).

     This module produces p_independent -- the project's independent edge signal. -->

- [ ] Define feature set: moneyness (S/K), DTE, RV-IV spread, open interest, volume, bid-ask spread
- [ ] Label historical options: ITM/OTM at expiry (binary outcome -- the prediction market analog)
- [ ] Train logistic regression baseline probability model on historical data
- [ ] Train gradient boosting model (XGBoost or LightGBM) as the primary p-estimator
- [ ] Apply Platt scaling or isotonic regression for probability calibration
- [ ] Compute edge using independent p: edge_independent = p_model − q_market
- [ ] Compare edge_independent against the CRR-derived edge as a validation cross-check

### Phase 4: Crowd Bias Detector / Regime Classification (Layer 2 — new)

<!-- PROJECT 6 REQUIREMENT: Section 3 — "A majority bettor / Bet-AI crowd bias detector"
     The original PLAN.md has no regime detection at all. This phase adds it.

     The regime detector classifies market conditions into two states:
       Normal regime  -- small-edge environment; crowd is approximately rational
       Herding regime -- crowd is systematically biased; IV is detached from RV;
                         vol premium is large and persistent

     Indicators used:
       - RV-IV spread: large positive spread (IV >> RV) signals vol overpricing (herding into fear)
       - IV momentum: rapid IV increase over 3-5 days signals herding into options
       - Volume spike: abnormal option volume relative to open interest
       - Mispricing persistence: edge_independent stays in the same sign for 3+ days

     The policy then conditions trade conviction on the detected regime. -->

- [ ] Compute RV-IV spread time series from historical data (primary herding signal)
- [ ] Build volume / open interest ratio indicator as a herding proxy
- [ ] Implement IV momentum feature (3-day and 5-day IV change)
- [ ] Define regime thresholds: normal (|RV-IV spread| < 5%), herding (spread > 10%)
- [ ] Train a regime classifier (logistic regression or threshold rule) on labeled historical windows
- [ ] Implement regime-conditional policy:
      - Normal regime: trade if |edge_independent| > 2% (existing min_edge threshold)
      - Herding regime: trade only if |edge_independent| > 8% (high-conviction only)
- [ ] Generate regime analysis time series plot for the experiment dashboard

### Phase 5: Microstructure-Aware Trading Policy (Layer 2 — new)

<!-- PROJECT 6 REQUIREMENT: Section 2 — "A microstructure-aware trading policy"
     The original PLAN.md simulation uses a binary win/loss model with no
     transaction costs. Project 6 requires explicit modeling of:
       - Bid-ask spread cost (half-spread paid on entry and exit)
       - Brokerage fees (Fidelity: $0.65/contract)
       - Slippage (price impact when order size is large relative to volume)
     The policy avoids entering a trade when net edge after costs is below
     the min_edge threshold.

     This module wraps the existing kelly.py output with a cost filter. -->

- [ ] Build micro_cost.py: model bid-ask spread, brokerage fee, slippage per contract
- [ ] Define net edge: edge_net = edge_independent - (spread_cost + fee + slippage) / V_market
- [ ] Update policy to gate trades on edge_net > min_edge (not raw edge)
- [ ] Add VaR constraint: reject trades where position size exceeds 5% of capital at risk
- [ ] Add max drawdown circuit breaker: halt trading if cumulative drawdown exceeds 15%
- [ ] Document all microstructure assumptions in the research report limitations section

### Phase 6: Backtesting and Simulation (expanded)

<!-- PROJECT 6 REQUIREMENT: Section 4 — "Backtesting and simulation"
     The existing simulation.py covers Monte Carlo P&L but does not run a
     historical backtest across multiple option contracts. This phase adds
     a walk-forward backtest that applies the full policy (Layer 1 + Layer 2)
     to historical data.

     Key metrics required by Project 6:
       - P&L distribution
       - Sharpe-like metric (annualized)
       - Max drawdown
       - Hit rate and probability calibration (Brier score)
     All results must be reproducible (fixed random seed). -->

- [x] Monte Carlo P&L simulation: Sharpe, max drawdown, hit rate (simulation.py, 1,000 trades, seed=42)
- [ ] Walk-forward backtest: apply full policy to historical AMD option chain snapshots
- [ ] Report P&L distribution, Sharpe, max drawdown across all backtest windows
- [ ] Compute hit rate: fraction of trades where model predicted direction correctly
- [ ] Generate P&L curve plot for experiment dashboard

### Phase 7: Probability Calibration and Evaluation (Layer 2 — new)

<!-- PROJECT 6 REQUIREMENT: Experiment dashboard — "Calibration curves"
     and research report — "Model for p (true probability)"
     Calibration measures whether the model's probability output is
     trustworthy. A model that says p=0.70 should be right 70% of the time.

     The Brier score is the standard scoring rule for binary probability
     models. It equals mean((p_predicted - outcome)^2). Lower is better.
     A naive baseline (always predict 0.5) has Brier score = 0.25.

     This phase produces the calibration deliverable required by Project 6
     and provides an honest assessment of the p-estimator's accuracy. -->

- [ ] Compute Brier score for p_estimator.py on held-out test set
- [ ] Compare Brier score against: (a) naive baseline, (b) market-implied q, (c) CRR V_model
- [ ] Generate reliability diagram (calibration curve): predicted p vs actual outcome frequency
- [ ] Report expected calibration error (ECE) as a summary statistic
- [ ] Save calibration_curve.png to project/outputs/ for experiment dashboard

### Phase 8: Deliverables

<!-- PROJECT 6 DELIVERABLE REQUIREMENTS:
       1. Research report (10-20 pages)
       2. Code repository
       3. Experiment dashboard
       4. Final presentation
     The items below map each requirement to a specific output file.
     Items marked [x] are already built; items marked [ ] are outstanding. -->

#### Research Report (10–20 pages)

- [ ] Section 1 — Market setup and assumptions (AMD options as binary contract analog)
- [ ] Section 2 — Behavioral hypotheses (majority bias, IV premium, herding indicators)
- [ ] Section 3 — CRR model for V_model / p (theory, forward pass, backward induction)
- [ ] Section 4 — Independent p-estimator (ML model design, features, calibration)
- [ ] Section 5 — Trading policy and risk controls (edge threshold, Kelly sizing, microstructure)
- [ ] Section 6 — Backtest results (P&L, Sharpe, drawdown, hit rate, calibration)
- [ ] Section 7 — Limitations (IV calibration assumption, data availability, no live trading,
      no dividend adjustment in Layer 1 CRR tree: measured -10.76% put / +6.58% call
      pricing error on AAPL 2016-2020; yield term omitted by AMD project scope)
- [ ] Section 8 — Ethics / responsible trading disclaimer

#### Code Repository

- [x] config.yaml — pipeline configuration (AMD option chain inputs)
- [x] data.py — Stage 1: data ingestion and preprocessing
- [x] tree.py — Stage 2: CRR American binomial tree pricer
- [x] greeks.py — Stage 3: numerical Greeks via finite differences
- [x] edge.py — Stage 4: mispricing edge computation
- [x] kelly.py — Stage 5a: Kelly Criterion trade sizing
- [x] simulation.py — Stage 5b: Monte Carlo P&L simulation
- [x] main.py — pipeline orchestrator
- [ ] market_data.py — IV surface and volume data ingestion (Layer 2)
- [ ] p_estimator.py — ML probability model training and calibration (Layer 2)
- [ ] bias_detector.py — regime classifier and crowd bias indicators (Layer 2)
- [ ] micro_cost.py — fee, spread, slippage cost model (Layer 2)
- [ ] calibration.py — Brier score and calibration curve (Layer 2)
- [ ] policy.py — regime-conditional trade entry/exit policy (Layer 2)
- [ ] backtest.py — walk-forward historical backtest runner (Layer 2)

#### Experiment Dashboard (plots saved to project/outputs/)

- [x] model_vs_market.png — V_model vs V_market for all four AMD tickets
- [x] convergence.png — CRR price convergence as N increases
- [x] kelly_fractions.png — full/half/quarter-Kelly dollar positions
- [x] early_exercise_boundary.png — S* boundary for AMD American puts
- [ ] calibration_curve.png — predicted p vs actual outcome frequency (Brier)
- [ ] pnl_curve.png — cumulative P&L over the walk-forward backtest window
- [ ] regime_analysis.png — RV-IV spread, IV momentum, regime state over time

#### Final Presentation

- [ ] Slide 1 — Project summary: two-layer pipeline architecture diagram
- [ ] Slide 2 — CRR pricing engine: forward pass + backward induction (use crr_pipeline_animation.html)
- [ ] Slide 3 — Independent p-estimator: features, model choice, calibration curve
- [ ] Slide 4 — Crowd bias detector: regime indicators and conditional policy
- [ ] Slide 5 — Backtest results: P&L curve, Sharpe, drawdown, hit rate
- [ ] Slide 6 — When does the crowd become systematically wrong? (regime analysis plot)
- [ ] Slide 7 — Failure cases and limitations
- [ ] Slide 8 — Ethics and responsible trading disclaimer

---

## Methods

<!-- ============================================================
     METHODS COMMENT
     ---------------
     This section documents the mathematical and algorithmic
     techniques used. Required by Project 6 in the research
     report. It also serves as the reference for anyone
     reproducing the pipeline from scratch.
     ============================================================ -->

### CRR Binomial Pricing (Layer 1)

- Forward pass: `S(i,j) = S × u^(i-j) × d^j`; `u = exp(IV × sqrt(dt))`, `d = 1/u`
- Risk-neutral probability: `p = (exp(r × dt) − d) / (u − d)`
- Backward induction: `hold = disc × (p × V_up + q × V_down)`; `V = max(intrinsic, hold)`
- American early exercise enforced at every node

### Edge and Kelly Sizing

- Mispricing edge: `edge = (V_model − V_market) / V_market`
- Kelly fraction: `f* = (p × b − q) / b` where `b = 1` (simplified 1:1 odds)
- Fractional Kelly: `f_half = f*/2`, `f_quarter = f*/4`
- Min edge filter: trades with `|edge| < 2%` are flagged NO TRADE

### Independent Probability Estimator (Layer 2)

- Feature set: moneyness, DTE, RV-IV spread, volume/OI ratio, bid-ask spread
- Primary model: gradient boosting (XGBoost/LightGBM) trained on binary ITM/OTM outcomes
- Calibration: Platt scaling or isotonic regression applied post-training
- Output: `p_independent` — probability option expires ITM, independent of market IV

### Crowd Bias Detection

- Herding signal: `RV_IV_spread = IV_implied − RV_30d`; large positive spread = vol overpricing
- Regime threshold: normal (`spread < 5%`), herding (`spread > 10%`)
- Policy conditioning: min edge threshold tightened from 2% to 8% in herding regime

### Probability Calibration

- Brier score: `BS = mean((p_pred − outcome)^2)` — lower is better; baseline = 0.25
- Reliability diagram: bins predicted p into deciles, plots mean predicted vs actual frequency
- Expected Calibration Error (ECE): mean absolute deviation across probability bins

### Microstructure Cost Model

- Net edge: `edge_net = edge_independent − (0.5 × spread + fee_per_share + slippage) / V_market`
- Trade only when `edge_net > min_edge`
- Max drawdown circuit breaker at 15% cumulative loss

---

## Technology Stack

<!-- Lists every library used and its specific role. This is required
     for the "Code repository" deliverable section. Reviewers should
     be able to reproduce the environment from this list alone. -->

| Library | Role |
|---|---|
| Python 3.13 | Primary language |
| NumPy | Vectorized CRR lattice construction; finite differences |
| pandas | Data ingestion, option chain DataFrame, results storage |
| scipy | IV solver (brentq), statistical functions, Monte Carlo helpers |
| yfinance | AMD historical price data and realized volatility download |
| matplotlib | Convergence plots, Kelly charts, calibration curves, regime plots |
| XGBoost / LightGBM | Gradient boosting probability estimator (p_estimator.py) |
| scikit-learn | Logistic regression baseline, Platt scaling, isotonic calibration |
| fpdf2 | PDF report generation (make_crr_pdf.py, make_pipeline_components_pdf.py) |
| Jupyter | Notebook-based reproducible analysis and reporting |
| GitHub | Repository hosting and version control |

---

## Ethics and Responsible Trading

<!-- ============================================================
     ETHICS COMMENT
     --------------
     Project 6 explicitly requires an ethics / responsible
     gambling section. This section must appear in the research
     report. It is included here in the plan so it is not
     accidentally omitted from the report outline.

     Key points to cover:
       - All results are simulation only; no live capital is at risk
       - Edge estimates are model-dependent; overconfidence is dangerous
       - Fractional Kelly is used precisely to limit ruin risk
       - The model does not guarantee profit
     ============================================================ -->

- All P&L figures are hypothetical simulation results, not live trading outcomes.
- Edge estimates depend on the accuracy of the IV forecast and ML probability model.
  Overconfident models can produce systematically wrong sizing recommendations.
- The fractional Kelly variants (half, quarter) exist specifically to reduce ruin risk
  in the presence of model error. Full Kelly is included for comparison only.
- The 15% drawdown circuit breaker and 2–8% min-edge filter are responsible risk
  controls that prevent the model from overtrading on noisy signals.
- This project must not be interpreted as a recommendation to trade options or
  prediction market contracts. It is an academic research simulation.

---

## Deliverable Artifacts

<!-- ============================================================
     DELIVERABLE ARTIFACTS COMMENT
     ------------------------------
     These are the exact same files produced by PLAN.md -- nothing
     built in the original pipeline is removed. The three files
     below document and visualize Layer 1 (CRR engine). The Layer 2
     outputs (calibration curve, P&L curve, regime plot) are added
     to project/outputs/ by the new modules in Phase 7.
     ============================================================ -->

---

### CRR-Binomial-Option-Pricing-Model-Pipeline-Components.pdf

<!-- Documents every stage of the Layer 1 pipeline in reference card format.
     One page per component. Serves as the "code repository documentation"
     deliverable for Project 6. -->

- **Source script:** `make_pipeline_components_pdf.py`
- **Build command:**
  ```
  .venv/bin/python3 make_pipeline_components_pdf.py
  ```
- **Output location:** `CRR-Binomial-Option-Pricing-Model-Pipeline-Components.pdf` (repo root)
- **Pages:** 9 (1 overview + 1 per pipeline component)
- **Used for:** Code repository documentation; Phase 8 deliverable

---

### CRR-Binomial-Option-Pricing-Model-Scheme.pdf

<!-- Technical deep-dive into the CRR model math: forward pass, backward
     induction, V_model vs V_market interpretation, Kelly edge framework.
     Maps directly to Sections 3 and 5 of the research report outline. -->

- **Source script:** `make_crr_pdf.py`
- **Build command:**
  ```
  .venv/bin/python3 make_crr_pdf.py
  ```
- **Output location:** `~/CRR-Binomial-Pricing-AMD-Options.pdf` (home directory)
- **Pages:** 6 (forward pass, backward induction, V_model/V_market)
- **Key parameters:** S=341.35, K=350, r=5.3%, IV=74.73% (put), IV=73.92% (call), T=18 days
- **Used for:** Research report theory section (Sections 3 and 5)

---

### crr_pipeline_animation.html

<!-- Self-contained interactive browser animation of the CRR binomial tree.
     51 frames covering all six pipeline phases: intro, forward pass,
     terminal payoffs, backward induction, pricing results, takeaways.
     Used as the visual centerpiece of the final presentation (Slide 2). -->

- **Source script:** `crr_binomial_pricing_amd_html.py`
- **Build command:**
  ```
  .venv/bin/python3 crr_binomial_pricing_amd_html.py
  ```
- **Output location:** `crr_pipeline_animation.html` (repo root)
- **Total frames:** 51 (N=4 visual tree; N=100 used for pipeline pricing results)
- **Used for:** Final presentation Slide 2; live classroom demo

---

<!-- ============================================================
     NOTES FOR FUTURE SESSIONS
     --------------------------
     - Claude can help build the PLAN2.md and the new Layer 2 modules.
     - Use Claude's MCP connectors to push completed modules to GitHub.
     - The walk-forward backtest (backtest.py) requires historical option
       chain data -- if live AMD data is unavailable, use the AAPL kaggle
       dataset as a structural proxy and document the substitution.
     - Brier score baseline (0.25) assumes 50/50 naive prediction; the
       model must beat this to demonstrate any predictive value.
     ============================================================ -->
