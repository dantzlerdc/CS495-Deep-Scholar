---
title: ""
fontsize: 14pt
documentclass: extarticle
geometry:
  - landscape
  - letterpaper
  - margin=0.7in
colorlinks: true
linkcolor: NavyBlue
header-includes:
  - \usepackage{fancyhdr}
  - \pagestyle{fancy}
  - \fancyhf{}
  - \fancyfoot[C]{\small Index Card \thepage{} of \pageref{LastPage}}
  - \renewcommand{\headrulewidth}{0pt}
  - \usepackage{lastpage}
  - \usepackage{titlesec}
  - \usepackage{etoolbox}
  - \definecolor{BCBlue}{HTML}{003D79}
  - |
    ```{=latex}
    \titleformat{\section}{\LARGE\bfseries\color{BCBlue}}{}{0pt}{}[{\color{BCBlue}\titlerule[2pt]}]
    \titlespacing*{\section}{0pt}{-30pt}{18pt}
    \pretocmd{\section}{\newpage}{}{}
    \setlength{\parskip}{0.5em}
    ```
---

# Slide 1 --- Title: Mathematical and Empirical Models in Agreement

- **Open warmly.** Welcome the committee. Introduce yourself: DeWayne Dantzler, CS\,495 Capstone Project 6.

- **Set the headline early.** "This project cross-validates two completely independent option-pricing models --- one mathematical, one machine-learning --- and shows they agree on crowd mispricing precisely when behavioral-finance theory predicts."

- **Frame the data.** "I'll show you the result on real AAPL options from 2016--2020 (101{,}535 contracts) and a live AMD option chain from April 2026."

- **Set audience expectations.** "I'll walk through one specific AAPL contract end-to-end so the math is concrete, then expand to the full backtest result and a live demo."

- **Anticipated question:** *"What's new here?"* --- Answer: "Nobody has cross-validated CRR against an IV-free ML classifier with regime-conditioned Kelly sizing before. The novelty is the cross-validation, not any single component."

# Slide 2 --- What Is the Problem?

- **Lead with the gap.** "Retail traders lack a principled framework to decide three things: whether a price is fair, how much to bet, and *when not to trade*."

- **State the three research questions** (memorize these):
    - Do CRR model prices predict whether an option expires ITM or OTM?
    - Does cross-validation between CRR and an ML classifier detect exploitable pricing edge?
    - Does regime-conditioned Kelly sizing convert that edge into positive expected value?

- **Define the edge formula on the board if asked**: $\text{edge} = (V_{\text{model}} - V_{\text{market}}) / V_{\text{market}}$. "Positive edge means the market is underpricing; negative means overpricing."

- **The pricing gap.** "The market price reflects sentiment, supply-demand, and the bid-ask spread. The model price is pure risk-neutral expectation. The gap between them is the potentially-exploitable edge."

- **Anticipated question:** *"Why not just trust the market?"* --- Answer: "Because the market is right *on average* but not in *every regime*. We'll show in a few slides that the cross-validation signal concentrates in herding episodes where the crowd is most biased."

# Slide 3 --- Why It Matters \& What Others Have Done

- **Scale the stakes.** "Options trade six hundred billion dollars notional *daily* in the US. Even a 2% mispricing detection has substantial profit-and-loss impact."

- **Cite Fama up front.** "Fama's Efficient Market Hypothesis from 1970 says public information is priced in on average. But the EMH itself acknowledges this is an *aggregate* claim --- not every regime, not every moment."

- **The Samuelson lens.** "Samuelson noticed that markets can be micro-efficient on individual contracts but exhibit aggregate bias under coordinated behavioral demand --- herding creates regime-local inefficiencies."

- **Prior work in one sentence each:**
    - Cox--Ross--Rubinstein 1979: binomial lattice (no ML)
    - Black--Scholes 1973: closed-form, but no American early exercise
    - Bakshi 1997: stochastic vol but requires unobservable parameters
    - Carr \& Wu 2009: IV systematically overstates RV (variance risk premium)
    - Kelly 1956: log-utility bet sizing, brought to markets by Thorp (1969)

- **State the gap explicitly.** "No prior work cross-validates CRR with an IV-free ML classifier and regime-conditioned Kelly sizing. That's the contribution."

# Slide 4 --- Contribution \& Methodology

- **State the novel contribution in one sentence.** "First framework to cross-validate CRR against a *fully independent* IV-free ML classifier --- the two signals share no inputs and no training data."

- **The three-layer pipeline** (walk top to bottom on the slide):
    - **Layer 1** --- CRR Binomial Pricer (deterministic no-arbitrage)
    - **Layer 2** --- XGBoost ITM/OTM Classifier (empirical ML, IV-free features)
    - **Layer 3** --- Kelly Criterion Position Sizer (regime-conditioned)

- **Key methodological commitments:**
    - Regime-conditioned Kelly from IV/RV$_{30}$ ratio
    - Walk-forward 60/20/20 split --- zero look-ahead bias
    - Open-source Streamlit calculator with live chain (we'll demo it)

- **Data.** "AAPL 2016--2020 Kaggle dataset for the walk-forward backtest (101{,}535 contracts), and an AMD April 2026 live chain pulled from Fidelity for the live validation."

- **Anticipated question:** *"Why XGBoost and not deep learning?"* --- Answer: "XGBoost handles nonlinear interactions like moneyness $\times$ DTE without the data hunger or calibration fragility of neural nets, and feature importances are interpretable."

# Slide 5 --- Worked Example: Contract A --- HERDING Setup

- **Lead with the choice to use one contract.** "Before the aggregate results, let me ground everything in *one real contract* so the math is concrete."

- **Read off the parameters slowly** (these are on screen):
    - Real AAPL put, quote date 2020-03-16
    - $S = \$241.47$, $K = \$240$, DTE = 18 days
    - $V_{\text{market}} = \$21.225$
    - $r = 2.00\%$
    - $N = 50$ pricing steps

- **The headline reading** (the punchline of this slide):
    - "IV is about 1.00. RV30 is about 0.82. The market is paying for 22\% more volatility than recent history justifies."
    - "That's a textbook herding regime signature."

- **Why $\sigma = \text{RV30}$, not IV.** "Critical methodological choice: I use realized historical volatility, not implied volatility. That makes the L1 signal mathematically independent of any market sentiment baked into IV."

- **Bridge to next slide.** "Let's now walk through how the CRR lattice prices this contract."

# Slide 6 --- Forward Pass --- Building the Stock Price Lattice

- **Lead with what the forward pass IS.** "The forward pass lays out every possible stock price path from today to expiration."

- **Three core CRR parameters** (write these on whiteboard if asked):
    - $u = e^{\sigma\sqrt{\Delta t}}$ --- up-factor
    - $d = 1/u$ --- down-factor (perfectly inverse)
    - $p^{*} = (e^{r\Delta t} - d)/(u - d)$ --- risk-neutral up-probability

- **Display vs pricing N.** "I'm showing a 5-step lattice for clarity, but the actual pricing uses 50 steps."

- **The no-arbitrage anchor.** "The risk-neutral probability $p^*$ is constructed so that the discounted expected next-step stock price equals today's price. That's what 'no risk-free profit' formally means."

- **What's NOT here yet.** "Important: no option value has been computed at this stage. The forward pass is purely stock-price evolution."

- **Bridge.** "Option pricing happens in the backward pass --- that's the next slide."

# Slide 7 --- Backward Induction --- Where the Option Price Emerges

- **State the algorithm in spoken English.** "Start at expiration with the terminal payoffs. At every interior node, compute two numbers: intrinsic value (the payoff if you exercise right now) and continuation value (the discounted expected future value). Take the max of those two and walk one step toward today."

- **The American optionality test.** "The max-of-intrinsic-vs-continuation is what makes this an *American* pricer. European options can only check at expiration; American options check at *every* node."

- **The result on Contract A:**
    - "$V$ at the root, $N=50$, is **\$16.663**."
    - "Market price was \$21.225."
    - "**Layer 1 edge = $-21.5\%$**. Contract is overpriced."

- **The intuition for the audience.** "When the gold star --- the actual market premium --- sits *above* the model price at the root, the crowd is paying more than no-arbitrage theory permits. That gap is the Layer 1 edge, before any ML model is consulted."

- **Bridge.** "Now: does an independent ML model agree?"

# Slide 8 --- Contract A Result --- Two Independent Models Agree

- **State the punchline first.** "Two completely independent models reach the *same* mispricing conclusion on this contract."

- **Layer 1 reading:**
    - $V_{\text{market}} = \$21.225$ vs. $V_{\text{model}} = \$16.663$
    - **edge $= -21.5\%$** --- the no-arbitrage pricer says overpriced.

- **Layer 2 reading:**
    - $p_{\text{indep}} = 0.0562$ vs. $q_{\text{market}} = 0.0884$
    - **edge $= -3.22\%$** --- the IV-free ML classifier *also* says overpriced.

- **Why this matters --- emphasize.** "No shared training data, no shared methodology, no shared inputs. The fact that they agree comes from *shared underlying reality* --- not from any calibration artifact."

- **Connect to theory.** "This agreement, in this regime, is the empirical fingerprint of Samuelson macro-inefficiency. Crowd consensus is diverging from underlying reality, and two independent methods detect it."

- **Forward reference.** "I'll show in slide 12 that this isn't just one contract --- the herding-regime cross-correlation across thousands of contracts is $r = 0.413$ with $p = 2.4 \times 10^{-10}$."

# Slide 9 --- CRR Pricing Results: Model vs Market Validation

- **The point of this slide.** "Before any edge claim, the CRR pricer itself must be calibrated. This slide validates Hypothesis H1."

- **What the chart shows.** "Dollar difference between CRR model fair value and the observed market price for all four AMD contracts: T1 buy call, T2 sell call, T3 buy put, T4 sell put."

- **The numbers to read aloud:**
    - "All four residuals are less than \$0.002 in absolute value."
    - "$|\text{edge}| < 0.01\%$ --- three orders of magnitude inside the $\pm 5\%$ acceptance band."
    - "The light-blue stripe is the acceptance band; our bars are essentially zero."

- **What it proves.** "The CRR American binomial pricer is correctly implemented and well-calibrated for at-the-money strikes."

- **H1 verdict.** "**Hypothesis H1 passed with substantial margin.** Section 4.2.1 of the report."

# Slide 10 --- CRR Pricing Results: Numerical Convergence

- **What's on screen.** "Main panel: CRR price as a function of lattice steps $N$. Inset: log-scale absolute residual against the $N=200$ baseline."

- **The convergence story:**
    - "Both call ($\approx \$19$) and put ($\approx \$27$) plateau by $N \approx 25$ steps."
    - "Log-residual crosses the \$0.01 threshold by $N \approx 100$ --- sub-penny precision."

- **The "only two lines" question.** "You may notice only two curves --- not four. That's because buy/sell variants of the same contract price identically: Action affects trade direction, not model price."

- **Why this matters.** "This validates the choice of $N = 100$ throughout the rest of the pipeline."

- **Anticipated question:** *"Why oscillating?"* --- Answer: "Binomial tree prices alternate between even and odd step counts before stabilizing --- that's a well-known property of discrete lattices, not a bug."

# Slide 11 --- CRR Pricing Results: Early Exercise Boundary

- **What the chart shows.** "The critical stock price $S^*(t)$ at each day. If the spot falls below $S^*$, immediate exercise of the American put dominates holding to expiration."

- **Two cases overlaid:**
    - **AMD live put** (green): $S = \$341.35$, $K = \$350$, out-of-the-money. The boundary rises gradually but *never reaches spot* --- early exercise is never optimal here.
    - **Illustrative deep-ITM put** (red): $S = \$310$, $K = \$350$. The boundary crosses spot around 17 days in (the grey shaded zone) --- exercise becomes optimal.

- **Why include the second case.** "The deep-ITM example demonstrates that the lattice correctly handles American optionality --- a capability that closed-form Black--Scholes cannot reproduce."

- **Bottom-line takeaway.** "Validates the lattice's American option handling. Section 4.4 of the report."

# Slide 12 --- Cross-Model \& Backtest: L1 vs L2 Cross-Validation

- **The most important slide of the talk.** Slow down here.

- **Two panels.** "Left: edge scatter of CRR Layer 1 edge versus XGBoost Layer 2 edge across 3,000 sampled AAPL contracts, colored by regime. Right: the actual ITM expiration rate per agreement zone."

- **The aggregate-vs-conditional contrast** (memorize the numbers):
    - "**Aggregate Pearson $r = 0.032$** --- statistically zero across all contracts."
    - "**In the herding regime: $r = 0.413$ ($p = 2.4 \times 10^{-10}$, $n = 217$).**"

- **The right-panel headline number.** "In the both-SELL agreement zone --- Q3 of the scatter --- the **actual** ITM expiration rate jumps to **76.5%** versus a baseline of about 63%."

- **What this proves.** "Direct empirical evidence that the cross-validation has *predictive content*. Both models, agreeing, predict actual outcomes."

- **Bridge.** "Where does the agreement come from? The next slide: the regime detector."

# Slide 13 --- Cross-Model \& Backtest: Regime Detection

- **Three-panel time series:**
    - Top: ATM implied vol (navy) vs. 30-day realized vol (red)
    - Middle: the RV-IV spread with herding (+10\%) and normal ($\pm 5\%$) thresholds
    - Bottom: the detected regime ribbon (burnt orange = Herding, green = Normal)

- **The dataset:**
    - "AAPL 2016--2021, 1,223 trading days"
    - "Classifier flags 104 days as Herding (8.5\%); rest as Normal"

- **The COVID anomaly note.** "March 2020 is annotated above the clip lines --- RV peaked at 4.0 and the spread troughed at $-3.6$. We let COVID be annotated, not allowed to dominate the y-axes."

- **The Simpson's Paradox punchline.** "That 8.5\% Herding slice is *exactly* the subset where Layer 1 and Layer 2 reach $r = 0.413$. The aggregate signal is statistical noise; conditioned on the right regime it is highly significant. Simpson's Paradox in action."

- **Anticipated question:** *"Could you predict the regime ahead of time?"* --- Honest answer: "No. The IV/RV30 ratio is *backward-looking*. This is a limitation noted in the Next Steps slide. The point is detection of *current* regime, not prediction of future regime."

# Slide 14 --- Cross-Model \& Backtest: Walk-Forward Backtest

- **The setup.** "Out-of-sample chronological test of the full Layer 1 + Layer 2 + Layer 3 pipeline. Test window: 2017--2021. Total trade decisions: 57,231. Decisions that actually triggered a trade: 3,760."

- **The headline numbers** (memorize):
    - "**Cumulative P\&L: \$2.94 million on a \$100k base.**"
    - "**Max drawdown: under 15\%. Circuit breaker never fired.**"
    - "Per-trade hit rate: **63.1\%** (2,371 wins vs. 1,389 losses)"
    - "Mean trade: \$781; median trade: \$1,220"

- **The Brier score validation.** "Layer 2 classifier Brier score: 0.211 --- below the 0.25 naive baseline of always predicting 50\%."

- **The sizing strategy.** "Regime-conditioned Kelly: half-Kelly in Normal, quarter-Kelly in Herding. The Herding throttle is intentional --- when conviction is highest, downside has to be capped."

- **The "no-trade" observation.** "Of 57k decisions, 53k were no-trade. The pipeline says NO most of the time. **Saying no is the most valuable thing the pipeline does.**"

- **H3 verdict.** "**Hypothesis H3 confirmed.** Section 4.8 of the report."

# Slide 15 --- Next Steps

- **Acknowledge the limitations honestly first** (right panel of the slide):
    - **Data scope:** AAPL only, single market cycle. Other tickers untested.
    - **Volatility surface:** Flat IV per contract; no smile or skew.
    - **Transaction costs:** Mid-price fills; no bid-ask friction or slippage.
    - **Regime detection lag:** IV/RV30 ratio is backward-looking.
    - **Kelly assumptions:** Log-utility; no leverage or portfolio-level limits.

- **Four research extensions** (left panel, can read or paraphrase):
    1. Expand option contracts to use other stock datasets to validate the model against.
    2. Run the cross-sectional test across multiple expiration cycles and multiple high-liquidity stocks (e.g., NVDA, MSFT) to prove the pipeline's stability.
    3. Modernize the Layer 2 ML model architecture by replacing XGBoost with **TabPFN v2** --- a transformer-based foundation model for tabular data that delivers state-of-the-art calibrated probability estimates without per-task gradient-boosting training.
    4. Publish open-source framework and Streamlit calculator for community validation and peer review.

- **Bridge to demo.** "Before conclusions, let me show you the framework actually running."

# Slide 16 --- Live Demo: Interactive CRR Binomial Pricing Calculator

- **Switch to the live app.** "I'm going to switch to the actual application now."

- **Demo plan for the next 3 minutes:**
    1. **Reproduce Contract A** --- enter S, K, IV, DTE from slide 5
    2. **Confirm Layer 1 edge $\approx -21.5\%$ (SELL)**
    3. **Show Kelly sizing on \$100k capital** --- bring up the Kelly tab
    4. **Animate the binomial tree live** --- show forward + backward induction
    5. **Live RV30 lookup** --- type any ticker, fetch live realized vol

- **Risk management note.** "The app shows full Greeks, regime detection, the no-trade signal, and a 1{,}000-trade Monte Carlo P\&L all in real time. It's a teaching tool, not a trading recommendation."

- **Backup plan if demo fails.** "If the live demo has any issues, all results are reproducible from the bundled `Users-Guide-CRR-Binomial-Pricing-Calculator.pdf` and the GitHub repo. The PDF is embedded inside the app on the User's Guide tab."

# Slide 17 --- Conclusion

- **Restate the central contribution** (slow and clear):
    - "CRR and XGBoost, using independent inputs, both agree on mispricing direction in the herding regime --- mutually cross-validating Samuelson macro-inefficiency."

- **Three hypotheses confirmed** (one breath each):
    - **H1 --- CRR Benchmark Confirmed.** Model within 1--2\% of market on 80\% of AMD live contracts; sub-rounding precision.
    - **H2 --- XGBoost Independent Estimator Confirmed.** Brier 0.211 versus 0.25 naive baseline. Top features are moneyness and DTE --- no IV leakage.
    - **H3 --- Fractional Kelly Dominates Confirmed.** \$2.9M P\&L over 101k AAPL contracts; max drawdown $<15\%$; circuit breaker never triggered.

- **The most important sentence in the deck.** "The pipeline's most valuable output is the **no-trade signal** --- when CRR and XGBoost disagree, no position is taken. **The model works precisely because it says no when there is no edge.**"

- **Close with thanks.** "Thank you. I welcome your questions."

- **Anticipated final questions to prepare for:**
    - "What would falsify your result?" --- A future market regime where L1 and L2 disagree but the actual outcomes match L2 only.
    - "Could you trade this with real money?" --- Not without the transaction-cost extensions noted in Next Steps.
    - "Why publish open-source?" --- Reproducibility and peer scrutiny are part of the validation.
