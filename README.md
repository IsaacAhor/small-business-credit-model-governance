# Small Business Credit Model Governance

This repository contains a practical body of work focused on interpretable
model governance and fair-lending monitoring for machine-learning-based small
business credit underwriting.

The locked endeavor is to develop, validate, and disseminate practical methods,
monitoring protocols, documentation standards, and tools for governance of
machine-learning-based small business credit underwriting systems in the United
States, including adverse action reason generation, less discriminatory
alternative assessment, and ongoing model-risk oversight, to improve regulatory
compliance, decision transparency, and responsible access to small business
credit.

The project is designed to support several connected outputs:

- a framework for governing ML-based small business underwriting systems
- monitoring checklists for explainability, fair lending, and model risk oversight
- implementation-oriented system designs, notebooks, and templates
- practitioner-facing written work that translates the framework into usable methods

## Core Objective

The central objective of this repository is to execute the locked endeavor
through public, reviewable artifacts: methods, monitoring protocols,
documentation standards, templates, synthetic demonstrations, and eventually a
configuration-driven governance evidence engine.

This includes work related to:

- adverse action reason generation and explanation quality
- less discriminatory alternative assessment
- ongoing model-risk oversight
- fairness and compliance monitoring
- governance documentation for deployment and post-deployment review

## Scope

This repository is governance-first and intentionally narrow. It is set up to support:

- policy and control documentation
- model inventory and monitoring structure
- validation and review artifacts
- implementation work once code and demonstration assets are added

It does not assume a fixed modeling stack at this stage.

## Repository Structure

- `docs/`
  Framework and article planning documents.
- `schemas/`
  Phase 1 JSON contracts for governed records and evidence-pack manifests.
- `notebooks/`
  Implementation notes and future analytical notebooks.
- `src/`
  Reusable validation models, CLI entry points, and later workflow code.
- `data/synthetic/`
  Deterministic demonstration inputs for validation and future monitoring runs.
- `tests/`
  Validation checks for schema, typed-model, and synthetic-data integrity.
- `templates/`
  Checklists and governance templates.
- `governance/`
  Control records, inventory templates, validation standards, and change logs.

## Initial Deliverables

The first phase of this repository is structured around four deliverables:

1. A flagship framework for model governance and fair-lending monitoring.
2. A practitioner article aligned to the same endeavor.
3. Reusable governance and fair-lending monitoring checklists.
4. A path toward executable tooling using synthetic or appropriately described
   demonstration data.
5. A Phase 0 system design layer for a governance evidence engine.
6. A Phase 1 data-contract layer with command-line validation.

## Working Scope Discipline

This repository should remain narrowly focused on:

- small business credit underwriting
- model governance
- explainability
- fair-lending monitoring
- interpretable risk oversight

It should avoid drifting into:

- generic AI commentary
- broad fintech branding
- unsupported legal conclusions
- claims of real-world deployment that are not documented

## Evidence Standard

Repository artifacts should distinguish between:

- framework claims
- demonstration outputs
- cited external references
- production or institution-specific evidence

Do not present a synthetic notebook, draft framework, or checklist as evidence
of production deployment. If an artifact is illustrative, label it that way.

## Data Policy

Public artifacts should use synthetic, simulated, or clearly licensed
demonstration data unless a dataset is approved and documented. Data-like files
must not be added casually. Any future non-synthetic data source should have a
documented provenance, permitted use, sensitivity classification, and reviewer.

## Near-Term Priorities

1. Add model-version, threshold-set, and reason-code mapping change review for Phase 5.
2. Expand reviewer-facing validation summaries and signoff depth.
3. Add targeted tests for drift logic, model-change impact, and validation-review behavior.
4. Refine the framework and practitioner article after the executable workflow can produce report excerpts.
5. Preserve public PR, commit, and validation history as implementation milestones land.

## Current Status

This repository now contains:

- a first full framework draft
- a first practitioner article draft
- a first synthetic notebook starter
- reusable monitoring and governance templates
- Phase 0 system design documents for a governance evidence engine
- Phase 1 JSON schemas, typed validation models, deterministic synthetic demo records, and validation tests
- Phase 1A cross-file evidence-integrity validation for the synthetic demo records
- a Phase 2 one-command synthetic monthly monitoring workflow that emits metrics, breaches, issues, and reviewer-ready evidence packs
- a Phase 3 adverse-action reason QA workflow that checks generated reason outputs, records traceable exceptions, and adds reason QA reports to evidence packs
- a Phase 4 fair-lending screening workflow that applies configured comparison groups, creates escalation findings, and adds reviewer notes to evidence packs
- repository guardrails that check required governance artifacts and data discipline

The next steps are to add model-change review, validation summaries, drift
logic, and stronger signoff controls described in the roadmap.
