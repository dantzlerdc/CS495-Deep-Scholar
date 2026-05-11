# ── OS detection ──────────────────────────────────────────────────────
ifeq ($(OS),Windows_NT)
    PYTHON  := python
    VENV    := .venv\Scripts
    RM_RF   := rmdir /s /q
    SEP     := \\
else
    PYTHON  := python3.13
    VENV    := .venv/bin
    RM_RF   := rm -rf
    SEP     := /
endif

POETRY  := $(VENV)$(SEP)poetry
PYEXEC  := $(VENV)$(SEP)python

.PHONY: setup run run-animation run-layer2 run-all clean

# ── setup: create venv, install poetry, install project deps ─────────
setup:
	$(PYTHON) -m venv .venv
	$(VENV)$(SEP)pip install --upgrade pip
	$(VENV)$(SEP)pip install poetry
	$(POETRY) install
	@echo ""
	@echo "Setup complete. Activate the virtualenv with:"
ifeq ($(OS),Windows_NT)
	@echo "  .venv\Scripts\activate"
else
	@echo "  source .venv/bin/activate"
endif

# ── run: execute the end-to-end AMD CRR + Kelly pipeline ─────────────
run:
	cd project && ../$(PYEXEC) main.py config.yaml

# ── run-animation: regenerate crr_pipeline_animation.html ────────────
run-animation:
	$(PYEXEC) crr_animation_html.py

# ── run-layer2: run all 7 Layer 2 modules in order ───────────────────
run-layer2:
	@echo "--- Layer 2 Step 1: market_data ---"
	$(PYEXEC) project/market_data.py
	@echo "--- Layer 2 Step 2: p_estimator ---"
	$(PYEXEC) project/p_estimator.py
	@echo "--- Layer 2 Step 3: bias_detector ---"
	$(PYEXEC) project/bias_detector.py
	@echo "--- Layer 2 Step 4: micro_cost ---"
	$(PYEXEC) project/micro_cost.py
	@echo "--- Layer 2 Step 5: calibration ---"
	$(PYEXEC) project/calibration.py
	@echo "--- Layer 2 Step 6: policy ---"
	$(PYEXEC) project/policy.py
	@echo "--- Layer 2 Step 7: backtest ---"
	$(PYEXEC) project/backtest.py
	@echo ""
	@echo "Layer 2 complete. Outputs in project/outputs/"

# ── run-all: Layer 1 (CRR pipeline) then animation then all Layer 2 ──
run-all: run run-animation run-layer2

# ── clean: remove the virtualenv ─────────────────────────────────────
clean:
	$(RM_RF) .venv
