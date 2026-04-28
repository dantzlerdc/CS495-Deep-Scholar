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

POETRY := $(VENV)$(SEP)poetry

.PHONY: setup clean

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

# ── clean: remove the virtualenv ─────────────────────────────────────
clean:
	$(RM_RF) .venv
