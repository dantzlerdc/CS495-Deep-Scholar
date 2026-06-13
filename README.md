# CS495-Deep-Scholar

CS 495 Capstone Project 6 — Bellevue College, Spring 2026.
**Mathematical and Empirical Models in Agreement:** Cross-Validating CRR
Binomial Pricing and Machine Learning for Crowd Mispricing Detection in
Equity Options.

A three-layer pipeline that prices American options with the
Cox–Ross–Rubinstein binomial lattice (Layer 1), cross-validates the
mispricing edge against an independent XGBoost ITM/OTM classifier
(Layer 2), and converts the cross-validated signal into risk-controlled
capital allocation through a regime-conditioned Kelly Criterion
(Layer 3).

---

## Repository Structure

The repository is organized by purpose so it scales with several
build artifacts (research report, presentation, posters, calculator,
documentation deliverables). Every hand-edited source lives under
`src/`; every rendered output lives under `dist/`.

```
.
├── README.md, CITATION.cff, AUTHORS.md, LICENSE
├── Makefile, pyproject.toml, poetry.lock, .gitignore
│
├── assets/                       Static images shared across documents
│   ├── branding/                 Bellevue College logo, brand tokens
│   ├── figures/                  Hand-curated PNGs, consumer-prefixed
│   │                             (Slide-*, Poster-*, Report-*)
│   └── icons/                    Tool logos for the pipeline flowchart
│
├── src/                          Sources organized by output document
│   ├── report/                   Research report .tex + references.bib
│   ├── presentation/             Beamer slide deck .tex
│   ├── posters/                  Four poster .tex variants + a0header.ps
│   ├── calculator/               Streamlit calculator and HTML animations
│   ├── pipeline-docs/            Generator scripts for documentation PDFs
│   ├── users-guide/              User's-guide Markdown sources
│   └── tools/                    One-off utility scripts
│
├── dist/                         All rendered output artifacts
│   ├── report/                   CS495_Capstone_Research_Report.pdf
│   ├── presentation/             CS495_Capstone_Presentation.pdf
│   ├── posters/                  Three poster PDFs
│   ├── users-guide/              User's-guide PDF (consumed by the
│   │                             calculator's User's Guide tab)
│   ├── pipeline-docs/            Documentation PDFs (build sequence,
│   │                             layers explained, flowchart, etc.)
│   ├── interactive/              HTML animations and dashboards
│   ├── trade-tickets/            AMD Fidelity trade-ticket PDFs
│   ├── submissions/              Final submission copies (_Dantzler.pdf)
│   └── archive/                  Superseded outputs kept for reference
│
├── docs/                         Planning, design, and reference material
│   ├── plans/                    PLAN.md, PLAN2.md, PLAN3.md
│   │   └── archive/              Superseded plan revisions
│   ├── notebooks/                Jupyter planning and literature notebooks
│   └── references/               Academic / instructor reference PDFs
│
├── project/                      Main Python pipeline (Layer 1 CRR engine,
│                                 Layer 2 XGBoost classifier, Layer 3 Kelly)
│
├── slides/                       Script-generated chart figures consumed
│   └── figures/                  by both the report and the presentation
│
├── PosterFigures/                Poster-specific generated figures
│
└── UsersGuideScreens/            Streamlit screenshots for the user's guide
```

### Where to find things

| You want to… | Look in |
|--------------|---------|
| Read the research report | `dist/report/CS495_Capstone_Research_Report.pdf` |
| Read the presentation | `dist/presentation/CS495_Capstone_Presentation.pdf` |
| Read the poster | `dist/posters/CS495-Capstone-Poster-BC.pdf` |
| Run the Streamlit calculator | `src/calculator/crr_binomial_pricing_calculator.py` |
| Edit the research report source | `src/report/CS495_Capstone_Research_Report.tex` |
| Edit the presentation source | `src/presentation/CS495_Capstone_Presentation.tex` |
| Re-run the pipeline | `make run` (Layer 1) / `make run-layer2` / `make run-comparison` / `make run-all` |
| Re-build the user's guide | `make users-guide` |

---

## Project Description

The project addresses two layered questions in quantitative finance:

1. **The classical mispricing question** — when a model produces a
   theoretical fair value that diverges from the observed market
   premium, is the gap large enough to justify a trade?
2. **The cross-validation question** — a single-model edge signal
   cannot self-certify. Is the detected mispricing real, or a model
   artifact?

The proposed answer is to operate two pricing approaches with
structurally independent inputs (Layer 1: no-arbitrage CRR
calibrated on realized volatility; Layer 2: XGBoost trained on
binary outcome labels with implied volatility deliberately excluded)
and use their **agreement** — particularly under a behavioral
regime classifier — as the diagnostic that the mispricing is
structural rather than artifactual.

---

## Objectives

1. Implement the CRR American binomial lattice in vectorized Python
   and price four AMD trade tickets at \\(N=100\\) steps.
2. Validate pricing accuracy within ±5 % of observed Fidelity
   market premiums.
3. Compute Δ, Γ, θ, ν, ρ via centered finite differences and
   validate against platform-reported Greeks.
4. Identify the early-exercise boundary for the AMD American puts.
5. Compute the mispricing edge and Kelly position sizes.
6. Sensitivity-analyze pricing and Kelly fractions across IV, the
   risk-free rate, and time to expiration.
7. Train an independent Layer-2 XGBoost ITM/OTM probability
   classifier (IV deliberately excluded from features) on AAPL
   2016–2020 chain data.
8. Cross-validate Layer-1 and Layer-2 edges on a shared 3,000-contract
   AAPL sample, conditioned on a crowd-bias regime classifier.
9. Walk-forward backtest the integrated three-layer pipeline across
   the AAPL 2017–2021 chronological chain (57,231 trade decisions).

---

## Tools / Technologies

Python 3.13 · Poetry · NumPy · pandas · Matplotlib · SciPy ·
yfinance · XGBoost · scikit-learn · Pillow · Streamlit · LaTeX
(XeLaTeX) · Beamer · TikZ · Git / GitHub.

---

## How to Run

```bash
# One-time environment bootstrap (creates .venv and installs deps)
make setup

# Layer 1 — CRR pricing engine on the live AMD chain
make run

# Layer 2 — XGBoost classifier + regime detector + microstructure
#           costs + walk-forward backtest
make run-layer2

# Layer 3 — Layer 1 vs Layer 2 cross-model comparison
make run-comparison

# Everything (run + run-animation + run-layer2 + run-comparison)
make run-all

# Re-build the calculator's User's Guide PDF
make users-guide

# Launch the Streamlit calculator
streamlit run src/calculator/crr_binomial_pricing_calculator.py
```

LaTeX documents are built directly from their `src/<consumer>/`
folder (e.g. `cd src/report && xelatex CS495_Capstone_Research_Report.tex`)
or via the `make` target that wraps the same.

---

## Team Members

**Author:** DeWayne Dantzler
**Faculty Advisor:** Dr. Pedro Albuquerque

---

## Timeline

Spring 2026 — Bellevue College CS 495 Capstone Project 6.

---

> **Attribution Requirement:** Any academic, research, or commercial usage
> must cite the original repository and authors.
