# Privacy Considerations

MediBridge handles **health information**, one of the most sensitive kinds of personal data. This document covers what personal data is in our dataset, what we did about it, and how the finished product would protect real patient data.

## 1. What personal data could be in this dataset?

| Data element | Present? | Risk | Our handling |
|---|---|---|---|
| **Voice recordings** (audio) | Yes | A voice is biometric personal data and can identify a speaker | Not processed in M2. Raw files are kept out of git (`.gitignore`) and fetched from the publisher by `make data` (`medibridge.download`), so **we never redistribute audio** |
| **Speaker ID** | Yes | Could link recordings to a person | Already a hashed value (e.g. `fb127148…`) from the publisher. We never try to reverse it. Missing IDs are set to `"unknown"` |
| **Person names in transcripts** | Yes: 2 `hi` conversations ("मेरा नाम … है" / "my name is …") | Direct identifier | **Masked as `[NAME]`** everywhere in the transcript, with entity offsets shifted (`mask_names` in `src/medibridge/privacy.py`; tested in `tests/test_privacy.py`) |
| **Phone numbers, e-mails, Aadhaar-like 12-digit numbers, URLs** | None found | Direct identifiers | A regex PII scan (`pii_scan` in `src/medibridge/privacy.py`) runs on every transcript. **0 hits** in `hi` and `en`. Any future hit is flagged in the `flag_pii` column |
| **Health conditions and drugs** | Yes (that is the task) | Sensitive if linked to a person | The publisher states the recordings are narrations and demo conversations by staff and medical-college speakers, not real patients. Once the names are masked, no transcript links a condition to a person |
| **Session IDs / file paths** | Yes | Indirect linkage between clips | Used only for leak-free splitting. They contain no personal data (random UUIDs and dates) |

The PII scan and the masking run inside `03_data_cleaning.ipynb`, which shows only the masked text.

## 2. Licence and permitted use

- The dataset is released under the **MIT licence**, which permits use and modification with attribution. Attribution is given in `01_data_card.md` and the README.
- We use the data only for building and evaluating the model, which matches its intended use (evaluating medical speech and text systems).

## 3. Legal context in India

India's **Digital Personal Data Protection Act, 2023 (DPDP Act)**, with the **DPDP Rules, 2025** notified by MeitY in November 2025 and phasing in through 2026–27, governs digital personal data.

| Principle | How this project respects it now | How a deployed MediBridge would respect it |
|---|---|---|
| Lawful purpose and consent | Public, licensed data; no real patients | Clear consent notice to patients before notes or audio are processed; processing only for documentation and claims |
| Purpose limitation | Data used only for this NLP task | Outputs used only for the clinical record and claim; no secondary use such as marketing |
| Data minimisation | Audio not processed; only the text fields we need | Process the note, not the whole patient file; drop audio after transcription |
| Accuracy | Gold labels validated; confidence flags planned | Human review of low-confidence entities before they enter a record |
| Storage limitation | Raw data not committed; can be deleted and re-downloaded | Retention limits; delete intermediate files after processing |
| Security safeguards | Local processing only; no third-party APIs | **On-premise inference** (no patient text leaves the hospital), encryption at rest, access logging, role-based access |
| Breach notification | n/a | Incident-response plan as required by the DPDP Rules |

Health records in India's digital-health system also follow the **Ayushman Bharat Digital Mission (ABDM)** consent framework, where records are shared only with the patient's consent via ABHA. A production integration would follow that consent flow.

## 4. Privacy-by-design decisions in our architecture
1. **Local, open-source models** (IndicTrans2, GLiNER, Whisper) instead of cloud LLM APIs, so no patient text is sent to a third party.
2. **De-identification before storage:** the same `mask_names` and `pii_scan` step will run on real input before anything is logged.
3. **Traceability without exposure:** each English entity keeps offsets into the source note, so a reviewer can verify it without copying more text than needed.
4. **No training on customer data by default:** any future fine-tuning on hospital data would need separate consent and de-identification.

## 5. Ethical considerations and residual risks
- **Re-identification through voice:** even with hashed IDs, voices are identifiable. Mitigation: we never publish audio or audio-derived embeddings.
- **Representation bias:** few speakers (5 known in `hi`) and staged conversations. Accents and dialects not in the data may get worse results. We will report results per context and, in M5, per speaker.
- **Clinical safety:** an extraction error, such as a wrong drug or dose, could cause harm if trusted blindly. The product is a documentation aid with human review, never an autonomous decision-maker.
- **Residual PII:** regex scans can miss unusual identifiers, such as names without a cue phrase. Before any real-data deployment, a dedicated de-identification model (NER for PERSON and LOCATION) would be added.
