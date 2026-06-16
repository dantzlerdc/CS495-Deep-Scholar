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

- **The elevator pitch** (memorize verbatim --- ready for any "what's your capstone?" moment): "I developed a *three-layer framework for options trading* that combines **Cox--Ross--Rubinstein pricing**, **XGBoost machine learning**, and **Kelly-based position sizing** to identify and manage option mispricing, particularly during market herding regimes."

- **Problem / Solution in one breath** (for the audience). "*Problem:* finding genuinely profitable option opportunities is hard. *Solution:* use *multiple independent models* to validate mispricing before any capital is risked."

- **Decoding the title keywords:**
    - **Mispricing** $\to$ Market Price $\ne$ Fair Value $\to$ candidate opportunity.
    - **Mathematical and Empirical in Agreement** $\to$ CRR (theory) *and* XGBoost (ML) both agree.
    - **Herding** $\to$ regime-local inefficiencies (focus of Slides 12--13).
    - **Kelly Sizing** $\to$ edge isn't enough; *how much should I risk?*

- **Frame the data + set expectations.** "Results on real AAPL options 2016--2020 ($101{,}535$ contracts) and a live AMD option chain from April 2026. I'll walk through one AAPL contract end-to-end so the math is concrete, then expand to the full backtest result and a live demo."

- **Anticipated faculty question:** *"What is the main contribution?"* --- Answer: "**Not** a new pricing model and **not** a new ML algorithm. The contribution is a **unified framework** combining theory-based pricing, *independent* ML validation, regime detection, and Kelly-based risk management into a single decision process."

# Slide 2 --- What Is the Problem?

- **Lead with the gap.** "Retail traders lack a principled framework to decide three things: **whether a price is fair, how much to bet, and *when not to trade*.** Most existing tools answer only one of those."

- **The retail-trader workflow contrast** (powerful framing). "Naive workflow: *Option looks interesting $\to$ buy it* --- no fair-value check, no validation, no risk sizing. This framework replaces that with: **Fair-Value Check $\to$ Independent Validation $\to$ Position Sizing $\to$ Trade or No-Trade.**"

- **State the three research questions** (memorize, with a plain-English translation ready):
    - Q1: *Do CRR model prices predict whether an option expires ITM or OTM?* (Can theoretical pricing say something useful about future outcomes?)
    - Q2: *Does cross-validation between CRR and an ML classifier detect exploitable pricing edge?* (When two independent models agree, does that signal carry real predictive value?)
    - Q3: *Does regime-conditioned Kelly sizing convert that edge into positive expected value?* (Even with an edge, can we manage risk well enough for profitable long-run results?)

- **The pricing gap.** "Market price reflects supply/demand, sentiment, bid-ask. Model price is pure risk-neutral expectation. Signed difference is the candidate edge: $\text{edge} = (V_{\text{model}} - V_{\text{market}}) / V_{\text{market}}$. **But the gap alone is not enough --- a real edge requires both layers to agree; otherwise, *no trade*.**"

- **What's missing today $\to$ what each layer solves.** "*Quantified edge* $\to$ CRR pricing. *Validation* $\to$ XGBoost. *Position sizing* $\to$ Kelly Criterion. *Regime filter* $\to$ IV/RV30 detector. Each missing piece maps to a specific component of the architecture on the next slide."

- **Anticipated faculty question:** *"Why isn't a pricing gap alone enough?"* --- Answer: "Pricing models can be wrong, and markets can stay mispriced longer than expected. A pricing gap *identifies a candidate*; independent ML confirmation reduces false positives; Kelly sizing decides whether the opportunity is worth risking capital on."

# Slide 3 --- Why It Matters \& What Others Have Done

- **The retail trader's three open questions** (audience hook). "**Is the option fairly priced? How much should I risk? When should I avoid trading?** Most existing tools answer only *one* of those. This framework answers all three."

- **The Pricing Gap formalism.** "Market price reflects supply/demand, sentiment, bid-ask, and noise. CRR model price is the risk-neutral fair-value benchmark. Their signed difference $(V_{\text{market}} - V_{\text{model}}) / V_{\text{market}}$ is the candidate edge: positive $\to$ market underpricing, negative $\to$ overpricing."

- **Scale the stakes.** "Options trade **\$600B+ notional daily** in the US. Even a 2\% mispricing detection has material P\&L impact."

- **Cite Fama, then qualify.** "Fama's EMH (1970): public information is priced in *on average* --- an *aggregate* claim, not every regime. **Samuelson** observed markets can be micro-efficient on individual contracts but exhibit aggregate bias under coordinated demand --- *herding creates regime-local inefficiencies*."

- **Prior work, one sentence each:**
    - Cox--Ross--Rubinstein 1979: binomial lattice (no ML).
    - Black--Scholes 1973: closed-form, but no American early exercise.
    - Bakshi 1997: stochastic vol but requires unobservable parameters.
    - Carr \& Wu 2009: IV systematically overstates RV (variance risk premium).
    - Kelly 1956: log-utility bet sizing, brought to markets by Thorp (1969).

- **State the gap explicitly.** "Existing work has *CRR pricing* **or** *ML prediction* **or** *Kelly sizing* **or** *regime detection* --- each in isolation. **No prior framework combines all four into a single cross-validated decision system.** That gap is the contribution."

- **Anticipated faculty question:** *"What is actually novel about your work?"* --- Answer: "Not CRR, not XGBoost, not Kelly *individually* --- those are established. The novelty is **combining them into a cross-validated framework**: a CRR pricing signal *independently confirmed* by ML, then sized via *regime-conditioned* Kelly."

# Slide 4 --- Contribution \& Methodology

- **The framing question.** "How does the system work from start to finish? This is the *roadmap slide* --- every subsequent slide is a detailed walkthrough of one piece of this diagram."

- **The novel contribution in one sentence.** "First framework to cross-validate CRR against a *fully independent* IV-free ML classifier --- the two signals share no inputs and no training data."

- **The three-layer pipeline** (walk top to bottom):
    - **Layer 1 --- CRR Binomial Pricer:** theory-based fair value. Inputs $S, K, T, \sigma, r \to V_{\text{model}}$; compare to $V_{\text{market}}$ to flag over- / under- / fair-priced.
    - **Layer 2 --- XGBoost ITM/OTM Classifier:** data-driven validation. *No no-arbitrage theory*; learns patterns from historical data.
    - **Layer 3 --- Kelly Position Sizer:** risk management. Small edge $\to$ small position; large edge $\to$ larger position. Regime-conditioned by IV/RV$_{30}$.

- **The central design choice** (the slide's most defensible idea). "Most trading systems do *Prediction $\to$ Trade*. This framework does **Prediction $\to$ Independent Confirmation $\to$ Risk Sizing $\to$ Trade**. **No single model is trusted alone --- multiple independent layers must agree before capital is committed.**"

- **Key methodological commitments:** walk-forward $60/20/20$ (zero look-ahead bias); $\sigma = \text{RV30}$ (not IV) for L1; no IV leakage into L2 features; open-source Streamlit calculator with live chain (demo later).

- **Data.** "AAPL 2016--2020 Kaggle dataset for the walk-forward backtest ($101{,}535$ contracts); AMD April 2026 live chain from Fidelity for live validation."

- **Anticipated faculty question:** *"Why not just use XGBoost by itself?"* --- Answer: "Because XGBoost identifies *statistical* patterns but provides no *economic* justification. CRR provides the no-arbitrage theory-based fair value; XGBoost is the *independent* validation. Combining both is what makes the framework defensible."

# Slide 5 --- Worked Example: Contract A --- HERDING Setup

- **The framing question.** "Before showing aggregate results, ground everything in *one real contract*: **what contract are we analyzing, and why was it chosen?** This is a real AAPL put pulled unmodified from the historical dataset --- **not synthetic, not cherry-picked**."

- **Read off the parameters slowly** (these are on screen):
    - Real AAPL put, quote date $2020$-$03$-$16$
    - $S = \$241.47$, $K = \$240$, DTE $= 18$ days
    - $V_{\text{market}} = \$21.225$, $r = 2.00\%$, $N = 50$ pricing steps

- **The March 2020 context** (why this regime is interesting and credible). "Quote date sits inside the COVID market shock --- volatility was extremely elevated and investors were aggressively buying downside protection, inflating put premiums. Exactly the environment where a herding-based framework expects to find mispricings."

- **The headline reading** (the punchline of the slide):
    - "IV $\approx 1.00$, RV30 $\approx 0.82$ $\to$ the market is paying for **$22\%$ more volatility than recent history justifies**."
    - "That's a textbook herding-regime signature: traders pricing in more fear than the data supports."

- **Herding regime in one sentence.** "Market environment where crowd behavior pushes prices away from fundamentals: *fear $\to$ higher IV $\to$ more expensive options $\to$ potential mispricing.*"

- **Anticipated faculty question** (the critical methodological one): *"Why use $\sigma = \text{RV30}$ instead of IV?"* --- Answer: "Because IV is *derived from the option price itself*. Using IV inside the pricing model would introduce **circularity** --- the model would converge to the market price by construction and produce a zero edge. RV30 is an independent estimate from historical returns, so the Layer 1 signal stays mathematically independent of the market sentiment."

# Slide 6 --- Forward Pass --- Building the Stock Price Lattice

- **The framing question.** "Before any option can be priced, the model first has to answer: **what stock prices are possible between today and expiration?** The forward pass builds that *map of every possible stock-price path*."

- **The setup.** "Start at $S_0 = \$341.35$. At each step the stock can only do one of two things --- *up* or *down* (hence *binomial*)."

- **Three core CRR parameters** (write on whiteboard if asked):
    - $u = e^{\sigma\sqrt{\Delta t}} \approx 1.0437$ --- up move: $S \to S \cdot u \approx \$356.3$.
    - $d = 1/u \approx 0.9581$ --- down move: $S \to S \cdot d \approx \$327.0$.
    - $p^{*} \approx 0.496$, $q^{*} \approx 0.504$ --- risk-neutral up/down probabilities.

- **Risk-neutral $\ne$ real-world.** "$p^{*}$ and $q^{*}$ are **not** the real-world probabilities of the stock going up or down. They are chosen so the discounted expected next-step stock price equals today's price: $\mathbb{E}[S_{t+1}] = S_t\,e^{r\Delta t}$. That is what *no arbitrage* formally requires. The values land near 50/50 because the time step is small and up/down moves are symmetric around the risk-free growth rate."

- **The recombining-tree advantage.** "*Every branch recombines*: $S_0 \cdot u \cdot d = S_0 \cdot d \cdot u$. The number of nodes grows **linearly** in $N$ rather than exponentially ($2^N$), which is exactly what makes CRR practical for American-option pricing."

- **Display vs pricing $N$.** "I'm showing a 5-step lattice for clarity; the actual pricing run uses 50 steps. **Important: no option value has been computed yet --- the forward pass is purely *stock-price* evolution.** Option pricing happens in the backward pass on the next slide."

- **Anticipated faculty question:** *"Why risk-neutral instead of real-world probabilities?"* --- Answer: "Because option pricing is **no-arbitrage valuation**, not forecasting. Risk-neutral probabilities price derivatives as if investors were indifferent to risk, producing prices consistent with the absence of arbitrage."

# Slide 7 --- Backward Induction --- Where the Option Price Emerges

- **The framing question.** "Slide 6 built the stock-price lattice --- *every possible future price*. This slide is where the model finally answers: **what is the option worth today?** Start at expiration with the known payoffs and walk backward to $t = 0$."

- **Terminal payoff example.** "At expiration the put value is known exactly: $V = \max(K - S, 0)$. *e.g.*\ $S = \$260 \to V = \$0$; $S = \$240 \to V = \$0$; $S = \$220 \to V = \$20$. Then at every interior node the model recursively asks: 'if I hold one more period, what is its expected value?'"

- **The two competing values at every node:**
    - **Intrinsic** $= \max(K - S, 0)$ --- what you'd get if you exercise *right now*.
    - **Continuation** $= e^{-r\Delta t}\,(p\, V_{\text{up}} + q\, V_{\text{down}})$ --- discounted expected value of waiting one more step.

- **The American-option decision rule.** "$V = \max(\text{intrinsic},\,\text{continuation})$ --- the larger one wins. **That max-check at every node is what makes this an *American* pricer**. European options only check at expiration; American options check at *every* node. Closed-form Black--Scholes cannot reproduce this."

- **The result on Contract A** ($N = 50$):
    - $V_{\text{model}} = \$16.663$ vs.\ $V_{\text{market}} = \$21.225$.
    - **Layer 1 edge $= -21.5\%$** $\to$ negative edge $\to$ overpriced $\to$ **SELL**.

- **The gold-star intuition.** "When the gold star --- the actual market premium --- sits *above* the model price at the root, the crowd is paying more than no-arbitrage theory permits. **This is the framework's first actionable trading signal**, generated before any ML model is consulted."

- **Anticipated faculty question:** *"Why use backward induction instead of computing the price directly?"* --- Answer: "Because an American option can be exercised *before* expiration. The optimal exercise decision at each node depends on the future continuation value, so the model must work backward from expiration --- something a single closed-form Black--Scholes computation cannot do."

# Slide 8 --- Contract A Result --- Two Independent Models Agree

- **The "first money slide" framing.** "Slides 5--7 walked through the *mechanics* of CRR. This slide finally answers: **what does the model conclude about this real contract?** Both CRR *and* XGBoost independently conclude the option is **overpriced $\to$ SELL**."

- **Layer 1 reading.**
    - $V_{\text{market}} = \$21.225$ vs.\ $V_{\text{model}} = \$16.663$
    - **Edge $= -21.5\%$** (negative $\to$ overpriced $\to$ **SELL**).

- **Layer 2 reading.**
    - $p_{\text{indep}} = 0.0562$ vs.\ $q_{\text{market}} = 0.0884$
    - **Edge $= -3.22\%$** --- the IV-free ML classifier *also* says **SELL**.

- **The "maybe vs much-stronger" framing.** "Only CRR says SELL $\to$ could be model error. Only XGBoost says SELL $\to$ could be ML noise. *Both* independently say SELL $\to$ a **much stronger signal** --- agreement points to *shared underlying reality*, not a shared modeling artifact."

- **Why the HERDING regime context matters.** "Contract A was deliberately chosen from a herding day: $\text{IV} \approx 1.00$ vs.\ $\text{RV30} \approx 0.82$ --- traders are paying for roughly $22\%$ more volatility than recent history justifies. That's the *opportunity* both models detect, and agreement here is the empirical fingerprint of **Samuelson macro-inefficiency**: crowd consensus diverging from underlying reality."

- **Anticipated faculty question:** *"Why should I trust agreement between two models?"* --- Answer: "Because they're independent. CRR is no-arbitrage theory; XGBoost is a data-driven classifier with no shared inputs. Agreement between independent models is far less likely to come from a shared modeling error and is therefore stronger evidence of *genuine* mispricing."

- **Forward reference.** "One contract. Slides 12--14 test whether this pattern holds across thousands; herding-regime cross-correlation jumps to $r = 0.413$ ($p = 2.4 \times 10^{-10}$)."

# Slide 9 --- CRR Pricing Results: Model vs Market Validation

- **The framing question.** "This slide answers: **can the CRR model accurately reproduce real market option prices?** Before any mispricing claim, the pricing engine itself has to be calibrated. This is the Layer 1 validation slide."

- **What the chart shows.** "Pricing residual $V_{\text{model}} - V_{\text{market}}$ for the four AMD contracts (T1 Buy Call, T2 Sell Call, T3 Buy Put, T4 Sell Put). A bar near zero means model price $\approx$ market price."

- **The numbers to read aloud:**
    - "All four residuals are less than \$0.002 in absolute value --- **two-tenths of a cent**."
    - "$|\text{edge}| < 0.01\%$ --- three orders of magnitude *inside* the $\pm 5\%$ acceptance band (the light-blue stripe)."

- **What it proves.** "Lattice implemented correctly, engine calibrated, residuals tiny, Layer 1 can serve as a fair-value benchmark for the rest of the pipeline."

- **The deeper interpretation.** "This slide is *not* trying to prove market inefficiency --- it shows the opposite: for these live AMD contracts the market is largely efficient because CRR and market prices nearly coincide. **That's actually a strength**: when meaningful deviations *do* appear later (Slides 12--14), they are far more likely to be *real signals* than model errors."

- **Anticipated question:** *"If the residuals are essentially zero, where does the edge come from?"* --- Strong answer: "This is a *live-chain* validation showing the engine is accurate. The edge analysis is performed on the larger historical AAPL dataset and becomes statistically meaningful only when conditioned on specific market regimes --- particularly the herding regime identified on Slides 12 and 13."

- **H1 verdict.** "**Hypothesis H1 passed with substantial margin.** Section 4.2.1 of the report."

# Slide 10 --- CRR Pricing Results: Numerical Convergence

- **The framing question.** "This slide answers: **how many time steps are enough in the CRR lattice?** A binomial model becomes more accurate as $N$ increases, but more steps also mean more computation. The slide shows $N = 100$ is more than sufficient."

- **What's on screen.** "Main panel: option price ($y$) vs.\ lattice steps $N$ ($x$); two curves --- call and put. Inset: $|\,\text{price}(N) - \text{price}(200)\,|$, the residual error against a 200-step benchmark, on a *log* $y$-axis."

- **The convergence story:**
    - "Both call ($\approx \$19$) and put ($\approx \$27$) plateau by $N \approx 25$ steps."
    - "Log-residual crosses the **\$0.01 threshold by $N \approx 100$** --- sub-penny precision."

- **Why the log scale.** "On a normal scale, tiny pricing errors are hard to see. Log scale makes it obvious that error approaches zero very rapidly --- the steeper the downward slope, the faster the lattice converges."

- **The "only two lines" question.** "You may notice only two curves, not four. Buy/sell variants of the same contract price identically: the *action* changes the trade direction, not the model price."

- **Why this matters.** "Slide 10 validated that CRR prices match market prices. This slide validates that those prices are *numerically stable*, not artifacts of a poorly chosen lattice. Implementation correct, solution converges, $N = 100$ gives sub-penny precision while avoiding unnecessary compute."

- **Anticipated question:** *"Why not just use $N = 500$ or $N = 1000$?"* --- Answer: "Because the convergence plot shows *diminishing returns*. Once the residual falls below one cent at $N \approx 100$, additional steps increase runtime without producing a meaningful improvement in pricing accuracy."

- **Anticipated question:** *"Why does the curve oscillate at small $N$?"* --- Answer: "Binomial tree prices alternate between even and odd step counts before stabilizing --- a well-known property of discrete lattices, not a bug."

# Slide 11 --- CRR Pricing Results: Early Exercise Boundary

- **The framing question.** "When should the holder of an American put exercise early instead of continuing to hold? This is something **Black--Scholes cannot show directly** --- the slide visualizes the CRR lattice's answer."

- **The decision line.** "$S^*(t)$ is the *early exercise boundary*. If spot is **above** $S^*$ $\to$ keep holding. If spot is **below** $S^*$ $\to$ exercise immediately. Mathematically the boundary is where Immediate Exercise Value $=$ Continuation Value --- the indifference point."

- **Two cases overlaid:**
    - **AMD live put** (green): $S = \$341.35$, $K = \$350$, slightly OTM. The boundary rises gradually but *never reaches spot* --- **early exercise is never optimal here**.
    - **Deep-ITM illustrative put** (red): $S = \$310$, $K = \$350$. Intrinsic value $= K - S = \$40$ --- substantial. The boundary crosses spot around day 17 (the grey *Exercise Region*) --- after that point, **immediate cash from exercising exceeds the discounted expected continuation value**.

- **Why this slide matters in defense.** "Most of the audience will focus on the ML slides. But this slide validates something deeper: the lattice isn't just producing a *price* --- it is solving the *optimal exercise problem* and identifying *when* exercising is rational. Layer 1 is a genuine American-option pricer, not just a numerical price calculator."

- **Anticipated faculty question:** *"Why would anyone ever exercise a put early?"* --- Answer: "A deep-ITM American put can have very little remaining time value. When the intrinsic value available today exceeds the discounted expected continuation value, exercising immediately maximizes value. The CRR lattice explicitly checks this at every node via $\max(\text{intrinsic},\,\text{continuation})$ --- a capability closed-form Black--Scholes cannot reproduce."

- **Bottom-line takeaway.** "Validates the lattice's American option handling. Section 4.4 of the report."

# Slide 12 --- Cross-Model \& Backtest: L1 vs L2 Cross-Validation

- **The most important slide of the talk.** Slow down here.

- **What the left plot shows.** "X-axis is the CRR (Layer 1) edge. Y-axis is the XGBoost (Layer 2) edge. Each dot is one of 3,000 sampled AAPL contracts, colored by regime. If the dots formed a strong diagonal, both models would agree everywhere. They don't."

- **The aggregate-vs-conditional contrast** (memorize):
    - "**Aggregate Pearson $r = 0.032$.**" Statistically zero across all 3,000 contracts.
    - "**Herding regime: $r = 0.413$ ($p = 2.4 \times 10^{-10}$, $n = 217$).**" Correlation jumps from essentially zero to moderate; the probability this happened by chance is tiny. Agreement appears specifically during crowd-driven conditions.

- **Why aggregate $r \approx 0$ is actually good for the thesis.** "CRR uses no-arbitrage financial theory; XGBoost uses machine learning. They are *structurally independent*. If they agreed everywhere a skeptic could argue they're measuring the same thing through different machinery. The fact that they mostly *do not* agree is what makes the occasions where they *do* agree --- the herding regime --- meaningful."

- **The right-panel headline.** "Both-SELL zone --- Q3, $n = 34$ where CRR *and* XGBoost both say overpriced --- realized ITM rate is **76.5\%** versus a baseline of about **63\%**. If model agreement were meaningless, the agreement bucket would sit at 63\% too; instead it jumps roughly thirteen points. That suggests there is *real predictive information* in the agreement signal."

- **Anticipated question:** *"If the overall correlation is only 0.032, why should we care?"* --- Answer: "Because the aggregate dataset mixes regimes. Once we condition on the herding regime the relationship becomes statistically significant. The aggregate result is *masking* the signal --- a textbook Simpson's paradox. That's what slide 13 unpacks."

- **Bridge.** "Where does the agreement come from? The next slide: the regime detector."

# Slide 13 --- Cross-Model \& Backtest: Regime Detection

- **Open with the headline.** "The market is not always in a herding state. Most of the time there is no strong signal, but during a small subset of days --- about 8.5\% --- the conditions exist where the CRR and XGBoost models begin agreeing and become much more predictive."

- **Walk the three panels top-to-bottom:**

    - **Panel 1 --- IV vs RV30 (top).** Navy = ATM implied vol (what traders are pricing). Red = 30-day realized vol (what actually occurred). "When IV is much higher than RV30, traders are overpaying for volatility out of fear or crowd behavior --- the classic herding signature."

    - **Panel 2 --- RV-IV spread (middle).** "This panel *is* the regime detector. Near zero = normal market. Outside the threshold bands ($\pm 5\%$ normal, $+10\%$ herding) IV and RV are diverging significantly. Large negative values mean IV greatly exceeds RV --- the crowd is pricing in more fear than the data supports."

    - **Panel 3 --- Regime ribbon (bottom).** "Green = Normal, burnt orange = Herding. Most of the chart is green. The orange periods are rare: 104 of 1,223 trading days, exactly 8.5\% --- those are the days the framework flags as potential crowd-driven mispricing opportunities."

- **The COVID anomaly note.** "March 2020 is annotated above the clip lines --- RV peaked at 4.0 and the spread troughed at $-3.6$. We let COVID be annotated, not allowed to dominate the y-axes."

- **The Simpson's Paradox punchline + thesis takeaway.** "Looking at all contracts, CRR and XGBoost barely correlate: $r = 0.032$. Restricting to the herding regime, agreement jumps to $r = 0.413$. The regime detector is the filter that separates signal from noise --- without it the dataset looks random; with it the models begin agreeing and the mispricing signal becomes statistically significant. That is precisely where the strategy has an edge."

- **Anticipated question:** *"Could you predict the regime ahead of time?"* --- Honest answer: "No. The IV/RV30 ratio is *backward-looking*. This is a limitation noted in the Next Steps slide. The point is detection of *current* regime, not prediction of future regime."

# Slide 14 --- Cross-Model \& Backtest: Walk-Forward Backtest

- **The framing.** "Slides 12 and 13 established *that* the models agree under herding. This slide answers: **does that agreement actually make money out-of-sample?** First slide where all three layers work together: L1 detects, L2 validates, L3 sizes (regime-conditioned half-Kelly Normal, quarter-Kelly Herding)."

- **The setup.** "Out-of-sample walk-forward 2017--2021. 57,231 total decisions; only **3,760 actually triggered a trade** (53k+ were no-trade)."

- **The headline numbers** (memorize):
    - "**Cumulative P\&L: \$2.94M on a \$100k base.** Max drawdown $<15\%$ --- circuit breaker never fired. **The capped drawdown matters as much as the profit**: gains weren't taken by extreme risk. (H3 confirmed; \S 4.8.)"
    - "Per-trade hit rate **63.1\%** (2,371 wins vs.\ 1,389 losses) --- materially better than a coin flip."
    - "Mean \$781; median \$1,220. **Median $>$ Mean** = a few large losses pulling the average down (typical left-skewed equity-strategy distribution)."

- **The "no-trade" observation.** "Histogram restricted to the 3,760 executed trades; 53k no-trade rows excluded so they don't overwhelm the distribution. Most ML projects ask 'should I buy?'; this pipeline also asks 'should I do nothing?' The 53k no-trades aren't a bug --- they're the pipeline recognizing that *edge exists only when CRR and XGBoost agree*. **Saying no is the most valuable thing the pipeline does.**"

- **The Brier score validation.** "Layer 2 Brier = 0.211 vs.\ a 0.25 naive baseline (= a useless 50/50 predictor). 0.211 means the probability estimates carry information --- not spectacular, but real. If asked *'is 0.211 good?'*: meaningfully better than baseline, but **performance comes from the framework, not any single layer** --- the classifier is one of three."

- **Anticipated question:** *"How realistic is the \$2.94M figure?"* --- Honest answer: "Single stock, one market cycle, mid-price fills, no transaction-cost/slippage model --- enumerated on the Next Steps slide. **Acknowledging these proactively makes the result more credible, not less.**"

# Slide 15 --- Next Steps

- **The framing question + main message.** "*If this project continued beyond the capstone, what would be done next?* Scope so far: **one primary stock (AAPL) + one historical window (2016--2020) + one ML architecture (XGBoost)**. The next step is *proving the results generalize beyond those conditions* --- current result: framework works on AAPL; next goal: **prove it works everywhere**."

- **Acknowledge the limitations honestly first** (right panel):
    - **Data scope:** AAPL only, single market cycle --- different sectors, volatility environments, and regimes untested.
    - **Volatility surface:** Flat IV per contract; no smile or skew.
    - **Transaction costs:** Mid-price fills; no bid-ask friction or slippage. *Actual trading performance could be lower than reported.*
    - **Regime detection lag:** IV/RV30 ratio is backward-looking. A future model could attempt *forecasting* regime shifts rather than only detecting them.
    - **Kelly assumptions:** Log-utility; no leverage or portfolio-level limits.

- **Four research extensions** (left panel, can read or paraphrase):
    1. Expand option contracts to use other stock datasets to validate the model against.
    2. Run the cross-sectional test across multiple expiration cycles and multiple high-liquidity stocks (e.g., NVDA, MSFT) to prove the pipeline's stability.
    3. Modernize the Layer 2 ML model architecture by replacing XGBoost with **TabPFN v2** --- a transformer-based foundation model for tabular data that delivers state-of-the-art calibrated probability estimates without per-task gradient-boosting training.
    4. Publish open-source framework and Streamlit calculator for community validation and peer review.

- **Anticipated faculty question:** *"If you had another six months, what would you do first?"* --- Answer: "**Cross-sectional validation** across multiple highly liquid stocks --- **NVDA, MSFT, AMD, SPY**. Demonstrating that the framework generalizes beyond AAPL would provide the strongest evidence that the observed results are *not security-specific*."

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

- **Open with the question and the answer.** "*Did the framework work?* Yes. CRR and XGBoost, using *independent* inputs, agree on mispricing direction *in the herding regime* --- the three components (**CRR + XGBoost + Kelly**) provide stronger evidence than any single model alone. The claim is *not* 'markets are always inefficient' --- it's that markets are *usually* efficient **but** during specific herding regimes independent models sometimes agree, and those signals carry predictive value."

- **Three hypotheses confirmed** (one breath each):
    - **H1 --- CRR Benchmark.** Within $1$--$2\%$ of market on $80\%$ of AMD contracts; without H1 the rest collapses.
    - **H2 --- XGBoost Independent Estimator.** Brier $0.211$ vs.\ $0.25$ baseline; no IV leakage --- a genuinely independent estimate.
    - **H3 --- Kelly Sizing.** \$$2.9$M P\&L over $101$k AAPL contracts; max drawdown $<15\%$; the edge survives risk management.

- **The most important sentence in the deck.** "Most trading systems only produce BUY/SELL. This framework also produces **DO NOTHING** when CRR and XGBoost disagree. **That filtering is likely responsible for much of the performance --- the model works precisely because it says *no* when there is no edge.**"

- **Anticipated faculty question:** *"What is the single most important contribution?"* --- Answer: "Demonstrating that **independent agreement** between a no-arbitrage pricer and an IV-free ML model acts as a **filter** for potential mispricing. The value is less in generating more trades and more in **knowing when not to trade**."

- **Other questions to be ready for:** *"What would falsify your result?"* (a regime where L1/L2 disagree but outcomes match L2 only); *"Could you trade this with real money?"* (not without the transaction-cost extensions in Next Steps); *"Why open-source?"* (reproducibility and peer scrutiny are part of the validation).

- **Close with thanks.** "Thank you. I welcome your questions."
