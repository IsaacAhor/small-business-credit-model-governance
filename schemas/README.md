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

Vendor-model oversight contracts:

- vendor risk review record
- vendor model component
- vendor model limitation
- vendor oversight configuration
- vendor event record
- business-credit notice control

Separate recourse-assessment contracts:

- recourse subject record
- recourse method record
- recourse action set
- recourse review configuration
- synthetic prediction model
- recourse assessment output

The optional bundle is backward compatible: datasets with none of the four
files retain the original contract. If any bundle file is present, validation
requires all four, checks their model/version/method/validation/threshold links,
and requires the evidence-pack manifest to reference each file.

These schemas are paired with typed validation models under
`src/credit_gov/schemas/` and deterministic synthetic inputs under
`data/synthetic/monthly-demo/`.

The vendor contracts are validated as a separate linked bundle against a core
model/version/decision/reason context. This preserves backward compatibility
for existing datasets. The vendor validator fails on missing evidence, broken
IDs, unresolved opaque-component controls, mismatched risk tiers, insufficient
heightened monitoring, unknown decisions or mappings, and unlinked events.

The recourse input contracts are also a separate all-or-none bundle and are not
added to the core mandatory schema tuple. They link to stable decision,
model/version, method/version, and action-set/version context while keeping
subject features and outputs outside required reason and notice records. The
closed output schema rejects reason, mapping, and notice fields.
