# Small Business Credit Model Governance

[![CI](https://github.com/IsaacAhor/small-business-credit-model-governance/actions/workflows/ci.yml/badge.svg)](https://github.com/IsaacAhor/small-business-credit-model-governance/actions/workflows/ci.yml)

This repository contains a practical body of work focused on model governance,
fair-lending monitoring, and reviewer-ready documentation for
machine-learning-based small business credit underwriting systems.

## For Reviewers

This repository demonstrates a repeatable governance workflow for
machine-learning-based small business credit underwriting systems. It shows how
a lender, validator, auditor, regulator-facing reviewer, or
policy/compliance professional could organize model records, threshold
reviews, adverse-action reason QA, fair-lending screening triggers, issue
registers, and reviewer-ready evidence packs using synthetic demonstration
data.

## Start Here

If you are new to the repository, use these entry points:

- `START_HERE.md`
  A short review path for understanding the repository quickly.
- `USE_CASES.md`
  Role-based paths for model-risk, fair-lending, compliance, credit policy,
  fintech governance, and research reviewers.
- `IMPLEMENTATION_GUIDE.md`
  A practical sequence for adapting the synthetic workflow into a governed
  monthly review pattern.
- `examples/evidence-packs/monthly-demo/README.md`
  A curated evidence-pack walkthrough that can be inspected without running
  code.

## What This Repository Demonstrates

The repository is meant to show practical execution, not only concept notes. It
brings together public, reviewable artifacts that support a governance workflow
for:

- model records and documentation standards
- threshold configuration and monitoring review
- adverse-action reason generation QA
- fair-lending screening and escalation triggers
- issue tracking and evidence-pack assembly
- ongoing model-risk oversight using deterministic demonstration inputs

## Who This Repository Is For

This repository should be readable and useful to:

- reviewers evaluating the professional value of the work
- non-technical reviewers who need a plain-language view of what the system does
- policy, compliance, fair-lending, validation, and model-risk professionals
- potential adopters evaluating how a governance workflow could be structured
- researchers or practitioners assessing governance methods using synthetic data

## What This Repository Contains

The repository is designed to support several connected outputs:

- a framework for governing ML-based small business underwriting systems
- monitoring checklists for explainability, fair lending, and model-risk oversight
- implementation-oriented system designs, workflows, and templates
- practitioner-facing written work that translates the framework into usable methods
- a configuration-driven governance evidence engine built around synthetic data

## What It Does Not Claim

This repository uses synthetic demonstration data and public documentation
artifacts. It does not claim:

- confidential production deployment
- institution-specific legal conclusions
- broad external adoption
- independent recognition by itself
- automatic certification of regulatory compliance

## Endeavor Alignment

The locked endeavor is to develop, validate, and disseminate practical methods,
monitoring protocols, documentation standards, and tools for governance of
machine-learning-based small business credit underwriting systems in the United
States, including adverse action reason generation, less discriminatory
alternative assessment, and ongoing model-risk oversight, to improve regulatory
compliance, decision transparency, and responsible access to small business
credit.

The central objective of this repository is to execute that endeavor through
public, reviewable artifacts: methods, monitoring protocols, documentation
standards, templates, synthetic demonstrations, and a configuration-driven
governance evidence engine.

## Core Use Cases

- monthly monitoring runs that compute metrics, identify threshold breaches, and
  generate evidence packs
- adverse-action reason review that tests mapping quality, specificity, and
  traceability
- fair-lending screening that flags disparity indicators for governance review
- change-review workflows for model versions, thresholds, and reason-code
  mappings
- independent validation review supported by reviewer-facing summary artifacts

## Scope

This repository is governance-first and intentionally narrow. It is set up to
support:

- policy and control documentation
- model inventory and monitoring structure
- validation and review artifacts
- implementation work tied to a synthetic governance evidence workflow

It does not assume a fixed modeling stack at this stage.

## Repository Structure

- `docs/`
  Framework and article planning documents.
- `docs/releases/`
  Release notes for stable public milestones.
- `START_HERE.md`, `USE_CASES.md`, and `IMPLEMENTATION_GUIDE.md`
  Reviewer and adopter entry points.
- `schemas/`
  Phase 1 JSON contracts for governed records and evidence-pack manifests.
- `notebooks/`
  Implementation notes and future analytical notebooks.
- `src/`
  Reusable validation models, CLI entry points, and later workflow code.
- `data/synthetic/`
  Deterministic demonstration inputs for validation and future monitoring runs.
- `examples/`
  Curated synthetic example outputs that can be reviewed without running code.
- `tests/`
  Validation checks for schema, typed-model, and synthetic-data integrity.
- `templates/`
  Checklists and governance templates.
- `governance/`
  Control records, inventory templates, validation standards, and change logs.

## Initial Deliverables

The first phase of this repository is structured around six deliverables:

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

## Reproducibility

Run Phase 1 data-contract validation:

```bash
python scripts/validate_phase1.py
```

Run the monthly monitoring workflow against the default synthetic dataset:

```bash
python scripts/run_monthly_monitoring.py data/synthetic/monthly-demo --evidence-root evidence
```

Run the repository tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Run repository guardrails:

```bash
python scripts/validate_repository.py
```

## Versioned Releases

This repository now uses versioned releases to mark stable public milestones.
Releases package coherent review points; commits remain the development history.

The first release milestone is `v0.4.0`, covering Phases 0 through 4: system
design, data contracts, evidence integrity, monthly monitoring, adverse-action
reason QA, fair-lending screening, and reviewer-facing project packaging.

The latest patch milestone is `v0.4.1`, which adds outsider-facing review and
implementation entry points without changing the Phase 4 technical scope.

See `docs/release-strategy.md`, `docs/releases/v0.4.0.md`, and
`docs/releases/v0.4.1.md`.

## Data Policy

Public artifacts should use synthetic, simulated, or clearly licensed
demonstration data unless a dataset is approved and documented. Data-like files
must not be added casually. Any future non-synthetic data source should have a
documented provenance, permitted use, sensitivity classification, and reviewer.

## Near-Term Priorities

1. Tag the current outsider-packaging patch milestone as `v0.4.1`.
2. Add model-version, threshold-set, and reason-code mapping change review for Phase 5.
3. Expand reviewer-facing validation summaries and signoff depth.
4. Add targeted tests for drift logic, model-change impact, and validation-review behavior.
5. Refine the framework and practitioner article after the executable workflow can produce report excerpts.
6. Preserve public PR, commit, release, and validation history as implementation milestones land.

## Current Status

This repository now contains:

- a first full framework draft
- a first practitioner article draft
- synthetic monitoring demonstration assets
- reusable monitoring and governance templates
- Phase 0 system design documents for a governance evidence engine
- Phase 1 JSON schemas, typed validation models, deterministic synthetic demo records, and validation tests
- Phase 1A cross-file evidence-integrity validation for the synthetic demo records
- a Phase 2 one-command synthetic monthly monitoring workflow that emits metrics, breaches, issues, and reviewer-ready evidence packs
- a Phase 3 adverse-action reason QA workflow that checks generated reason outputs, records traceable exceptions, and adds reason QA reports to evidence packs
- a Phase 4 fair-lending screening workflow that applies configured comparison groups, creates escalation findings, and adds reviewer notes to evidence packs
- release strategy documentation and `v0.4.0` release notes for stable milestone preservation
- `v0.4.1` outsider-packaging notes and reviewer entry points
- repository guardrails that check required governance artifacts and data discipline

The next steps are to add model-change review, validation summaries, drift
logic, and stronger signoff controls described in the roadmap.
