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
- override event
- outcome record
- breach record
- evidence pack manifest

These schemas are paired with typed validation models under
`src/credit_gov/schemas/` and deterministic synthetic inputs under
`data/synthetic/monthly-demo/`.
