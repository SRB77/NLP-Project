"""MediBridge: Hinglish clinical text -> structured English medical entities.

Modules:
    config     paths and tunable constants
    download   fetch the raw dataset
    io         load raw data / processed splits, write JSONL, CoNLL and JSON
    spans      entity span parsing, validation and overlap handling
    text       tokenizer, script tagging, code-mixing index, normalisation
    privacy    PII scan and name masking
    bio        character spans -> BIO token tags
    cleaning   the cleaning pipeline (`clean`)
    split      leak-free stratified train/val/test split
    pipeline   end-to-end data preparation (`medibridge-prepare`)
"""

__version__ = "0.2.0"
