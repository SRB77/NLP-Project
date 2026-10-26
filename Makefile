# Common developer tasks. Run `make help` to list them.
PYTHON ?= .venv/bin/python
NOTEBOOKS := $(wildcard m2_data/0*.ipynb)

.PHONY: help setup data prepare test lint format notebooks check

help:  ## List available targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

setup:  ## Create .venv and install the package with analysis + dev extras
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[analysis,dev]"

data:  ## Download the raw dataset into data/raw/ (~275 MB, pinned revision)
	$(PYTHON) -m medibridge.download

prepare:  ## Rebuild data/processed/ from data/raw/ (deterministic)
	$(PYTHON) -m medibridge.pipeline

test:  ## Run the test suite
	$(PYTHON) -m pytest

lint:  ## Lint code and notebooks
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format:  ## Auto-format code and notebooks
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

notebooks:  ## Re-execute the M2 notebooks in place (needs data/raw/)
	cd m2_data && for nb in $(notdir $(NOTEBOOKS)); do ../$(PYTHON) -m jupyter nbconvert --to notebook --execute --inplace $$nb; done

check: lint test  ## Everything CI runs
