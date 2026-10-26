# MediBridge

This project turns Hindi–English (Hinglish) clinical notes into readable, structured English records. For each note it returns:
- an English translation
- a list of medical entities, each with its original Hindi/Hinglish span, its English span and an English type

NLP semester project, Industry Track, team of 4.

| Milestone | Folder | Status |
|---|---|---|
| M1 — Problem definition & business case | [m1_presentation/](m1_presentation/) | Deck ready |
| M2 — Data understanding & preparation | [m2_data/](m2_data/) | Ready: see [m2_data/README.md](m2_data/README.md) |
| M3 — Baseline & model development | `src/medibridge/` | — |
| M4 — Evaluation & optimisation | — | — |
| M5 — Deployment prototype | — | — |
| M6 — Final delivery | — | — |

## Quick start

```bash
make setup      # create .venv and install the package (editable) with analysis + dev extras
make data       # download the raw dataset into data/raw/ (~275 MB, pinned revision)
make prepare    # rebuild data/processed/ from data/raw/ (deterministic)
make test       # run the test suite
make help       # list every target
```

Without `make`:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[analysis,dev]"
medibridge-download && medibridge-prepare && pytest
```

The processed splits are committed, so `make data` and `make prepare` are only needed to regenerate them. Notebooks and model code can use `data/processed/` straight away.

## Repository layout

```
├── src/medibridge/          # the Python package (all reusable code lives here)
│   ├── config.py            #   paths and tunable constants (split ratios, seed, thresholds)
│   ├── download.py          #   CLI: fetch the raw dataset              → medibridge-download
│   ├── pipeline.py          #   CLI: raw → cleaned, split, reported     → medibridge-prepare
│   ├── io.py                #   load raw data / processed splits; write JSONL, CoNLL, JSON
│   ├── spans.py             #   entity span type, parsing, validation, overlap handling
│   ├── text.py              #   tokenizer, script tagging, code-mixing index, normalisation
│   ├── privacy.py           #   PII scan and name masking
│   ├── bio.py               #   character spans → BIO token tags
│   ├── cleaning.py          #   the cleaning pipeline: clean()
│   └── split.py             #   leak-free stratified train/val/test split
├── tests/                   # pytest: one file per module + integrity checks on data/processed/
├── data/
│   ├── raw/                 # downloaded parquet (git-ignored)
│   └── processed/           # cleaned splits (JSONL + BIO CoNLL) and reports (committed)
├── m1_presentation/         # M1 deck (PDF) and its references
├── m2_data/                 # M2 deliverables: data card, notebooks, privacy, figures
├── pyproject.toml           # package metadata, dependencies, ruff + pytest configuration
├── Makefile                 # developer tasks
└── .github/workflows/ci.yml # lint + tests on every push / pull request
```

### How the data pipeline fits together

```
download.py ──► data/raw/*.parquet
                     │  io.load_raw
                     ▼
cleaning.clean ── spans.parse_entities → text.normalize_text → spans.resolve_overlaps
                  → privacy.mask_names → spans.validate_spans → features
                     │
                     ▼
split.assign_splits ── union-find leak groups → stratified greedy assignment
                     │
                     ▼
io.write_jsonl / io.write_conll ──► data/processed/  (+ cleaning_report.json, split_report.json)
```
`pipeline.py` runs these steps in order.

### Using the data in model code

```python
from medibridge.io import load_split

train = load_split("hi", "train")  # columns: id, text, entities, nested_entities, context, …
train.entities[0]  # [{"start": 42, "end": 48, "text": "stress", "type": "clinical_findings"}, …]
```

## Engineering conventions

- **All reusable logic goes in `src/medibridge/`.** Notebooks import from the package and only analyse and present. Never copy functions into a notebook.
- **Configuration goes in `config.py`.** No magic numbers or paths elsewhere.
- **Entity spans are plain dicts** (`spans.Span`) with `start`/`end` character offsets. `end` is exclusive, and `text[start:end] == span["text"]` must always hold. Any function that edits text must remap the offsets and re-validate.
- **Style:** `ruff` handles linting and formatting (line length 100), with type hints on public functions and docstrings that explain *why*, not just *what*. Run `make format` before committing.
- **Tests:** every module has a `tests/test_<module>.py`. `make check` (lint + tests) must pass; CI runs the same checks.
- **Data:** raw data is never committed. Processed data is regenerated only through `make prepare`, so the outputs are reproducible from the pinned dataset revision.
- **Commits:** use small, focused commits with an imperative subject line, e.g. `Add BIO export for nested spans`.
