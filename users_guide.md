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

## Quick-Start Workflow

1. Enter your ticker symbol in the sidebar (e.g., `AAPL`).
2. Select Option Type (`put` or `call`) and Action (`buy` or `sell`).
3. Fill in the contract parameters: underlying price, strike, market price, and implied volatility.
4. Set Days to Expiration, risk-free rate, and number of CRR steps.
5. Configure Kelly Parameters (capital and minimum edge threshold).
6. Click **Calculate**.
7. Navigate the six tabs to explore pricing, Greeks, edge, sizing, simulation, and the animated tree.

# Sidebar Parameters

All inputs are on the left sidebar. The app re-runs calculations only when you press **Calculate** --- sidebar changes alone do not trigger recalculation.

## Contract Parameters

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

### Display Steps (N)

The number of tree steps used only for the animated visualization (Tab 6). The actual pricing always uses the full N from the CRR Steps field above. Smaller display N (4--8) produces readable node labels; larger values (10--12) show tree structure at the cost of label legibility.

### Speed (sec/step)

Pause duration between animation frames. Lower values (0.05--0.10) produce fast animations; higher values (0.5--1.0) are better for demonstrations or teaching.

# Tab 1 --- Pricing

This tab presents the primary output of the CRR model and two diagnostic charts.

## Metric Row

Three headline metrics appear at the top:

| Metric | Description |
|--------|-------------|
| CRR Model Price | The theoretical fair value computed by the binomial model |
| Market Price | The V_market you entered in the sidebar |
| % Error | $(V_{\text{model}} - V_{\text{market}}) / V_{\text{market}} \times 100$ |

A **positive** % Error means the model believes the contract is underpriced by the market. A **negative** % Error means the model believes it is overpriced.

## Model vs Market Bar Chart

A side-by-side bar chart comparing the CRR model price (blue) and the market price (gold). Dollar values are printed above each bar.

**How to interpret:** The visual gap between the two bars is proportional to the edge. A large gap warrants careful review of your IV input --- if the gap is consistently large, your implied volatility may not accurately reflect what the market is pricing.

## CRR Convergence vs Step Count Chart

A line chart showing how the model price changes as N increases through the values `[5, 10, 25, 50, 100, 150, 200]`. The market price is drawn as a horizontal dashed line.

**How to interpret:**

- **Oscillating convergence** is normal for binomial models. The price alternates slightly between even and odd step counts before stabilizing.
- **Convergence to a value near V_market** suggests the IV you entered is consistent with market consensus.
- **Convergence to a value far from V_market** is the source of the edge signal --- the model and market disagree on fair value at all step counts, which is more meaningful than a single-step result.
- Look for stabilization by N = 50--100. If the price is still moving significantly at N = 150, consider that the option may be deep in- or out-of-the-money, or that DTE is very short.

## Early Exercise Boundary (Puts Only)

For American put options, a third chart appears below the two main charts. It plots the critical stock price $S^*$ at each time step --- the threshold below which immediate exercise is optimal.

**How to interpret:**

- The boundary is plotted in amber dots, with a dashed blue line at your current spot price $S$.
- **If $S$ is above all amber dots:** The put is not worth exercising early at any node --- time value exceeds intrinsic value everywhere.
- **If $S$ approaches or crosses the boundary:** Early exercise may be rational. The exact crossover indicates the range of stock prices at which you should consider exercising rather than holding.
- The boundary typically slopes downward toward expiration: as DTE shrinks, early exercise becomes optimal at higher stock prices.
- American calls on non-dividend-paying stocks are **never** optimally exercised early, which is why this chart only appears for puts.

# Tab 2 --- Greeks

Option Greeks measure the sensitivity of the option price to changes in underlying variables. The app computes all five first-order Greeks using **finite-difference bumping** --- running the CRR model at slightly perturbed inputs and computing the numerical derivative.

## Greek Definitions and Interpretations

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

## Interpreting the Greeks Table

The bottom table restates each Greek with a plain-English interpretation column. Use this when presenting results to a non-technical audience or double-checking the sign and magnitude of each sensitivity.

# Tab 3 --- Edge & Signal

This tab synthesizes the pricing output into a trading recommendation.

## Metric Row

| Metric | Meaning |
|--------|---------|
| Edge | $(V_{\text{model}} - V_{\text{market}}) / V_{\text{market}} \times 100\%$ --- positive means model thinks the option is cheap |
| IV | The implied volatility you entered |
| RV30 | 30-day annualized realized volatility fetched from Yahoo Finance |

## Trading Signal Banner

The large colored banner shows one of three signals:

| Signal | Color | Meaning |
|--------|-------|---------|
| **BUY** | Green | Edge > threshold AND action = buy (model price > market price) |
| **SELL** | Navy | Edge < $-$threshold AND action = sell (model price < market price) |
| **NO TRADE** | Gray | Edge within the no-trade zone, or direction mismatch |

Below the banner, a brief explanation states the specific reason for the signal (e.g., *"Model price > market price --- contract appears underpriced"*).

**Important caveat:** The signal assumes your IV input is accurate and that the CRR model is the correct pricing engine. If your IV differs significantly from the market's implied volatility, the edge may be an artifact of the input rather than a genuine mispricing.

## Regime Banner

When RV30 data is successfully fetched, a second colored banner appears showing the current volatility regime, defined by the ratio IV/RV30:

| Ratio | Regime | Color | Meaning |
|-------|--------|-------|---------|
| > 1.20 | **HERDING** | Burnt orange | Market is paying significantly more than historical vol justifies. Sellers have an edge; buyers may be overpaying for protection. |
| 0.80 -- 1.20 | **NORMAL** | Green | IV is in line with recent realized vol. The market is pricing uncertainty without systematic overbidding or underbidding. |
| < 0.80 | **COMPRESSION** | Sky blue | Market is pricing in less vol than history suggests. Options appear cheap relative to recent moves; buyers may have an edge. |

**How to use regime with the signal:** A BUY signal in a COMPRESSION regime is more compelling --- you are buying cheap protection in a market that is underpricing risk. A SELL signal in a HERDING regime is similarly reinforced --- you are collecting inflated premiums.

## Edge Gauge Bar Chart

A horizontal bar chart displays the edge value on a numeric axis. Two vertical dashed lines mark the no-trade zone boundaries at $\pm\text{min\_edge}$, with the zone shaded in purple.

**How to interpret:**

- **Bar inside the purple zone:** Edge is too small to act on --- could be noise, transaction costs, or bid-ask spread.
- **Bar extends right (positive):** Model believes the option is underpriced; the longer the bar, the stronger the buy signal.
- **Bar extends left (negative):** Model believes the option is overpriced; the longer the bar, the stronger the sell signal.
- Compare the bar length to the no-trade zone width. A bar that barely clears the threshold is a marginal signal; one that is three times the threshold is substantially more conviction.

# Tab 4 --- Kelly Sizing

The Kelly Criterion is a mathematically optimal formula for allocating capital to a bet with a known edge and win probability.

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

The table shows, for each variant:

- **Fraction (f\*):** The decimal fraction of total capital to allocate.
- **% of Capital:** Same value expressed as a percentage.
- **Dollar Amount:** Fraction $\times$ Capital. This is the maximum recommended position size in dollars, not the number of contracts.
- **Trade Signal:** Repeats the BUY / SELL / NO TRADE from Tab 3.

When all fractions are `0.0000` (NO TRADE), the info box reminds you that edge is below the threshold and no position is recommended.

## Kelly Bar Chart

Three bars (green, navy, gold) show the Full, Half, and Quarter Kelly fractions as percentages of capital. Use this chart to quickly visualize the sizing difference between variants.

**How to interpret:**

- A Full Kelly bar at 8% with \$100,000 capital means the model recommends risking up to \$8,000 on this trade.
- Use **Half Kelly** (4%) as your practical starting point.
- If the Kelly fraction exceeds 20--25% of capital on a single option trade, double-check your edge estimate --- very high fractions often indicate an unusually extreme edge or an input error.

# Tab 5 --- Monte Carlo Simulation

The Monte Carlo tab projects the long-run P\&L trajectory of repeatedly applying the Kelly-sized strategy across 1,000 simulated trades.

## How the Simulation Works

For each of the 1,000 trades, the simulator:

1. Draws a random outcome (win or loss) using the Bernoulli distribution with $p_{\text{win}}$.
2. Applies the Kelly fraction to the current capital (the bet compounds --- a win increases capital; a loss reduces it).
3. Records the cumulative P\&L after each trade.

Only variants with Kelly fraction > 0 are simulated. If NO TRADE is signaled, the tab displays an info message instead of charts.

## Cumulative P&L Chart

Three colored curves show the cumulative P\&L path for Full Kelly (green), Half Kelly (navy), and Quarter Kelly (gold). The legend includes the **Annualized Sharpe Ratio** for each variant.

**How to interpret:**

- **Steeper upward slope** = higher expected growth rate (Full Kelly grows fastest in expectation).
- **Larger swings / deeper dips** = higher variance. Full Kelly can produce dramatic drawdowns even when the edge is positive.
- **Smoother curve** = lower variance. Quarter Kelly is the smoothest but grows most slowly.
- The Sharpe ratio (shown in the legend) normalizes return by volatility. A Sharpe > 1.0 is generally considered good; > 2.0 is strong. Compare Sharpes across variants to judge the risk-adjusted return tradeoff.

## Summary Statistics Table

Below the chart, a table reports four statistics for each variant:

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

## What the Binomial Tree Shows

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

Click **Animate Tree** to start the two-phase animation:

**Phase 1 --- Forward Pass (left to right):** Stock price nodes are revealed column by column, simulating how the stock can evolve from today to expiration. Each node shows the dollar stock price at that step and state. This demonstrates the forward propagation of the underlying process.

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
