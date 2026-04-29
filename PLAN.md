# PLAN.md

## Project Overview
**Title:** Profit-Maximizing Model for Prediction Markets
**Author:** DeWayne Dantzler
**Date:** April 27, 2026

### Description
Prediction markets (like Kalshi) aggregate crowd beliefs into prices, but crowds are systematically biased — they herd, overreact, 
and exhibit the favorite-longshot bias (overpricing unlikely outcomes). The central question is: when the majority is wrong in a 
predictable way, can a well-designed model detect that mispricing and profitably trade against it without going broke?

The project treats prediction market mispricing as a signal extraction problem: estimate P(true outcome) independently of crowd price, 
measure the gap, size the bet via Kelly, and manage drawdown. It is fundamentally an empirical test of whether behavioral biases in crowd 
markets are large enough and persistent enough to be profitably exploited by a calibrated probabilistic model.

Build a pipeline that implements the Cox-Ross-Rubinstein (CRR) Binomial Option Pricing Model for American-style equity options and applies 
the resulting theoretical prices as a probability estimator inside a Kelly Criterion trade-sizing framework

### Objectives: Project Targets 

- When does the majority become systematically wrong? Not all crowd errors are exploitable — the model must identify regimes
where bias is structural and persistent, not random noise.

- How do you size bets optimally? Using the Kelly Criterion (f* = (p·b − q) / b), the project asks how to maximize long-run wealth
growth while avoiding ruin — including fractional Kelly variants that reduce variance.

- Can ML estimate true probabilities better than the biased market price? The model must produce a calibrated p-estimate
that is more accurate than what the crowd implies, which is the edge that justifies trading.

- How do you handle market friction? Fees, bid-ask spreads, and slippage erode theoretical edges — the project quantifies
whether edges survive these real-world costs.

- How does the strategy perform under regime shifts? The model distinguishes normal market conditions (small-edge trades)
from herding regimes (high-conviction-only trades), and backtests across both.

## Scope (restrictions)

- American options only. All four AMD contracts are treated as American-style contracts. Early exercise capability is
required in every model variant. European-style pricing is excluded.

- No dividends. AMD's dividend treatment is excluded from all model runs. The standard CRR risk-neutral probability
formula is used without a continuous yield adjustment:

## Tasks
<!-- Try to be highly specific as this helps Claude -->

### Phase 1: Data Collection & Cleaning
- [] Download and load the dataset kaggle.com/datasets/kylegraupe/aapl-options-data-2016-2020
- [] Download and load the dataset kaggle.com/datasets/bendgame/options-market-trades
- [] Download and load the AMD option contracts from https://finance.yahoo.com/ 

### Phase 2: Modeling
- [] Pricing: Implement the CRR American binomial tree in Python and validate it against observed AMD premiums and Greeks within ±5%.
- [] Mispricing detection: Compute the signed edge (V_model − V_market) / V_market for all four trade tickets and determine the direction of crowd bias.
- [] Trade sizing: Apply the Kelly Criterion (full, half, and quarter-Kelly) to translate each edge into a concrete dollar position recommendation.
- [] Early exercise: Map the critical stock price S* below which early exercise of the AMD American puts is optimal, at every time step.
- [] Sensitivity: Quantify how stable the edge and Kelly fraction are under perturbations to σ, r, and T.

### Phase 3: Data Collection
- [] Store all inputs in a structured pandas DataFrame; document the exact timestamp of data collection for reproducibility.
- [] Extract the six Greeks: Implied Volativity(IV), Gamma, Delta, Theta, Vega, and Rho and store in a panda DataFrame 

### Phase 4: Plots
- Convergence plots
- Kelly charts
- Plot the binomial model theoretical prices versus the actual observed limit prices for four types of AMD trade tickets: Buy/Sell AMD Calls and Buy/Sell AMD Puts
-  

### Phase 5: Project Workflow
<!-- The project follows a linear pipeline of six stages, each building directly on the previous: -->
- [] Data ingestion — Extract AMD chain inputs; source r and realized volatility.
- [] Tree construction — Build CRR lattice (NumPy vectorized) for each ticket.
- [] Pricing & Greeks — Backward induction with American exercise; numerical Greeks.
- [] Edge computation — Compare V_model vs. V_market; compute mispricing signal.
- [] Kelly sizing — Convert edge to f*, f_half, f_quarter; dollar position recommendation.

### Phase 6: Deliverables
- [] Research report (10–20 pages) covering theory, implementation, results, pricing validation, mispricing analysis, and Kelly sizing.
- [] Reproducible Python code repository with documented modules: data.py, tree.py, greeks.py, edge.py, kelly.py, simulation.py.
- [] Final presentation slides covering the end-to-end pipeline, key results, and failure cases.
  
<!-- Document the techniques you plan to use -->
## Methods
- Mispricing Edge Computation: edge = (V_model − V_market) / V_market
- Full, half, and quarter-Kelly fractions need to be computed

### Technology Stack
- Pandas for data manipulation
- scikit-learn preprocessing
- Python 3.11 Primary language
- numpy Vectorized binomial lattice construction; numerical finite differences
- matplotlib / plotly 	Convergence plots, lattice visualization, Greek surfaces, Kelly charts, tornado charts
- yfinance 	AMD historical price data and realized volatility download
- scipy 	Statistical functions; Monte Carlo helper distributions
- jupyter 	Notebook-based reproducible analysis for reporting
- GitHub 	Repository hosting and version control

<!-- Ok to use Claude to help build the PLAN.md -->
<!-- Learn how to use claude's MCP's to connect claude to github repo -->

