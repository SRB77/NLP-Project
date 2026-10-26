# Data Card: Eka Medical ASR Evaluation Dataset (as used in MediBridge)

This card follows the structure of *Datasheets for Datasets* (Gebru et al., 2021) and *Data Cards* (Pushkarna et al., 2022). The numbers come from `02_exploratory_analysis.ipynb`, `data/processed/cleaning_report.json` and `data/processed/split_report.json`.

## 1. Summary

| | |
|---|---|
| **Name** | Eka Medical ASR Evaluation Dataset |
| **Publisher** | EkaCare (Orbi Health Pvt. Ltd.), India |
| **Source** | https://huggingface.co/datasets/ekacare/eka-medical-asr-evaluation-dataset |
| **Version used** | Hugging Face commit `433e66037c8aebb8f396b938624a5ab6afc4ca36` (last modified 2025-07-30). Pinned as `HF_REVISION` in `src/medibridge/config.py` |
| **Licence** | MIT. Free to use with attribution |
| **Modality** | 16 kHz speech audio + human transcript + medical entity spans |
| **Subsets** | `hi`: Hindi / Hinglish, 320 recordings, 1.57 h. `en`: Indian-English, 3,619 recordings, 8.40 h |
| **Our role for it** | `hi` is the **primary** data (it matches the Hinglish product). `en` is **auxiliary** (English-side NER and extra training signal) |

## 2. Motivation and intended use

- **Why the publisher built it:** to evaluate speech recognition for Indian medical scribes, with a focus on medical terminology and Indian branded drugs.
- **Why we use it:** it is the only public dataset we found that combines (a) Hindi–English code-mixed clinical speech and transcripts with (b) gold medical entity spans with character offsets. That is exactly the input and labels of MediBridge: Hinglish clinical text → typed medical entities.
- **Our uses:**
  - M2–M4: text-side entity extraction (transcripts plus spans).
  - M5: speech front-end evaluation (audio plus transcripts).
- **Out of scope:** clinical decision-making, diagnosis, or any use on real patients without further validation.

## 3. Collection process (as stated by the publisher)

- Natural speech recorded by EkaCare's internal team in narrated medical-text sessions and in recorded EkaScribe demonstration sessions with internal medical professionals.
- Additional speakers came from four medical colleges, adding regional accents.
- Eight annotators are listed, most of them medical doctors.
- **We did not collect or re-annotate any data.** We only cleaned and split it (Section 7).

## 4. Composition

### Rows by recording context

| Context | `hi` | `en` | What it is |
|---|---:|---:|---|
| `conversation` | 127 | 110 | Doctor–patient dialogue, the most realistic input. Mixed Devanagari and Latin script |
| `narration_sentence` | 193 | 1,303 | A medical sentence read aloud. In `hi`: drug descriptions written in Devanagari |
| `narration_entity` | — | 2,206 | A single medical term read aloud |
| **Total** | **320** | **3,619** | |

### Entity labels (raw spans, before flattening nested spans)

| Type | `hi` | % | `en` | % | Examples (`hi`) |
|---|---:|---:|---:|---:|---|
| `drugs` | 918 | 48.4 | 2,722 | 23.9 | टैबलेट, मेटफॉर्मिन, Augmentin 650 mg |
| `clinical_findings` | 679 | 35.8 | 5,951 | 52.3 | डायबिटीज, हाई ब्लड प्रेशर, fever |
| `diagnostics` | 129 | 6.8 | 1,046 | 9.2 | एचबीए१सी, CBC lab test, chest X ray |
| `advices` | 104 | 5.5 | 395 | 3.5 | दिन में दो बार, after food |
| `misc_medical` | 67 | 3.5 | 1,259 | 11.1 | दो लीटर, smoking |

### Mapping to the MediBridge schema
We adopt the dataset's 5 clinician-annotated types one-to-one as our English output types (M1 deck, slide 4). That way the system is scored directly against the gold labels:
- `drugs` → DRUG (the dose is part of the span, e.g. "Augmentin 650 mg")
- `clinical_findings` → CLINICAL_FINDING (symptoms and diseases)
- `diagnostics` → DIAGNOSTIC (tests and examinations)
- `advices` → ADVICE (frequency, duration, diet, rest)
- `misc_medical` → MISC_MEDICAL

Finer types such as DOSAGE or BODY_PART are a stretch goal.

### Fields

| Field | Type | Description | Used in M2? |
|---|---|---|---|
| `audio` | audio, 16 kHz | Waveform | No (kept raw for M5) |
| `file_name` | str | Original audio path | No |
| `md5_audio`, `md5_text` | str | Hashes of audio and transcript | Yes: `md5_audio` becomes our row `id`. Both are used for duplicate checks |
| `duration` | float | Seconds | Yes |
| `text` | str | Ground-truth transcript | Yes |
| `audio_language`, `text_language` | str | `hi` or `en` | Checked (constant per subset) |
| `session_id` | str | Recording session | Yes: the split grouping key |
| `speaker` | str or null | Hashed speaker ID. Missing for 127 `hi` and 110 `en` rows | Yes, as `"unknown"` when missing |
| `type_concept` | str | Dominant concept type of the recording | Yes |
| `recording_context` | str | conversation / narration_sentence / narration_entity | Yes: split stratum |
| `medical_entities` | JSON str | `[[text, type, [[start, end], …]], …]` | Yes: the labels |

## 5. Key characteristics (from EDA and statistics)

- **Code-mixing is mostly inside one script.** 93% of `hi` entity spans are in Devanagari, yet many are English words: डायबिटीज (*diabetes*), इन्फेक्शन (*infection*), and dosages as "एमजी" (*mg*, 132 times, versus 3 in Latin script). About 20% of conversation transcripts also contain Latin-script English.
- **Conversations differ from narrations.** They are longer (median 50 vs 36 tokens) and have half the entity density (0.08 vs 0.17 entities per token). The entity type depends strongly on context (χ², Cramér's V ≈ 0.54).
- **Long tail.** About half the vocabulary appears only once, and **68–72% of entity mentions in `hi` val/test never appear in train**.
- **Class imbalance:** about 14 : 1 between the most and least frequent type.

## 6. Known limitations and biases

1. **Small Hindi set.** 320 transcripts, and only 13 conversation sessions, one of which has 24 clips. `hi` test results will have wide confidence intervals.
2. **Few speakers.** `hi` has only 5 known speakers plus 127 rows without an ID, so a speaker-disjoint split is impossible. This matters mostly for speech (M5).
3. **Narrations are scripted.** `hi` narration sentences are drug-leaflet descriptions read aloud: formal, drug-heavy, and unlike real clinic talk.
4. **Simulated conversations.** The conversations come from demonstration sessions by internal staff, not real consultations. Real clinics will be noisier.
5. **Nested and repeated annotations.** 85 nested spans in `hi` and 329 in `en` were moved to `nested_entities` (see cleaning). The 54 duplicate-transcript groups in `en` had conflicting labels; we kept the first copy.
6. **Released as one test split only.** Our train/val/test split is our own, so results are not directly comparable with the publisher's ASR benchmarks.
7. **No English translation of `hi` spans.** The gold labels are Hindi-side spans with English type names. English span text (our product output) must be produced and evaluated by us in M3/M4.

## 7. Preprocessing we applied
Code: `src/medibridge/cleaning.py` (with `text.py`, `spans.py`, `privacy.py`). Walkthrough: `03_data_cleaning.ipynb`.

| Step | `hi` | `en` |
|---|---:|---:|
| Input rows | 320 | 3,619 |
| Texts normalised (NFC, nukta, zero-width, whitespace), offsets remapped | 69 | 120 |
| Nested or overlapping spans moved to `nested_entities` | 85 | 329 |
| Transcripts with a self-introduced name masked as `[NAME]` | 2 | 0 |
| Duplicate transcripts removed | 4 | 292 |
| Rows with no entities (kept, flagged) | 10 | 10 |
| Audio under 1 s (kept, flagged) | 0 | 8 |
| **Output rows** | **316** | **3,327** |
| **Output main entity spans** (all offsets re-validated) | **1,733** | **10,309** |

## 8. Splits
Code: `src/medibridge/split.py`. Verification: `05_train_val_test_split.ipynb`.

| | `hi` train | val | test | `en` train | val | test |
|---|---:|---:|---:|---:|---:|---:|
| Rows | 221 | 48 | 47 | 2,329 | 500 | 498 |
| Sessions | 139 | 32 | 32 | 2,276 | 493 | 491 |
| Entity spans | 1,195 | 253 | 285 | 7,244 | 1,561 | 1,504 |

How the split works:
- Grouped by session **and** normalised transcript (union-find), stratified by recording context, 70/15/15, seed 42.
- **Zero** session, exact-text or normalised-text overlap between splits.
- Entity-type proportions are statistically indistinguishable across `hi` splits (χ² p = 0.59). For `en` the difference is negligible (Cramér's V = 0.03).

## 9. Files

| Path | Content |
|---|---|
| `data/raw/{hi,en}/*.parquet` | Original files (not in git; run `make data`) |
| `data/processed/{hi,en}_{train,val,test}.jsonl` | Clean transcripts with `entities` (character spans), `nested_entities`, metadata and features |
| `data/processed/bio/*.conll` | Token-level BIO tags for token-classification baselines |
| `data/processed/cleaning_report.json`, `split_report.json` | Machine-readable counts for every step |

## 10. Maintenance
- The publisher says it will keep growing the dataset. We pin the commit above so our results are reproducible.
- Rerunning `make prepare` regenerates every processed file deterministically.

## Citation
EkaCare. *Eka Medical ASR Evaluation Dataset.* Hugging Face, 2025. https://huggingface.co/datasets/ekacare/eka-medical-asr-evaluation-dataset (MIT licence).
