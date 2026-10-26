# M1 References

The numbers match the references slide in `M1_Problem_Definition.pdf`. Caveats are noted where a figure needs one.

## Problem and market evidence

1. Sinsky C. et al. *Allocation of Physician Time in Ambulatory Practice: A Time and Motion Study in 4 Specialties.* Annals of Internal Medicine 165:753–760, 2016. doi:10.7326/M16-0961.
   - 57 US physicians were observed for 430 hours.
   - For every hour of direct patient time, they spent nearly 2 hours on EHR and desk work, plus 1–2 hours after hours.
   - Summary: https://www.advisory.com/daily-briefing/2016/09/08/documentation-time
2. Kaiser Permanente / The Permanente Medical Group. *Ambient AI scribes*, NEJM Catalyst.
   - About 15,791 documentation hours saved, across 7,260 physicians and about 2.5M encounters (Oct 2023 – Dec 2024).
   - The time savings are self-reported estimates.
   - https://www.ama-assn.org/practice-management/digital-health/ai-scribes-save-15000-hours-and-restore-human-side-medicine
   - https://www.beckershospitalreview.com/healthcare-information-technology/ai/16k-hours-saved-ambient-ai-scribes-at-kaiser-permanente/
3. Census of India 2011, language data.
   - Hindi including dialects: 52.83 crore speakers (43.63%). Hindi alone as mother tongue is about 32.2 crore.
   - https://en.wikipedia.org/wiki/Multilingualism_in_India
4. Ministry of Health & Family Welfare, written reply to the Rajya Sabha, Dec 2025.
   - 13,88,185 registered allopathic doctors. Doctor–population ratio 1:811, which counts allopathic and AYUSH practitioners and assumes 80% availability.
   - https://medicaldialogues.in/news/health/doctors/indias-doctor-population-ratio-1811-govt-tells-parliament-159970
5. PIB / ABDM fact sheet, Jul 2026.
   - Over 104 crore health records linked to over 93 crore ABHA accounts.
   - https://ianslive.in/ayushman-bharat-digital-mission-links-over-104-crore-health-records--20260706133553
6. IRDAI Annual Report FY24, as reported by Business Standard (Dec 2024).
   - ₹26,000 crore in health claims repudiated (up 19.1%), and 11% of claims denied.
   - This figure is not specific to documentation problems.
   - https://www.business-standard.com/finance/personal-finance/health-insurance-claims-rejection-up-19-10-in-fy24-irdai-report-124122700754_1.html
7. Indian clinical speech AI vendors (all figures vendor-reported):
   - Eka Care Parrotlet-a v2 / EkaScribe, over 3,000 doctors: https://www.digitalhealthnews.com/eka-care-unveils-clinical-speech-model-parrotlet-for-medical-transcription
   - Augnito, over 4,000 doctors: https://analyticsindiamag.com/indias-first-speech-recognition-system-for-healthcare-industry-the-startup-story-of-augnito/

## Related work (past experiments)

8. Singh V., Vijay D., Akhtar S. S., Shrivastava M. *Named Entity Recognition for Hindi-English Code-Mixed Social Media Text.* NEWS Workshop @ ACL 2018. https://aclanthology.org/W18-2405/
9. Jain A., Paranjape B., Lipton Z. C. *Entity Projection via Machine Translation for Cross-Lingual NER.* EMNLP-IJCNLP 2019. https://aclanthology.org/D19-1100/
10. Gala J. et al. *IndicTrans2: Towards High-Quality and Accessible MT Models for All 22 Scheduled Indian Languages.* TMLR 2023. https://arxiv.org/abs/2305.16307
11. Zaratiana U., Tomeh N., Holat P., Charnois T. *GLiNER: Generalist Model for NER using Bidirectional Transformer.* NAACL 2024. https://arxiv.org/abs/2311.08526
12. Dou Z.-Y., Neubig G. *Word Alignment by Fine-tuning Embeddings on Parallel Corpora* (awesome-align). EACL 2021. https://arxiv.org/abs/2101.08231
13. Bhogale K. et al. *Vistaar: Diverse Benchmarks and Training Sets for Indian Language ASR.* Interspeech 2023. https://arxiv.org/abs/2305.15386 and https://github.com/AI4Bharat/vistaar
14. Ghosh A. et al. *MedSumm: A Multimodal Approach to Summarizing Code-Mixed Hindi-English Clinical Queries.* ECIR 2024 (introduces the MMCQS dataset). https://arxiv.org/abs/2401.01596
15. Srivastava V., Singh M. *PHINC: A Parallel Hinglish Social Media Code-Mixed Corpus for Machine Translation.* W-NUT 2020. https://arxiv.org/abs/2004.09447 and https://zenodo.org/records/3605597
16. *COMI-LINGUA: Expert Annotated Large-Scale Dataset for Multitask NLP in Hindi-English Code-Mixing*, 2025. https://arxiv.org/abs/2503.21670
17. *Named-entity recognition for Hindi language using context pattern-based maximum entropy* (HHD corpus). Computer Science 23(1), 2022. doi:10.7494/csci.2022.23.1.3977. https://repo.agh.edu.pl/handle/AGH/113299

18. EkaCare. *Eka Medical ASR Evaluation Dataset.* Hugging Face, 2025 (MIT licence). This is the primary dataset chosen in M2, and it includes the ASR benchmark (Whisper-v3 large WER 0.157 and Parrotlet-a-en-5b WER 0.109 on the English subset). https://huggingface.co/datasets/ekacare/eka-medical-asr-evaluation-dataset
19. Das A., Gambäck B. *Identifying Languages at the Word Level in Code-Mixed Indian Social Media Text.* ICON 2014. This paper defines the Code-Mixing Index used in the M2 analysis.

## M2 findings cited in the deck
All of these come from our own analysis in `m2_data/`:
- 93% of Hindi entity spans are in Devanagari (`02_exploratory_analysis.ipynb`).
- 68–72% of val/test entity mentions are out-of-vocabulary, Cramér's V = 0.54, and the class imbalance is about 14 : 1 (`04_statistical_analysis.ipynb`).
- The splits are 221 / 48 / 47 with zero leakage (`05_train_val_test_split.ipynb`).
- The privacy scan found nothing, and 2 names were masked (`03_data_cleaning.ipynb`).

## Datasets (supporting)

- **MMCQS (MedSumm):** https://github.com/ArkadeepAcharya/MedSumm-ECIR2024 (release status not yet checked)
- **Synthetic Indian Clinical Notes v2:** https://data.mendeley.com/datasets/bzgjmph5n2/1. Other versions: https://data.mendeley.com/datasets/nn5r5htbpx
- **PHINC:** https://huggingface.co/datasets/veezbo/phinc
- **COMI-LINGUA:** https://huggingface.co/datasets/LingoIITGN/COMI-LINGUA
- **Eka Medical ASR evaluation set (MIT):** https://aikosh.indiaai.gov.in/home/datasets/details/eka_medical_asr_evaluation_dataset.html

## Privacy

20. Digital Personal Data Protection Act 2023, and the DPDP Rules 2025 notified by MeitY in Nov 2025, which phase in through 2026–27. https://www.scconline.com/blog/post/2025/11/14/meity-notified-digital-personal-data-protection-rules-2025/
