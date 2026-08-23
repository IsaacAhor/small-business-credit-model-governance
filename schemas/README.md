# Schemas

This directory contains the Phase 1 JSON schemas for the governance evidence
engine.

Current contracts:

- model registry record
- model version record
- threshold set
- application decision record
- score output
- reason-code mapping
- adverse-action reason output
- fair-lending screening config
- override event
- outcome record
- breach record
- evidence pack manifest

Optional model-governance bundle contracts:

- model risk profile
- explainability method record
- model validation record
- model monitoring plan

The optional bundle is backward compatible: datasets with none of the four
files retain the original contract. If any bundle file is present, validation
requires all four, checks their model/version/method/validation/threshold links,
and requires the evidence-pack manifest to reference each file.

These schemas are paired with typed validation models under
`src/credit_gov/schemas/` and deterministic synthetic inputs under
`data/synthetic/monthly-demo/`.
