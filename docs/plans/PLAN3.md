# PLAN3.md — Layer 1 vs Layer 2 Cross-Model Comparison

<!-- ============================================================
     PURPOSE
     -------
     PLAN3.md documents the cross-model comparison between Layer 1
     (CRR binomial pricing) and Layer 2 (XGBoost ML estimator) when
     both are applied to the same AAPL Kaggle contracts. This plan
     is additive -- it does NOT modify any existing pipeline module.
     All new work lives in two new scripts:
       - project/layer1_vs_layer2.py   (comparison analysis + plots)
       - make_aapl_crr_animation.py    (animated simulation HTML)
     ============================================================ -->

## Overview

**Title:** Layer 1 vs Layer 2 Cross-Model Comparison on AAPL Options
**Author:** DeWayne Dantzler
**Course:** CS495 Deep Scholar — Capstone Project 6
**Depends on:** PLAN2.md (both layers must be built first)

This plan documents a standalone comparison that answers the strongest
scientific question the project can ask:

> Do two completely independent methods — one mathematical/no-arbitrage
> (CRR), one empirical/ML (XGBoost) — agree on which AAPL options are
> mispriced by the crowd?

If they agree, both models validate each other simultaneously.
If they disagree, the disagreement zone is itself a finding worth reporting.

---

## The Scientific Question

<!-- ============================================================
     WHY THIS COMPARISON MATTERS
     ---------------------------
     Layer 1 and Layer 2 approach the same economic question from
     opposite directions:

     Layer 1 asks: "Given realized volatility as the true sigma,
     what should this option cost under no-arbitrage?" If the market
     charges more, the crowd is overpaying for volatility.

     Layer 2 asks: "Given historical ITM outcomes, what is the true
     probability this option expires ITM?" If the market implies a
     higher probability, the crowd is overestimating ITM likelihood.

     Both signals detect the same behavioral phenomenon -- the
     volatility risk premium / crowd herding into options -- but via
     different mechanisms. The comparison quantifies how much they
     agree.
     ============================================================ -->

Each model produces an **edge signal** on the same scale of direction:

| Model | Edge Signal | Negative = market overprices | Positive = market underprices |
|---|---|---|---|
| Layer 1 | `(V_model_rv - V_market) / V_market` | CRR(RV30) < market | CRR(RV30) > market |
| Layer 2 | `p_independent - q_market` | ML prob < market-implied prob | ML prob > market-implied prob |

Plotting L1 edge vs L2 edge on the same contracts produces a scatter where:
- **Quadrant III** (both negative): both models say market overprices → strong SELL signal
- **Quadrant I** (both positive): both models say market underprices → strong BUY signal
- **Quadrants II and IV**: models disagree → mixed signal, stay out

---

## Methodology

<!-- ============================================================
     METHODOLOGY COMMENT
     -------------------
     The key requirement is that both models are evaluated on
     IDENTICAL contracts. This rules out reusing separate outputs
     from aapl_crr_validation.py (Layer 1 sample) and
     backtest_trades.csv (Layer 2 traded contracts), because those
     datasets don't overlap -- the backtest only kept contracts that
     passed the edge filter.

     Instead, a single script draws a fresh common sample, applies
     both models, and compares on the same rows.
     ============================================================ -->

### Step 1 — Common Dataset

Load the AAPL 2016-2020 Kaggle dataset via `market_data.load_prepared()`.
This gives all engineered features (moneyness, RV30, IV, spreads) needed
by both models. Sample 1,500 valid put and 1,500 valid call contracts
with:
- DTE >= 5 days
- Both bid and ask > 0
- IV > 1% and RV30 > 1%
- Underlying price > 0

### Step 2 — Layer 1 Edge Signal

For each sampled contract, call `tree.price_american_option()` using:
- `S` = UNDERLYING_LAST
- `K` = STRIKE
- `T` = DTE / 365
- `sigma` = **RV30** (realized volatility — the fundamental physical estimate)
- `r` = 0.02 (approximate 2016-2020 average risk-free rate)
- `N` = 50 steps

<!-- Using RV30 as sigma is the meaningful choice for edge detection.
     When sigma=IV, CRR reproduces the market price by construction
     (since IV is back-solved from market price). Using RV30 gives
     what the option SHOULD cost if historical volatility persisted,
     revealing the vol risk premium the crowd pays. -->

```
edge_L1 = (V_model_rv - V_market) / V_market
```

### Step 3 — Layer 2 Edge Signal

Load trained models via `p_estimator.load("call")` and
`p_estimator.load("put")`. Apply `predict_p(bundle, X_raw)` to the
same sampled contracts using the pre-engineered feature columns.

```
q_market  = P_mid / STRIKE       (puts)
q_market  = C_mid / UNDERLYING   (calls)
edge_L2   = p_independent - q_market
```

<!-- q_market is a rough but consistent proxy for market-implied ITM
     probability. It matches the formula used in backtest.py so the
     comparison is internally consistent. -->

### Step 4 — Regime Labels

Apply `bias_detector.compute_atm_iv()` and `compute_regime()` to the
full dataset to get a daily regime map, then join to the sampled
contracts on QUOTE_DATE.

### Step 5 — Comparison Plots

Generate `project/outputs/l1_vs_l2_comparison.png` with four panels:

1. **Edge Scatter** — L1 edge (x) vs L2 edge (y), colored by regime,
   with quadrant shading and Pearson correlation annotated.
2. **Agreement Breakdown** — Bar chart of % contracts in each quadrant
   (both agree SELL, both agree BUY, disagree).
3. **Actual ITM Rate by Zone** — When both models agree the market
   overprices, does the option actually expire OTM more often?
   Validates that the agreement signal has predictive content.
4. **Regime-Conditional Correlation** — Pearson r in normal vs herding
   regime, showing whether crowd bias amplifies both signals together.

---

## Animated Simulation

<!-- ============================================================
     ANIMATION DESIGN
     ----------------
     The animation (aapl_crr_comparison.html) shows the CRR
     binomial tree being built for REAL AAPL contracts selected
     from the comparison analysis. This makes the Layer 1 math
     concrete and ties it directly to the comparison finding.

     Two contracts are animated:
       Contract A -- herding regime, both models agree market overprices
       Contract B -- normal regime, both models agree pricing is fair

     Each contract goes through four phases:
       Phase 1: Contract profile (parameters from AAPL dataset)
       Phase 2: Forward pass -- building the stock price lattice
       Phase 3: Terminal payoffs (ITM nodes colored green)
       Phase 4: Backward induction -- V values propagating back
       Phase 5: Result -- V_model_rv vs V_market + L2 comparison

     The right-side info panel shows the Layer 2 signal updating
     alongside the tree, so both models are visible simultaneously.
     ============================================================ -->

### Contract Selection Criteria

**Contract A (Herding, overpriced):**
- Regime = herding
- `edge_L1 < -0.15` (CRR says market overprices by > 15% using RV30)
- `edge_L2 < -0.03` (L2 also says market overprices)
- DTE between 10 and 90 days
- Near-ATM: moneyness between 0.90 and 1.10
- V_market > $0.50 (avoid deep OTM noise)

**Contract B (Normal, fair pricing):**
- Regime = normal
- `|edge_L1| < 0.08` (CRR says fair)
- `|edge_L2| < 0.04` (L2 says fair)
- Same DTE and moneyness constraints

### Animation Output

- **File:** `aapl_crr_comparison.html`
- **Frames:** ~28 frames (intro + 11 per contract + comparison)
- **Controls:** Play/Pause, Step, Slider, Speed, Contract A/B jump buttons
- **Info panel:** Shows contract parameters, V_model_rv, V_market,
  edge_L1, p_independent, q_market, edge_L2, and regime label on
  every frame so the viewer always knows where both signals stand.

---

## Known Limitations

<!-- ============================================================
     These limitations must be cited when presenting results.
     They are documented here to ensure they appear in Section 7
     of the research report.
     ============================================================ -->

- **No dividend adjustment.** Layer 1's CRR tree omits the continuous
  dividend yield term. AAPL paid ~0.6-1.0% annually over 2016-2020,
  causing systematic put underpricing of -10.76% and call overpricing
  of +6.58% (measured in aapl_crr_validation.py). This biases edge_L1
  for puts in a known direction: it makes puts appear less overpriced
  than they are. The bias is quantified and documented rather than
  corrected, per the AMD project scope.

- **Shared training data.** The Layer 2 XGBoost model was trained on
  80% of the full AAPL dataset. When edge_L2 is computed on a fresh
  10% sample, some contracts may overlap with training data, slightly
  inflating agreement due to overfitting. This is noted but not
  corrected since the comparison is methodological rather than a
  held-out generalization test.

- **q_market is a rough proxy.** The market-implied probability formula
  (P_mid / STRIKE for puts) is a simplified approximation, not a true
  risk-neutral probability. It serves as a consistent relative measure
  but should not be interpreted as a precise probability estimate.

- **Risk-free rate is constant.** A flat r = 2% is used for all
  contracts across 2016-2020. The actual Fed Funds rate ranged from
  0.5% to 2.5%, introducing small pricing errors in Layer 1.

---

## Files Created by This Plan

<!-- These are the ONLY new files created. No existing pipeline
     files are modified. -->

| File | Type | Purpose |
|---|---|---|
| `PLAN3.md` | Documentation | This file |
| `project/layer1_vs_layer2.py` | Python script | Runs comparison, saves plots |
| `make_aapl_crr_animation.py` | Python script | Generates animated HTML |
| `project/outputs/l1_vs_l2_comparison.png` | Plot | 4-panel comparison figure |
| `aapl_crr_comparison.html` | HTML | Animated CRR tree simulation |

---

## Build Commands

<!-- Run these in order. Both layers must already be built
     (make run-layer2 must have completed successfully). -->

```bash
# Step 1: Generate comparison plots
.venv/bin/python project/layer1_vs_layer2.py

# Step 2: Generate animated HTML simulation
.venv/bin/python make_aapl_crr_animation.py
```

Or add to Makefile:
```bash
make run-comparison
```

---

## How to Read the Results

<!-- This section explains how to interpret each plot for the
     research report. Written now so nothing is left ambiguous
     when writing Section 6 (Backtest Results). -->

**Edge scatter (Panel 1):**
A positive Pearson correlation means both models detect the same
mispricing direction. A correlation near zero means they are
independent and the agreement in Quadrant III is coincidental.
A negative correlation would mean the models systematically disagree.

**Agreement breakdown (Panel 2):**
If > 50% of contracts fall in Quadrant III (both say SELL), this
confirms the volatility risk premium is persistent and detectable by
both independent methods -- a key finding for the research report.

**Actual ITM rate by zone (Panel 3):**
If contracts in the "both SELL" zone have a lower actual ITM rate
than contracts in the "disagree" zone, the combined signal has
genuine predictive content beyond either model alone.

**Regime-conditional correlation (Panel 4):**
If the correlation is higher during herding regime than normal regime,
this confirms that crowd behavioral bias amplifies the same signal in
both the mathematical and ML approaches simultaneously.
