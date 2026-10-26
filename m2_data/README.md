# M2: Data Understanding & Preparation

**Objective (from the handbook):** understand, clean and prepare the data responsibly so it is ready for modelling.
**Dataset:** Eka Medical ASR Evaluation Dataset (EkaCare, MIT licence). `hi` (Hinglish, primary) has 320 transcripts; `en` (auxiliary) has 3,619.

## Deliverables checklist

| Handbook deliverable | Where to find it | Evidence |
|---|---|---|
| ☑ **Data card** | [01_data_card.md](01_data_card.md) | Source, licence, collection, composition, field dictionary, limitations, preprocessing, splits |
| ☑ **Exploratory analysis** | [02_exploratory_analysis.ipynb](02_exploratory_analysis.ipynb) | 5 figures, code-mixing analysis, entity analysis, data-quality audit, key findings |
| ☑ **Data cleaning** | [03_data_cleaning.ipynb](03_data_cleaning.ipynb) + [`src/medibridge/cleaning.py`](../src/medibridge/cleaning.py) | 10-step pipeline with before/after counts; every entity offset re-validated |
| ☑ **Statistical analysis** | [04_statistical_analysis.ipynb](04_statistical_analysis.ipynb) | χ² + Cramér's V, Mann–Whitney U, Spearman, Zipf, OOV rates, class imbalance, bootstrap CI |
| ☑ **Train / validation / test split** | [05_train_val_test_split.ipynb](05_train_val_test_split.ipynb) + [`src/medibridge/split.py`](../src/medibridge/split.py) | 70/15/15, grouped by session and text, stratified by context. **0 leakage**, verified by tests |
| ☑ **Privacy considerations** | [06_privacy_considerations.md](06_privacy_considerations.md) | PII scan (0 identifier hits), 2 names masked, audio not redistributed, DPDP Act 2023 mapping |
| Expected outcome: *documented, leak-free, clean splits, ready for modelling* | [`data/processed/`](../data/processed/) | Span JSONL + BIO CoNLL per split; `tests/` (40 tests pass) |

## Key findings
1. **Hidden code-mixing.** 93% of Hindi entity spans are in Devanagari, yet many are English words (डायबिटीज = diabetes, इन्फेक्शन = infection, "एमजी" = mg). Script-based language ID underestimates the mixing, so the pipeline must handle **transliterated English**.
2. **Context matters.** Entity type depends strongly on recording context (χ² p ≈ 10⁻¹⁰⁸, Cramér's V = 0.54). Conversations are longer and have half the entity density of narrations, so we stratify splits by context and will report metrics per context.
3. **Memorisation won't work.** 68–72% of entity mentions in `hi` val/test never occur in train. This supports a zero-shot / translation-based design (GLiNER + IndicTrans2) over a dictionary.
4. **Imbalanced labels.** There are about 14× more `drugs` spans than `misc_medical` spans, so we report macro-F1 and consider class weights.
5. **Data quality fixed.** 69 + 120 texts normalised (nukta forms, whitespace, zero-width characters), 296 duplicates removed, and 414 nested spans preserved separately. All 12,042 output spans are verified against the text.
6. **Leak-free splits.** Zero session or transcript overlap, and `hi` entity-type proportions are equal across splits (χ² p = 0.59).

## Folder contents
```
m2_data/
  01_data_card.md                  data card
  02_exploratory_analysis.ipynb    EDA (figures → figures/)
  03_data_cleaning.ipynb           cleaning walkthrough
  04_statistical_analysis.ipynb    statistical tests
  05_train_val_test_split.ipynb    split + leakage verification
  06_privacy_considerations.md     privacy
  figures/                         8 PNG charts
../src/medibridge/                 reusable package (see the repository README for the module map)
../tests/                          unit tests + integrity checks on data/processed/
../data/processed/                 {hi,en}_{train,val,test}.jsonl, bio/*.conll, *_report.json
```

## Reproduce
```bash
make setup       # .venv + pip install -e ".[analysis,dev]"
make data        # ~275 MB parquet → data/raw/ (pinned revision)
make prepare     # data/raw/ → data/processed/ (deterministic)
make test        # 40 tests
make notebooks   # re-execute the notebooks in place
```

## Processed record format (`data/processed/*.jsonl`)
```json
{"id": "942d0c98…", "subset": "hi", "context": "conversation",
 "text": "… It could be stress related or migraine, अच्छा। …",
 "entities": [{"start": 42, "end": 48, "text": "stress", "type": "clinical_findings"}, …],
 "nested_entities": [], "session_id": "5482F557-…", "speaker": "unknown",
 "duration": 20.4, "n_tokens": 54, "n_entities": 6, "pct_devanagari": 0.48, "pct_latin": 0.35,
 "cmi": 42.22, "flag_no_entities": false, "flag_short_audio": false, "flag_pii": false}
```
Load a split with `from medibridge.io import load_split; load_split("hi", "train")`.
