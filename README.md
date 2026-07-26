# Small Business Credit Model Governance

[![CI](https://github.com/IsaacAhor/small-business-credit-model-governance/actions/workflows/ci.yml/badge.svg)](https://github.com/IsaacAhor/small-business-credit-model-governance/actions/workflows/ci.yml)

This repository contains reproducible governance methods, documentation
standards, and public-data run kits for model-risk monitoring, fair-lending
review, and reviewer-ready documentation for machine-learning-based small
business credit underwriting systems.

## For Reviewers

This repository demonstrates repeatable governance methods for
machine-learning-based small business credit underwriting systems. It shows how
a lender, validator, auditor, regulator-facing reviewer, or
policy/compliance professional could organize model records, threshold
reviews, adverse-action reason QA, fair-lending screening triggers, issue
registers, and reviewer-ready evidence packs using synthetic fixtures and
clearly scoped public-data run kits.

The workflow generates adverse-action reasons from ranked decision drivers
(then reviews them via reason QA), reports statistical significance on every
fair-lending disparity screen (two-proportion z-test with Fisher's exact
fallback), estimates protected-class proxies via BISG (Bayesian Improved
Surname Geocoding) with proxy-weighted disparity testing, and ships a
portfolio-scale synthetic dataset (`data/synthetic/monthly-portfolio`, 320
decisions) so screens and exceptions fire on realistic distributions. As a
supporting risk-management component, it also includes a
less-discriminatory-alternative (LDA) assessment step that scores a supplied
candidate model against the baseline; see `docs/fair-lending-statistics.md`
for the statistical methodology.

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
- `examples/evidence-packs/monthly-portfolio/README.md`
  A curated portfolio-scale evidence-pack walkthrough (320 synthetic
  decisions, with statistical significance results, BISG proxy screening, and
  LDA assessment) that can be inspected without running code. A minimal
  controlled-breach pack is under `examples/evidence-packs/monthly-demo/`.
- `docs/adverse-action-reason-run-kit/README.md`
  A one-folder reviewer and operator entry point for the synthetic adverse-
  action reason accuracy benchmark, including run command, limitations,
  benchmark spec, private-data requirements, and evidence-pack review path.

## What This Repository Demonstrates

The repository is meant to show practical execution, not only concept notes. It
brings together public, reviewable artifacts that support a governance workflow
for:

- model records and documentation standards
- threshold configuration and monitoring review
- adverse-action reason generation and reason accuracy QA
- fair-lending screening with statistical significance testing and
  escalation triggers
- BISG protected-class proxy estimation with proxy-weighted disparity
  screening
- issue tracking and evidence-pack assembly
- ongoing model-risk oversight using deterministic demonstration inputs

## Who This Repository Is For

This repository should be readable and useful to:

- legal and policy professionals reviewing the practical value of the work
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
- a configuration-driven governance evidence engine supported by synthetic
  fixtures and clearly scoped public-data run kits

## What It Does Not Claim

This repository uses synthetic demonstration data, clearly scoped public
datasets, and public documentation artifacts. It does not claim:

- confidential production deployment
- institution-specific legal conclusions
- broad external adoption
- independent recognition by itself
- automatic certification of regulatory compliance

## License and Citation

The repository is licensed under the Apache License 2.0 (see `LICENSE`),
which includes an explicit patent grant so institutions can evaluate and
adapt the workflow. Citation metadata is provided in `CITATION.cff`.

## Project Objective

The objective of this project is to develop, validate, and disseminate practical methods,
monitoring protocols, documentation standards, and tools for governance of
machine-learning-based small business credit underwriting systems in the United
States, including adverse action reason generation, less discriminatory
alternative assessment, and ongoing model-risk oversight, to improve regulatory
compliance, decision transparency, and responsible access to small business
credit.

The repository pursues that objective through public, reviewable artifacts:
methods, monitoring protocols, documentation standards, templates, synthetic
fixtures, public-data run kits, and a configuration-driven governance evidence
engine.

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
  Reusable validation, monitoring, reason-generation, LDA assessment, and
  model-change validation code.
- `data/synthetic/`
  Deterministic demonstration inputs for validation, monitoring, and portfolio-scale workflow runs.
- `data/reference/bisg/`
  Demonstration BISG reference tables with a documented path to full Census-derived data.
- `examples/`
  Curated synthetic example outputs that can be reviewed without running code.
- `tests/`
  Validation checks for schemas, typed models, synthetic-data integrity, monitoring, reason QA, fair-lending screening, reason generation, LDA assessment, and model-change validation.
- `templates/`
  Checklists and governance templates.
- `governance/`
  Control records, inventory templates, validation standards, and change logs.

## Initial Deliverables

The first phase of this repository is structured around six deliverables:

1. A flagship framework for model governance and fair-lending monitoring.
2. A practitioner article aligned to the same objective.
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

Run the adverse-action reason accuracy benchmark after reviewing the landing run kit:

`docs/adverse-action-reason-run-kit/README.md`

```bash
python scripts/run_adverse_action_reason_benchmark.py --overwrite
```

Run the standalone Phase 5 model-change and validation review (the portfolio
dataset ships the prior-version comparison inputs):

```bash
python scripts/run_change_validation.py data/synthetic/monthly-portfolio
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

The first release milestone was `v0.4.0`, covering Phases 0 through 4: system
design, data contracts, evidence integrity, monthly monitoring, adverse-action
reason QA, fair-lending screening, and reviewer-facing project packaging.

The latest documented milestone is `v0.8.0`, which adds the synthetic adverse-
action reason accuracy and transparency benchmark. The benchmark is a public,
on-domain synthetic run kit for reason generation, driver-to-reason mapping,
reason QA, and evidence-pack review under Regulation B 12 CFR 1002.9. It is not
public proof of live small-business notice accuracy, lender adoption,
deployment, legal compliance, or regulatory approval.

The prior release, `v0.7.0`, adds the SBA 7(a) public-data monitoring run kit:
an adapter for real SBA 7(a)/504 FOIA loan-level data, a synthetic schema
fixture for pipeline validation, reproducibility documentation, and
scope/limitations notes. The run kit is designed to exercise model-risk
monitoring and drift reporting on real approved-loan public data; it is not an
underwriting model, fairness analysis, adverse-action analysis, deployment
claim, or legal conclusion. The prior substantive analytical milestone,
`v0.6.0`, adds statistical significance testing for fair-lending screens and
optional BISG proxy monitoring on the portfolio-scale synthetic dataset.

See `docs/release-strategy.md`, `docs/releases/v0.4.0.md`,
`docs/releases/v0.4.1.md`, `docs/releases/v0.5.0.md`,
`docs/releases/v0.6.0.md`, `docs/releases/v0.6.1.md`,
`docs/releases/v0.6.2.md`, `docs/releases/v0.6.3.md`, and
`docs/releases/v0.7.0.md`.

## Data Policy

Public artifacts should use synthetic, simulated, or clearly licensed
demonstration data unless a dataset is approved and documented. Data-like files
must not be added casually. Any future non-synthetic data source should have a
documented provenance, permitted use, sensitivity classification, and reviewer.

## Near-Term Priorities

1. Complete the Phase 8 analytical-rigor track: an LDA step that searches
   candidate models and a reproducible run on a recognizable public dataset.
2. Add drift logic and regression controls to strengthen the analytical layer.
3. Refine the framework and practitioner article after the portfolio-scale workflow produces report excerpts.
4. Preserve public PR, commit, release, and validation history as implementation milestones land.

The core Phase 5 change-and-validation workflow is now implemented; the remaining
gaps above are analytical-rigor and dissemination work, not change-governance
plumbing.

## Current Status

This repository now contains:

- a first full framework draft
- a publish-ready practitioner article and archived working drafts
- synthetic monitoring demonstration assets
- reusable monitoring and governance templates
- Phase 0 system design documents for a governance evidence engine
- Phase 1 JSON schemas, typed validation models, deterministic synthetic demo records, and validation tests
- Phase 1A cross-file evidence-integrity validation for the synthetic demo records
- a Phase 2 one-command synthetic monthly monitoring workflow that emits metrics, breaches, issues, and reviewer-ready evidence packs
- a Phase 3 adverse-action reason QA workflow that checks generated reason outputs, records traceable exceptions, and adds reason QA reports to evidence packs
- a Phase 4 fair-lending screening workflow that applies configured comparison groups, creates escalation findings, and adds reviewer notes to evidence packs
- a Phase 3B adverse-action reason-generation workflow with deterministic regeneration checks
- a Phase 4B less-discriminatory-alternative assessment workflow integrated into optional monitoring evidence outputs
- a portfolio-scale synthetic monthly dataset that exercises reason generation, reason QA, fair-lending screening, and LDA assessment
- a Phase 5 model-change and validation-review workflow that compares prior and current model-version, threshold-set, and reason-code mapping records, summarizes change impact, and emits a reviewer signoff record tied to a version and evidence pack
- an SBA 7(a) public-data monitoring run kit that adapts real approved-loan
  FOIA data into model-risk monitoring cohorts while excluding fairness and
  adverse-action interpretations that the data cannot support
- a synthetic adverse-action reason accuracy benchmark that demonstrates reason
  generation, driver-to-reason mapping, reason QA, and public-data limitations
  without claiming real-world notice accuracy
- a one-folder adverse-action reason run-kit landing path that explains how to
  run, review, limit, and extend the benchmark
- release strategy documentation and versioned release notes through `v0.8.0` for stable milestone preservation
- `v0.4.1` outsider-packaging notes and reviewer entry points
- repository guardrails that check required governance artifacts and data discipline

With Phase 5 implemented, the current priority is the Phase 8 analytical-rigor
track (see `docs/system-implementation-roadmap.md`): an LDA step that searches
candidate models and a reproducible run on a recognizable public dataset, plus
drift logic and regression controls.
