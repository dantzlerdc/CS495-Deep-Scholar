---
title: |
  CRR Binomial Pricing Calculator --- User Guide
subtitle: |
  Cox-Ross-Rubinstein American Option Pricer · Kelly Criterion Sizing · Monte Carlo Simulation
author: CS495 Deep Scholar Project
date: May 2026
documentclass: article
fontsize: 11pt
geometry: margin=1in
toc: true
toc-depth: 3
numbersections: true
colorlinks: true
linkcolor: NavyBlue
urlcolor: NavyBlue
toccolor: NavyBlue
header-includes:
  - \usepackage{fancyhdr}
  - \usepackage{lastpage}
  - \pagestyle{fancy}
  - \fancyhf{}
  - \fancyhead[L]{CRR Binomial Pricing Calculator}
  - \fancyhead[R]{User Guide}
  - \fancyfoot[C]{\thepage}
  - \renewcommand{\headrulewidth}{0.4pt}
  - \usepackage{titling}
  - \pretitle{\begin{center}\Large\bfseries}
  - \posttitle{\end{center}}
  - \usepackage{float}
  - \floatplacement{figure}{H}
  - \usepackage{titlesec}
  - \usepackage{etoolbox}
  - \definecolor{BCBlue}{HTML}{003D79}
  - |
    ```{=latex}
    \titleformat{\section}{\Large\bfseries\color{BCBlue}}{\thesection}{1em}{}[{\color{BCBlue}\titlerule[2pt]}]
    \titlespacing*{\section}{0pt}{20pt}{14pt}
    \pretocmd{\section}{\newpage}{}{}
    \setlength{\fboxsep}{0pt}
    \setlength{\fboxrule}{0.5pt}
    \let\oldincludegraphics\includegraphics
    \renewcommand{\includegraphics}[2][]{\fbox{\oldincludegraphics[#1]{#2}}}
    ```
---

# Overview

The CRR Binomial Pricing Calculator is an interactive web application built with Streamlit that implements the Cox-Ross-Rubinstein (CRR) binomial option pricing model. It prices American-style equity options, computes the full set of option Greeks, applies the Kelly Criterion to suggest position sizes, and runs a Monte Carlo P\&L simulation --- all in real time from a single browser tab.

## What the App Does

| Feature | Description |
|---------|-------------|
| American Option Pricing | Computes fair value using the CRR recombining binomial tree |
| Greeks | Delta, Gamma, Theta, Vega, and Rho via finite-difference bumping |
| Edge Detection | Compares model price to market price; flags mispricings |
| Regime Analysis | Classifies the volatility environment (Normal / Herding / Compression) |
| Kelly Sizing | Converts edge into Full, Half, and Quarter Kelly position sizes |
| Monte Carlo Simulation | Projects cumulative P\&L over 1,000 simulated trades |
| Tree Animation | Animated binomial tree showing forward stock propagation and backward option induction |
| Embedded User's Guide | This document is bundled inside the app on the User's Guide tab for offline reference |

## Intended Audience

The tool is designed for finance students, quantitative traders, and researchers who understand basic options mechanics and want a transparent, step-by-step view of how a CRR model prices a contract and sizes a trade.

# Getting Started

## Prerequisites

Install the required Python packages before launching:

```bash
pip install streamlit yfinance numpy pandas matplotlib
```

The application also requires the project-local modules located in the `project/` subdirectory:

- `project/tree.py` --- CRR binomial tree engine
- `project/greeks.py` --- Greek computation via finite-difference bumping
- `project/kelly.py` --- Kelly Criterion and edge-to-probability mapping
- `project/simulation.py` --- Monte Carlo P\&L simulator

## Launching the App

From the project root directory, run:

```bash
streamlit run crr_binomial_pricing_calculator.py
```

Streamlit will open a browser tab automatically (typically at `http://localhost:8501`). The app uses a wide layout for maximum chart visibility.

![Initial view of the calculator on launch: the sidebar (Contract Parameters) is visible on the left with the default values pre-populated; the main content area shows the title banner, the seven-tab navigation strip, and a callout asking you to click **Calculate**.](UsersGuideScreens/crrr-calculator-frontscreen.png){width=70%}

The very first view --- before you have changed any defaults or pressed **Calculate** --- is shown above. The sidebar holds the Contract Parameters block (Ticker, Option Type, Action, Underlying Price, Strike, Market Price, Implied Volatility), pre-populated with sensible defaults. The main content area shows the title, the seven-tab navigation strip, and a callout reading *"Enter your contract parameters in the sidebar and click Calculate to populate this tab."* No calculation has run yet --- the sidebar holds your inputs, ready for execution.

## Quick-Start Workflow

1. Enter your ticker symbol in the sidebar (e.g., `AAPL`).
2. Select Option Type (`put` or `call`) and Action (`buy` or `sell`).
3. Fill in the contract parameters: underlying price, strike, market price, and implied volatility.
4. Set Days to Expiration, risk-free rate, and number of CRR steps.
5. Configure Kelly Parameters (capital and minimum edge threshold).
6. Click **Calculate**.
7. Navigate the seven tabs to explore pricing, Greeks, edge, sizing, simulation, the animated tree, and the embedded user's guide.

# Sidebar Parameters

All inputs are on the left sidebar. The app re-runs calculations only when you press **Calculate** --- sidebar changes alone do not trigger recalculation.

## Contract Parameters

![Sidebar top section: Contract Parameters --- ticker, option type, action, underlying price, strike, market price, and implied volatility.](UsersGuideScreens/crr-calc-sidepanel-part1.png){height=6in}

The top section of the sidebar collects everything that defines the option contract itself.

### Ticker (for RV30 lookup)

- **Purpose:** The equity ticker symbol used to fetch six months of historical close prices from Yahoo Finance.
- **Used for:** Computing the 30-day and 60-day Realized Volatility (RV30, RV60), which feeds the Regime analysis in the Edge & Signal tab.
- **Note:** The ticker does not need to match the option you are pricing. You can price any hypothetical contract while pulling realized vol for any symbol. Internet connectivity is required for the RV lookup; if the fetch fails the app continues without regime data.

### Option Type

- **put** --- A contract giving the holder the right to sell the underlying at the strike price. The intrinsic value is $\max(K - S, 0)$.
- **call** --- A contract giving the holder the right to buy the underlying at the strike price. The intrinsic value is $\max(S - K, 0)$.

### Action

- **buy** --- You are long the option (paid the premium). A positive edge (model > market) supports buying.
- **sell** --- You are short the option (collected the premium). A negative edge (model < market) supports selling.

The Action field determines how the Kelly win probability is derived and whether the trading signal reads **BUY**, **SELL**, or **NO TRADE**.

### Underlying Price (S \$)

The current market price of the underlying stock in dollars. This is the spot price $S_0$ used as the root node of the binomial tree.

### Strike Price (K \$)

The contractual price at which the option holder may exercise. For puts, exercise is profitable when $S < K$; for calls, when $S > K$.

### Market Price (V_market)

The actual market premium of the option (the mid or last price from your broker). The model compares its theoretical fair value against this number to compute edge:

$$\text{Edge} = \frac{V_{\text{model}} - V_{\text{market}}}{V_{\text{market}}}$$

### Implied Volatility (IV)

The annualized volatility implied by the market premium, expressed as a decimal (e.g., `0.30` = 30%). This is the $\sigma$ parameter that drives the up/down factors of the binomial tree. You must provide this manually --- the app does not back-solve IV from the market price.

## Time and Rate Parameters

![Sidebar middle section: Time and rate inputs (DTE, risk-free rate, CRR steps) and the Kelly Parameters block (capital, minimum edge threshold).](UsersGuideScreens/crr-calc-sidepanel-part2.png){height=6in}

The middle section of the sidebar holds the time, rate, and step-count parameters, then transitions into the Kelly inputs.

### Days to Expiration (DTE)

Calendar days remaining until the option expires. Internally converted to years:

$$T = \frac{\text{DTE}}{365}$$

### Risk-free Rate (r)

The continuously compounded annualized risk-free interest rate, expressed as a decimal (e.g., `0.053` = 5.3%). Use the current 3-month or 1-year Treasury yield as a proxy.

### CRR Steps (N)

The number of time steps in the binomial tree used for actual pricing. More steps increase accuracy at the cost of compute time:

| N | Accuracy | Compute time |
|---|----------|--------------|
| 10--25 | Low (educational only) | Instant |
| 50--100 | Good for most contracts | < 1 second |
| 150--200 | High precision | 1--3 seconds |
| 500 | Maximum | 5--15 seconds |

A value of **100** is the recommended default for routine use.

## Kelly Parameters

### Capital (\$)

Your total tradeable capital in dollars. The Kelly sizing output scales the optimal bet fraction against this number to produce a dollar position size.

### Min Edge Threshold

The minimum absolute edge (as a decimal) required before the model recommends a trade. If $|\text{Edge}| < \text{threshold}$, all Kelly fractions are set to zero and the signal reads **NO TRADE**. The default of `0.02` (2%) filters out noise near fair value.

## Tree Animation

![Sidebar bottom section: Tree Animation sliders (display steps, animation speed) and the Calculate button.](UsersGuideScreens/crr-calc-sidepanel-part3.png){width=3in}

The final section of the sidebar configures the binomial tree animation on Tab 6 and presents the **Calculate** button that runs the full pipeline.

### Display Steps (N)

The number of tree steps used only for the animated visualization (Tab 6). The actual pricing always uses the full N from the CRR Steps field above. Smaller display N (4--8) produces readable node labels; larger values (10--12) show tree structure at the cost of label legibility.

### Speed (sec/step)

Pause duration between animation frames. Lower values (0.05--0.10) produce fast animations; higher values (0.5--1.0) are better for demonstrations or teaching.

# Tab 1 --- Pricing

This tab presents the primary output of the CRR model and two diagnostic charts. Every tab opens with an **About this screen** expander that summarizes what the screen shows, why it matters, and where the underlying logic is implemented in the research codebase.

![Tab 1 "About this screen" expander: the orientation panel for the Pricing tab.](UsersGuideScreens/crr-calc-tab-pricing-about-section.png)

## About This Screen

**What this shows.** The Cox--Ross--Rubinstein American binomial pricer applied to your sidebar contract: **Model vs Market** (CRR fair value `V_model` vs market premium `V_market`), **Convergence** of `V_model` as lattice depth `N` grows, and the **Early Exercise Boundary** `S*` below which exercising an American put dominates holding.

**Why it matters.** Pricing accuracy is hypothesis **H1** of the research --- every downstream decision (edge detection, regime classification, Kelly sizing) assumes `V_model` is calibrated. The boundary panel is the analytic capability that justifies the CRR lattice over the closed-form Black--Scholes model for American options.

**Research link.** Implements *§3.4.1 --- Layer 1: CRR Pricing Engine*, validated in *§4.2--§4.4* of the capstone report. Maps to Project 6's "true `p` estimator" deliverable.

## Metric Row

Three headline metrics appear at the top of the tab:

| Metric | Description |
|--------|-------------|
| CRR Model Price | The theoretical fair value computed by the binomial model |
| Market Price | The V_market you entered in the sidebar |
| % Error | $(V_{\text{model}} - V_{\text{market}}) / V_{\text{market}} \times 100$ |

A **positive** % Error means the model believes the contract is underpriced by the market. A **negative** % Error means the model believes it is overpriced.

## Model vs Market Bar Chart

![Model vs Market bar chart: CRR model price (blue) vs observed market premium (orange) with dollar labels above each bar.](UsersGuideScreens/crr-calc-tab-pricing-model-vs-market-barchart.png)

A side-by-side bar chart comparing the CRR model price (blue) and the market price (gold). Dollar values are printed above each bar.

**How to interpret:** The visual gap between the two bars is proportional to the edge. A large gap warrants careful review of your IV input --- if the gap is consistently large, your implied volatility may not accurately reflect what the market is pricing.

## CRR Convergence vs Step Count Chart

![CRR Convergence vs Step Count: model price plotted against N = 5, 10, 25, 50, 100, 150, 200, with the market price overlaid as a dashed reference line.](UsersGuideScreens/crr-calc-tab-pricing-convergence-steps.png)

A line chart showing how the model price changes as N increases through the values `[5, 10, 25, 50, 100, 150, 200]`. The market price is drawn as a horizontal dashed line.

**How to interpret:**

- **Oscillating convergence** is normal for binomial models. The price alternates slightly between even and odd step counts before stabilizing.
- **Convergence to a value near V_market** suggests the IV you entered is consistent with market consensus.
- **Convergence to a value far from V_market** is the source of the edge signal --- the model and market disagree on fair value at all step counts, which is more meaningful than a single-step result.
- Look for stabilization by N = 50--100. If the price is still moving significantly at N = 150, consider that the option may be deep in- or out-of-the-money, or that DTE is very short.

## Early Exercise Boundary (Puts Only)

![Early Exercise Boundary: critical S* (amber dots) plotted against days-from-today, with the current spot $S = \$200$ shown as a dashed blue line.](UsersGuideScreens/crr-calc-tab-pricing-early-exercise-boundary.png)

For American put options, a third chart appears below the two main charts. It plots the critical stock price $S^*$ at each time step --- the threshold below which immediate exercise is optimal.

**How to interpret:**

- The boundary is plotted in amber dots, with a dashed blue line at your current spot price $S$.
- **If $S$ is above all amber dots:** The put is not worth exercising early at any node --- time value exceeds intrinsic value everywhere.
- **If $S$ approaches or crosses the boundary:** Early exercise may be rational. The exact crossover indicates the range of stock prices at which you should consider exercising rather than holding.
- The boundary typically slopes downward toward expiration: as DTE shrinks, early exercise becomes optimal at higher stock prices.
- American calls on non-dividend-paying stocks are **never** optimally exercised early, which is why this chart only appears for puts.

# Tab 2 --- Greeks

Option Greeks measure the sensitivity of the option price to changes in underlying variables. The app computes all five first-order Greeks using **finite-difference bumping** --- running the CRR model at slightly perturbed inputs and computing the numerical derivative.

![Tab 2 "About this screen" expander: the orientation panel for the Greeks tab.](UsersGuideScreens/crr-calc-tab-greeks-about-section.png)

## About This Screen

**What this shows.** The five standard option Greeks --- $\Delta$ (Delta), $\Gamma$ (Gamma), $\Theta$ (Theta), $\nu$ (Vega), $\rho$ (Rho) --- plus $\sigma$ (IV, implied volatility input). Greeks are computed via centered finite differences over the full `N=100`-step CRR lattice. The table provides plain-English interpretation of each Greek's per-unit effect.

**Why it matters.** Greeks decompose how the option price responds to changes in spot, volatility, time, and interest rates --- the standard tool for hedging and risk decomposition. Validating model Greeks against the platform-reported Fidelity values (target: ±10\% per Greek) confirms the lattice's partial derivatives are correctly computed.

**Research link.** Implements *§3.4.2 --- Layer 1: Greeks*, validated in *§4.2.2 --- Break-Even and Greeks Validation*. Supports Project 6's "risk controls" and "decision theory" requirements.

## Greek Definitions and Interpretations

![Greeks tab full view: top metric strip for the five Greeks plus the IV input, followed by the plain-English interpretation table for each Greek.](UsersGuideScreens/crr-calc-tab-greeks.png)

The bottom table restates each Greek with a plain-English interpretation column. Use this when presenting results to a non-technical audience or double-checking the sign and magnitude of each sensitivity. The five Greek subsections below give the formal definition, sign conventions, and intended use of each.

### Delta ($\Delta$)

$$\Delta = \frac{\partial V}{\partial S}$$

The change in option value per \$1 move in the underlying stock.

| Option | Sign | Typical Range |
|--------|------|---------------|
| Long call | Positive | 0 to +1 |
| Long put | Negative | $-1$ to 0 |

**Interpretation:** A delta of +0.45 means your long call gains approximately \$0.45 for every \$1 the stock rises. A delta of $-0.60$ means your long put gains \$0.60 for every \$1 the stock falls.

**Use:** Delta is the primary hedge ratio. To delta-hedge a long call position in 1 contract (100 shares), short $\Delta \times 100$ shares of the underlying.

### Gamma ($\Gamma$)

$$\Gamma = \frac{\partial^2 V}{\partial S^2} = \frac{\partial \Delta}{\partial S}$$

The rate of change of Delta per \$1 move in the underlying.

**Interpretation:** A gamma of 0.05 means if the stock rises \$1, your delta increases by 0.05. High gamma positions (near-the-money, short DTE) have rapidly changing deltas and require frequent hedge rebalancing.

**Use:** Long options have positive gamma (you benefit from large moves in either direction). Short options have negative gamma (you lose on large moves). Gamma peaks at-the-money and near expiration.

### Theta ($\Theta$)

$$\Theta = \frac{\partial V}{\partial t}$$

The change in option value per calendar day passing, with all else equal.

**Interpretation:** A theta of $-0.05$ means the option loses approximately \$0.05 of value each day purely from time decay. Theta is almost always negative for long options (you pay for time) and positive for short options (you collect decay).

**Use:** Theta accelerates as expiration approaches, particularly for at-the-money options. A theta of $-0.10$ with 30 DTE will increase (in magnitude) as DTE shrinks toward zero.

### Vega ($\nu$)

$$\nu = \frac{\partial V}{\partial \sigma}$$

The change in option value per 1 vol-point (0.01) move in implied volatility.

**Interpretation:** A vega of 0.08 means if IV rises from 30% to 31% (a 0.01 move), the option gains \$0.08. Vega is always positive for long options (you benefit from rising volatility) and negative for short options.

**Use:** Vega is largest for at-the-money, longer-dated options. If you have a directional view on volatility (not just price), vega tells you how sensitive your position is to that view.

### Rho ($\rho$)

$$\rho = \frac{\partial V}{\partial r}$$

The change in option value per 100 basis point (1%) move in the risk-free rate.

**Interpretation:** A rho of 0.12 means if interest rates rise 1%, the option gains \$0.12. Rho is positive for calls (higher rates increase call value via cost of carry) and negative for puts.

**Use:** Rho is the least impactful Greek for most short-dated options but matters for longer-dated LEAPS or in volatile interest rate environments.

# Tab 3 --- Edge & Signal

This tab synthesizes the pricing output into a trading recommendation.

![Tab 3 "About this screen" expander: the orientation panel for the Edge & Signal tab.](UsersGuideScreens/crr-calc-tab-edge-about-section.png)

## About This Screen

**What this shows.** The mispricing **edge** = `(V_model − V_market) / V_market`, expressed as a percentage; a categorical **trade signal** (BUY / SELL / NO TRADE) gated by the min-edge threshold; and the **volatility regime** (NORMAL / HERDING / COMPRESSION) derived from the IV/RV30 ratio. The horizontal gauge shows the edge magnitude with the no-trade zone shaded.

**Why it matters.** This is the bridge from pricing to trading. The regime card surfaces the project's central finding: in the **herding regime**, two completely independent models (CRR and XGBoost) agree on mispricing direction (Pearson $r = 0.413$, $p = 2.4 \times 10^{-10}$), while in the normal regime correlation is statistically zero --- a Simpson's Paradox-type result.

**The Layer-2 XGBoost classifier.** The CRR engine (Layer 1) is a deterministic no-arbitrage pricer. Layer 2 trains a **gradient-boosted decision tree ensemble** (XGBoost 2.0) on 47,578 historical AAPL contracts (2016--2020) to predict the *binary* ITM/OTM expiration outcome. Crucially, the L2 model uses **realized 30-day volatility (RV30) in place of implied volatility** as its volatility feature --- making it mathematically and informationally independent of Layer 1. XGBoost was chosen over logistic regression (too rigid for nonlinear interactions like moneyness × DTE) and neural networks (overkill for this dataset size, harder to calibrate). Feature importances by gain: **moneyness 38\%**, DTE 24\%, RV-IV spread 17\%, volume/OI ratio 11\%, bid-ask spread 10\%. The classifier is calibrated via **Platt scaling** on a held-out validation fold, producing a **Brier score of 0.211** --- below the 0.25 naive baseline (always predict 0.5) and below the market-implied benchmark.

**Cross-validation insight.** Because L1 and L2 share *no inputs and no training signal*, their strong herding-regime correlation cannot be a calibration artifact. It is direct evidence that both models independently detect the same crowd-overpricing bias --- the strongest result of the research.

**Research link.** Implements *§3.4.3 (Edge)*, *§3.4.5 (Layer 2 --- Independent Probability Estimator)*, *§3.4.6 (Crowd Bias Detector)*; cross-validation result in *§4.7*, feature importance in *§4.9*, Brier validation in *§4.10.2*. Maps to Project 6's "majority bettor / Bet-AI crowd bias detector" deliverable.

## Metric Row

| Metric | Meaning |
|--------|---------|
| Edge | $(V_{\text{model}} - V_{\text{market}}) / V_{\text{market}} \times 100\%$ --- positive means model thinks the option is cheap |
| IV | The implied volatility you entered |
| RV30 | 30-day annualized realized volatility fetched from Yahoo Finance |

## Trading Signal Banner

The large colored banner shows one of three signals --- BUY, SELL, or NO TRADE --- with a brief reason line beneath it. The three states are shown below.

![BUY signal banner (green): "Model price > market price --- contract appears underpriced".](UsersGuideScreens/crr-calc-tab-edge-green-buy-banner.png)

![SELL signal banner (navy): "Model price < market price --- contract appears overpriced".](UsersGuideScreens/crr-calc-tab-edge-blue-sell-banner.png)

![NO TRADE signal banner (gray): "Direction mismatch --- edge favours the opposite action" or "Edge is below the minimum threshold".](UsersGuideScreens/crr-calc-tab-edge-grey-no-trade-banner.png)

| Signal | Color | Meaning |
|--------|-------|---------|
| **BUY** | Green | Edge > threshold AND action = buy (model price > market price) |
| **SELL** | Navy | Edge < $-$threshold AND action = sell (model price < market price) |
| **NO TRADE** | Gray | Edge within the no-trade zone, or direction mismatch |

**Important caveat:** The signal assumes your IV input is accurate and that the CRR model is the correct pricing engine. If your IV differs significantly from the market's implied volatility, the edge may be an artifact of the input rather than a genuine mispricing.

## Regime Banner

When RV30 data is successfully fetched, a second colored banner appears showing the current volatility regime, defined by the ratio IV/RV30. The three regime banners in their distinct color treatments are shown below.

![HERDING REGIME banner (burnt orange): IV / RV30 = 1.48, "Crowd overbidding inflates premiums above CRR fair value".](UsersGuideScreens/crr-calc-tab-edge-herding.png)

![NORMAL REGIME banner (green): IV / RV30 = 0.86, "Efficient pricing, premiums reflect historical uncertainty without systemic overbidding".](UsersGuideScreens/crr-calc-tab-edge-normal-regime.png)

![COMPRESSION REGIME banner (sky blue): IV / RV30 = 0.49, "Market is underpricing volatility relative to recent history".](UsersGuideScreens/crr-calc-tab-edge-compression-regime.png)

| Ratio | Regime | Color | Meaning |
|-------|--------|-------|---------|
| > 1.20 | **HERDING** | Burnt orange | Market is paying significantly more than historical vol justifies. Sellers have an edge; buyers may be overpaying for protection. |
| 0.80 -- 1.20 | **NORMAL** | Green | IV is in line with recent realized vol. The market is pricing uncertainty without systematic overbidding or underbidding. |
| < 0.80 | **COMPRESSION** | Sky blue | Market is pricing in less vol than history suggests. Options appear cheap relative to recent moves; buyers may have an edge. |

**How to use regime with the signal:** A BUY signal in a COMPRESSION regime is more compelling --- you are buying cheap protection in a market that is underpricing risk. A SELL signal in a HERDING regime is similarly reinforced --- you are collecting inflated premiums.

## Edge Gauge Bar Chart

![Edge gauge horizontal bar chart: the edge value with the no-trade zone shaded in purple, bounded by the $\pm$ min-edge threshold lines.](UsersGuideScreens/crr-calc-tab-edge-horizontal-gauge.png)

A horizontal bar chart displays the edge value on a numeric axis. Two vertical dashed lines mark the no-trade zone boundaries at $\pm\text{min\_edge}$, with the zone shaded in purple.

**How to interpret:**

- **Bar inside the purple zone:** Edge is too small to act on --- could be noise, transaction costs, or bid-ask spread.
- **Bar extends right (positive):** Model believes the option is underpriced; the longer the bar, the stronger the buy signal.
- **Bar extends left (negative):** Model believes the option is overpriced; the longer the bar, the stronger the sell signal.
- Compare the bar length to the no-trade zone width. A bar that barely clears the threshold is a marginal signal; one that is three times the threshold is substantially more conviction.

# Tab 4 --- Kelly Sizing

The Kelly Criterion is a mathematically optimal formula for allocating capital to a bet with a known edge and win probability.

![Tab 4 "About this screen" expander: the orientation panel for the Kelly Sizing tab.](UsersGuideScreens/crr-calc-tab-kelly-about-section.png)

## About This Screen

**What this shows.** Position sizing recommendations under three variants of the **Kelly Criterion**: **Full Kelly** (`f* = (p·b − q)/b`), **Half Kelly** (`f*/2`), and **Quarter Kelly** (`f*/4`). The bar chart visualizes each fraction as a percentage of capital; the table translates fractions into dollar amounts based on your sidebar capital.

**Why it matters.** The Kelly Criterion (Kelly, 1956; Thorp, 1969) is the mathematically optimal answer to "given an edge, how much should I bet?" Full Kelly maximizes long-run growth but exhibits high variance; fractional Kelly (MacLean et al., 2010) trades a modest expected-growth reduction for substantially lower drawdown --- the practical default for any real position sizer.

**Layer-2 connection.** The win probability `p` used to compute `f*` can be derived either from the CRR edge (Layer 1, the source in this calculator) or from the **XGBoost classifier's calibrated probability** $\hat{p}_{\text{model}}$ (Layer 2). The classifier provides a *direct* probability estimate rather than an inferred one --- useful when the market price diverges materially from the model. In the walk-forward backtest, half-Kelly sizing applied to L2's calibrated probability produced the **\$2.9M cumulative P\&L** result reported on the Monte Carlo tab.

**Research link.** Implements *§3.4.3 --- Mispricing Edge and Kelly Sizing*. Tests hypothesis **H3** in *§4.8*: fractional Kelly outperforms full Kelly in risk-adjusted backtest.

## Mathematical Foundation

The standard Kelly formula for a binary bet with a 1:1 payoff is:

$$f^* = p - q = 2p - 1$$

where $p$ is the win probability and $q = 1 - p$ is the loss probability.

The app derives $p_{\text{win}}$ from the edge:

$$p_{\text{win}} = \text{clip}\left(0.5 + \frac{\text{edge}}{2},\ 0.01,\ 0.99\right)$$

This maps a zero-edge position to 50% win probability (coin flip) and scales linearly from there.

## Kelly Variants

The app computes three variants to address the practical over-aggressiveness of full Kelly:

| Variant | Fraction | Description |
|---------|----------|-------------|
| Full Kelly | $f^*$ | Theoretically optimal but maximizes volatility of outcomes |
| Half Kelly | $f^*/2$ | Widely preferred in practice --- halves drawdown risk while retaining most of the growth |
| Quarter Kelly | $f^*/4$ | Conservative; appropriate for uncertain edge estimates or high-variance payoffs |

## Reading the Kelly Table

![Kelly Sizing table: Full / Half / Quarter rows with fraction, percent of capital, dollar amount, and trade signal columns.](UsersGuideScreens/crr-calc-tab-kelly-part2.png)

The table shows, for each variant:

- **Fraction (f\*):** The decimal fraction of total capital to allocate.
- **% of Capital:** Same value expressed as a percentage.
- **Dollar Amount:** Fraction $\times$ Capital. This is the maximum recommended position size in dollars, not the number of contracts.
- **Trade Signal:** Repeats the BUY / SELL / NO TRADE from Tab 3.

When all fractions are `0.0000` (NO TRADE), the info box reminds you that edge is below the threshold and no position is recommended.

## Kelly Bar Chart

![Kelly Position Sizing bar chart: Full Kelly (green), Half Kelly (blue), and Quarter Kelly (orange) shown as percentages of capital with the value labelled on each bar.](UsersGuideScreens/crr-calc-tab-kelly-bar-chart.png)

Three bars (green, navy, gold) show the Full, Half, and Quarter Kelly fractions as percentages of capital. Use this chart to quickly visualize the sizing difference between variants.

**How to interpret:**

- A Full Kelly bar at 8% with \$100,000 capital means the model recommends risking up to \$8,000 on this trade.
- Use **Half Kelly** (4%) as your practical starting point.
- If the Kelly fraction exceeds 20--25% of capital on a single option trade, double-check your edge estimate --- very high fractions often indicate an unusually extreme edge or an input error.

# Tab 5 --- Monte Carlo Simulation

The Monte Carlo tab projects the long-run P\&L trajectory of repeatedly applying the Kelly-sized strategy across 1,000 simulated trades.

![Tab 5 "About this screen" expander: the orientation panel for the Monte Carlo tab.](UsersGuideScreens/crr-calc-tab-monte-carlo-about-section.png)

## About This Screen

**What this shows.** A **Monte Carlo simulation** of 1,000 hypothetical trades drawn from the empirical edge distribution (seed=42), with cumulative profit-and-loss curves overlaid for the three Kelly sizing variants. The summary table reports hit rate, total P\&L, max drawdown, and the annualized Sharpe ratio for each variant.

**Why it matters.** A single-trade edge means little; persistent positive expected value across many trades is what matters. This Monte Carlo isolates the Layer-1 pipeline's behavior in isolation. The full **Layer-1 + Layer-2 walk-forward backtest** --- applying the CRR pricer, the XGBoost classifier, the regime detector, and the microstructure cost filter chronologically to four years of out-of-sample AAPL data --- produces **\$2.9M cumulative P\&L** with **max drawdown \< 15\%**, the project's headline empirical result.

**Layer-2's role in the backtest.** XGBoost's calibrated probability $\hat{p}_{\text{model}}$ (Brier 0.211, well-calibrated in the 0.3--0.7 range) drives the position-entry filter: only contracts where both L1 and L2 agree on direction *and* exceed the regime-conditional edge threshold trigger a trade. The regime detector raises that threshold from 2\% to 8\% in herding mode, throttling the policy to high-conviction trades --- which is exactly when the cross-model agreement is strongest.

**Research link.** Implements *§3.4.4 --- Layer 1: Monte Carlo Simulation*; full walk-forward result in *§4.8 / Figure 7*, statistical validation in *§4.10.3*. Maps to Project 6's "backtesting and simulation" deliverable.

## How the Simulation Works

For each of the 1,000 trades, the simulator:

1. Draws a random outcome (win or loss) using the Bernoulli distribution with $p_{\text{win}}$.
2. Applies the Kelly fraction to the current capital (the bet compounds --- a win increases capital; a loss reduces it).
3. Records the cumulative P\&L after each trade.

Only variants with Kelly fraction > 0 are simulated. If NO TRADE is signaled, the tab displays an info message instead of charts.

## Cumulative P&L Chart

![Monte Carlo Profit and Loss chart: cumulative P\&L over 1,000 trades for Full / Half / Quarter Kelly, with annualized Sharpe ratios shown in the legend.](UsersGuideScreens/crr-calc-tab-monte-carlo-part1.png)

Three colored curves show the cumulative P\&L path for Full Kelly (green), Half Kelly (navy), and Quarter Kelly (gold). The legend includes the **Annualized Sharpe Ratio** for each variant.

**How to interpret:**

- **Steeper upward slope** = higher expected growth rate (Full Kelly grows fastest in expectation).
- **Larger swings / deeper dips** = higher variance. Full Kelly can produce dramatic drawdowns even when the edge is positive.
- **Smoother curve** = lower variance. Quarter Kelly is the smoothest but grows most slowly.
- The Sharpe ratio (shown in the legend) normalizes return by volatility. A Sharpe > 1.0 is generally considered good; > 2.0 is strong. Compare Sharpes across variants to judge the risk-adjusted return tradeoff.

## Summary Statistics Table

![Monte Carlo summary statistics table: Hit Rate, Total P\&L, Max Drawdown, and Annualized Sharpe per variant.](UsersGuideScreens/crr-calc-tab-monte-carlo-part2.png)

Below the chart, a table reports four statistics for each variant.

| Statistic | Meaning |
|-----------|---------|
| Hit Rate | Fraction of the 1,000 simulated trades that were wins. Should be close to $p_{\text{win}}$ by the law of large numbers. |
| Total P\&L | Net profit or loss over all 1,000 simulated trades starting from the configured capital. |
| Max Drawdown | The largest peak-to-trough decline in cumulative P\&L. Measures worst-case interim loss. |
| Ann. Sharpe | Annualized Sharpe ratio: expected return divided by standard deviation of returns, scaled to annual. |

**How to use the table:**

- Compare **Max Drawdown** across variants. If Full Kelly drawdown exceeds your pain tolerance (e.g., > 30% of capital), use Half or Quarter Kelly.
- A **Total P\&L** that is negative despite a positive edge is possible in any single simulation run due to variance. Re-running the app can show a different path.
- The **Hit Rate** should cluster around $p_{\text{win}}$. If it diverges significantly, this is a random sample effect --- 1,000 trades is enough to reveal the distribution but not eliminate variance.

# Tab 6 --- Tree Animation

The Tree Animation tab provides an interactive visual explanation of how the CRR model actually computes an option price.

![Tab 6 "About this screen" expander: the orientation panel for the Tree Animation tab.](UsersGuideScreens/crr-calc-tab-tree-about-section.png)

## About This Screen

**What this shows.** An animated visualization of the **CRR binomial lattice** at a small display step count (N=5--12 for clarity; actual pricing uses your sidebar N). **Phase 1 (forward)** builds the stock price tree --- each node moves up by $u = e^{\sigma\sqrt{\Delta t}}$ or down by $d = 1/u$. **Phase 2 (backward induction)** replaces stock prices with option values, highlighting **early-exercise nodes in purple** where intrinsic value beats continuation.

**Why it matters.** The lattice is the central algorithm of the pricing engine, but normally invisible. This animation makes the math transparent and auditable: a user can see exactly how `V_model` is constructed from terminal payoffs back to today.

**Research link.** Visualizes *§2.2 (CRR foundational equations)* and *§3.4.1 (backward induction)*. Supports the **transparency** significance argument in *§1.4*.

## What the Binomial Tree Shows

![Tree Animation tab header: the display-step note, the node-color legend, and the "Animate Tree" button.](UsersGuideScreens/crr-calc-tab-tree-part1.png)

The CRR binomial model discretizes time into $N_{\text{disp}}$ steps. At each step, the stock price can move up by factor $u$ or down by factor $d$, where:

$$u = e^{\sigma\sqrt{\Delta t}},\quad d = \frac{1}{u},\quad \Delta t = \frac{T}{N}$$

This produces a **recombining lattice** --- an up move followed by a down move reaches the same node as a down move followed by an up move, keeping the tree from growing exponentially.

## Node Color Legend

| Color | Meaning |
|-------|---------|
| Gold | Root node at $t = 0$ --- today's stock price $S$ |
| Blue | Stock price nodes (forward pass --- showing where the stock can go) |
| Green | Option value nodes where holding is optimal (continuation value > intrinsic value) |
| Purple | Option value nodes where early exercise is optimal (intrinsic value > continuation value) |

## Animation Phases

Click **Animate Tree** to start the two-phase animation.

![Forward Pass complete: the binomial lattice fully populated with stock prices from $S_0 = \$200$ at $t=0$ to the terminal nodes 30 days out.](UsersGuideScreens/crr-calc-tab-tree-forward-pass.png)

**Phase 1 --- Forward Pass (left to right):** Stock price nodes are revealed column by column, simulating how the stock can evolve from today to expiration. Each node shows the dollar stock price at that step and state. This demonstrates the forward propagation of the underlying process.

![Backward Induction complete: option values populated across the lattice, with green nodes where holding dominates and purple nodes where early exercise dominates.](UsersGuideScreens/crr-calc-tab-tree-backward-pass.png)

**Phase 2 --- Backward Induction (right to left):** Starting at the terminal nodes (expiration), nodes flip from stock prices to option values. The backward induction computes:

$$V_{i,j} = \max\Bigl(\text{intrinsic}_{i,j},\ e^{-r\Delta t}\bigl[p \cdot V_{i+1,j} + (1-p) \cdot V_{i+1,j+1}\bigr]\Bigr)$$

where $p = (e^{r\Delta t} - d)/(u - d)$ is the risk-neutral probability.

- **Green nodes (hold):** The discounted expected future value exceeds intrinsic value --- it is better to keep the option alive.
- **Purple nodes (early exercise):** Intrinsic value exceeds the continuation value --- for American options, immediate exercise is optimal at this node.

## Static View

Without clicking Animate, the tree displays the full forward pass (all stock prices visible) as a static snapshot. This is useful for quickly checking tree structure at different step counts.

## How to Use the Tree Tab Effectively

1. Set $N_{\text{disp}}$ to 5--7 for a readable diagram with visible dollar labels.
2. Observe the purple early-exercise nodes on a deep in-the-money put. They cluster at the bottom-left of the tree, where the stock price has fallen well below strike.
3. For calls on non-dividend-paying stocks, you should see **no purple nodes at all** --- early exercise of American calls is never optimal in this model.
4. Slow the animation speed to 0.5--1.0 sec/step when explaining the model in a presentation.

# Tab 7 --- User's Guide

The seventh tab embeds this very document inside the calculator so the reference manual is always one click away --- no separate file open, no context switch out of the app.

![User's Guide tab: a download button at the top followed by an inline PDF viewer that shows the bundled user-guide document.](UsersGuideScreens/crr-calc-tab-users-guide.png)

## What This Tab Provides

The tab is structured into three elements, top to bottom:

1. **An orientation paragraph** that tells you the tab is the full reference manual and offers two ways to read it (download or inline).
2. **A primary "Download User's Guide (PDF)" button** that streams the bundled PDF file to your browser's normal download flow.
3. **An inline PDF viewer (iframe)** that renders the same PDF directly inside the tab so you can scroll, search, and follow the document outline without leaving the calculator.

The downloaded copy is the most recent build of `Users-Guide-CRR-Binomial-Pricing-Calculator.pdf` produced from `users_guide.md` via Pandoc; the embedded viewer shows the same bytes encoded inline.

## When to Use Each Path

- **Use the inline viewer** for quick lookups while you are working with the calculator (for example, checking the meaning of the Min Edge Threshold while sizing a trade). The viewer supports the browser's standard PDF controls --- zoom, find, page navigation, and the document-outline panel on the left.
- **Use the download button** when you want to read the guide offline, print it, share it with a collaborator, or annotate it in a dedicated PDF reader. The downloaded file is self-contained and includes the table of contents, the list of figures, and all cross-references.

## Notes and Caveats

- The PDF lives next to `crr_binomial_pricing_calculator.py` in the project root. If you move the calculator script, also move (or re-bundle) the user-guide PDF, or the tab will show an error pointing at the expected path.
- The User's Guide tab is always available --- it does not require pressing **Calculate** first. The other six tabs show a placeholder until calculations have run.
- Some browsers block embedded PDFs by default. If the inline viewer is blank but the download button still works, use the download path or check your browser's PDF settings.

# Mathematical Reference

## CRR Model Parameters

| Symbol | Formula | Description |
|--------|---------|-------------|
| $\Delta t$ | $T/N$ | Length of one time step (in years) |
| $u$ | $e^{\sigma\sqrt{\Delta t}}$ | Up factor --- stock price multiplier on an up move |
| $d$ | $1/u$ | Down factor --- stock price multiplier on a down move |
| $p$ | $(e^{r\Delta t} - d)/(u - d)$ | Risk-neutral up probability |
| disc | $e^{-r\Delta t}$ | One-period discount factor |

## Stock Price Lattice

$$S_{i,j} = S_0 \cdot u^{i-j} \cdot d^{j} \qquad i = 0, \ldots, N;\ j = 0, \ldots, i$$

where $i$ is the time step and $j$ is the number of down moves.

## Option Value Recursion

**Terminal payoff:**

$$V_{N,j} = \max(S_{N,j} - K,\ 0)\ \text{(call)},\quad V_{N,j} = \max(K - S_{N,j},\ 0)\ \text{(put)}$$

**Backward induction (American):**

$$V_{i,j} = \max\Bigl(\text{Intrinsic}_{i,j},\ \text{disc} \cdot \bigl[p\, V_{i+1,j} + (1-p)\, V_{i+1,j+1}\bigr]\Bigr)$$

## Edge and Kelly

$$\text{Edge} = \frac{V_{\text{model}} - V_{\text{market}}}{V_{\text{market}}}$$

$$p_{\text{win}} = \text{clip}(0.5 + \text{edge}/2,\ 0.01,\ 0.99)$$

$$f^* = 2 p_{\text{win}} - 1 \quad \text{(binary Kelly)}$$

## Realized Volatility

$$\text{RV30} = \hat\sigma\bigl(\{\ln(C_t / C_{t-1})\}_{t=1}^{30}\bigr) \times \sqrt{252}$$

where $C_t$ is the daily closing price.

# Common Questions and Troubleshooting

## "RV30 shows N/A"

The app could not fetch historical price data for the ticker you entered. Check:

- Ticker symbol spelling (use the exact Yahoo Finance symbol, e.g., `BRK-B` not `BRK.B`).
- Internet connectivity.
- Yahoo Finance may throttle requests; wait a few minutes and retry.

## "All Kelly fractions = 0"

Your edge is within the no-trade zone. Either:

- The market is fairly pricing this contract relative to your IV input.
- Your IV input is close to what the market is using, leaving no edge.
- Try lowering the **Min Edge Threshold** to see what the unconstrained Kelly fraction would be.

## The model price seems way off from market price

Verify that your **Implied Volatility** input is the market's actual IV for this contract, not a guess. The IV is the single most important input --- a 5% error in IV can move the model price by more than the edge you are measuring. Most brokers display IV alongside the option chain.

## The convergence chart does not flatten out

For very short-dated options (DTE < 5) or deep in-the-money options, the binomial model can converge slowly or oscillate. Increase N to 200--500 for short-dated contracts, or use the Black-Scholes formula as a cross-check.

## Early exercise boundary disappears for part of the put's life

The model found no nodes where early exercise was optimal for those time steps, typically because the put is out-of-the-money at those periods. This is expected behavior.

## The embedded User's Guide viewer is blank

Some browsers block inline PDFs by default. If you see a blank iframe but the **Download User's Guide (PDF)** button still works, either use the download path or enable PDF rendering in your browser's settings.

# Limitations and Assumptions

| Assumption | Implication |
|------------|-------------|
| No dividends | The model assumes the underlying pays no cash dividends. For dividend-paying stocks, the CRR price will overstate call values and understate put values. |
| Constant volatility | IV is held constant across all tree nodes. Real markets exhibit a volatility skew and term structure. |
| Constant risk-free rate | The risk-free rate is fixed for the option's life. |
| American exercise only | The model computes American-style (early exercise possible) prices. For European options, the early exercise comparison should be removed; however, for non-dividend-paying stocks the difference is negligible for calls. |
| Binary Kelly payoff | The Kelly formula used assumes a simple win/loss bet. Options have asymmetric, continuous payoff distributions, so the Kelly fraction is an approximation. |
| 1,000 trade simulation | Monte Carlo paths are illustrative. Actual trading involves transaction costs, slippage, margin requirements, and position limits not modeled here. |

\vspace{1em}

*This guide covers the CRR Binomial Pricing Calculator as implemented in `crr_binomial_pricing_calculator.py`. For issues or feature requests, refer to the project repository.*
