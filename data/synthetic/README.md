# Synthetic Data

This directory contains deterministic synthetic and demonstration-only records
for the governance evidence engine.

Rules:

- no real applicant, borrower, or institution data belongs here
- filenames should include `synthetic` or `demo` when the file type is treated as data by repository guardrails
- each dataset should disclose its synthetic status and intended monitoring use
- inputs should remain stable so validation tests and future workflow runs are reproducible

The datasets under this directory support validation, monthly monitoring,
controlled-breach, no-breach, adverse-action reason QA, and fair-lending
screening demonstrations.
