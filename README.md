# Small Business Credit Model Governance

[![CI](https://github.com/IsaacAhor/small-business-credit-model-governance/actions/workflows/ci.yml/badge.svg)](https://github.com/IsaacAhor/small-business-credit-model-governance/actions/workflows/ci.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21614944.svg)](https://doi.org/10.5281/zenodo.21614944)

This repository contains reproducible methods, monitoring protocols,
documentation standards, and portable tools for model-risk governance and
adverse-action reason accuracy and traceability in machine-learning-based small
business credit underwriting systems. Fair-lending screening is included as a
supporting risk-review module.

## For Reviewers

This repository demonstrates repeatable governance methods for
machine-learning-based small business credit underwriting systems. It shows how
a lender, validator, auditor, regulator-facing reviewer, or policy/compliance
professional could organize model and version records, risk and materiality
assessments, explainability-method documentation, validation findings,
threshold monitoring, adverse-action reason QA, change review, issue registers,
and hash-verifiable evidence packs using synthetic fixtures and clearly scoped
public-data run kits.

The core workflow generates adverse-action reasons from ranked decision
drivers, reviews their mapping and traceability, records validation independence
and promotion posture, monitors versioned thresholds, and preserves input/output
fingerprints. A portfolio-scale synthetic dataset
(`data/synthetic/monthly-portfolio`, 320 decisions) exercises the broader review
path. Supporting fair-lending modules add significance testing, BISG proxy
estimation with sensitivity analysis, and a bounded LDA comparison; see
`docs/fair-lending-statistics.md` for their methods and limitations.

## Start Here

If you are new to the repository, use these entry points:

- `START_HERE.md`
  A short review path for understanding the repository quickly.
- `USE_CASES.md`
  Role-based paths for model-risk, fair-lending, compliance, credit policy,
  credit-union vendor-risk, fintech governance, and research reviewers.
- `IMPLEMENTATION_GUIDE.md`
  A practical sequence for adapting the synthetic workflow into a governed
  monthly review pattern.
- `docs/model-governance-validation-run-kit/README.md`
  The formal risk-profile, explainability-method, validation, and monitoring
  bundle, with its deterministic reviewer summary and candid gap record.
- `examples/evidence-packs/monthly-portfolio/README.md`
  A curated portfolio-scale evidence-pack walkthrough (320 synthetic
  decisions, with statistical significance results, BISG proxy screening, and
  LDA assessment) that can be inspected without running code. A minimal
  controlled-breach pack is under `examples/evidence-packs/monthly-demo/`.
- `docs/adverse-action-reason-run-kit/README.md`
  A one-folder reviewer and operator entry point for the synthetic adverse-
  action reason accuracy benchmark, including run command, limitations,
  benchmark spec, private-data requirements, and evidence-pack review path.
- `docs/model-risk-oversight-run-kit/README.md`
  A model-risk oversight public-data run kit for SBA 7(a)/504 FOIA approved-loan
  monitoring and drift review.
- `docs/credit-union-ai-vendor-risk-run-kit/README.md`
  A credit-union AI underwriting vendor-risk profile that maps public NCUA
  risk-management themes to due diligence, monitoring, adverse-action review,
  model-change review, issue tracking, and reviewer signoff.
- `docs/ai-rmf-alignment.md`
  A practical mapping from the repository workflow to the NIST AI RMF Govern,
  Map, Measure, and Manage functions.

## What This Repository Demonstrates

The repository is meant to show practical execution, not only concept notes. It
brings together public, reviewable artifacts that support a governance workflow
for:

- model records and documentation standards
- model risk/materiality, explainability-method, validation, and monitoring-plan
  records
- threshold configuration and monitoring review
- adverse-action reason generation and reason accuracy QA
- model-change review and validation findings
- issue tracking and evidence-pack assembly
- ongoing model-risk oversight using deterministic demonstration inputs
- credit-union AI underwriting vendor-risk review, using public NCUA resources
  as source grounding for due diligence, controls, monitoring, and oversight
- supporting fair-lending screening with statistical significance testing,
  explicit inconclusive outcomes, BISG sensitivity analysis, and bounded LDA
  comparison

## Who This Repository Is For

This repository should be readable and useful to:

- legal and policy professionals reviewing the practical value of the work
- non-technical reviewers who need a plain-language view of what the system does
- policy, compliance, fair-lending, validation, and model-risk professionals
- credit-union vendor-management and member-business lending reviewers
- potential adopters evaluating how a governance workflow could be structured
- researchers or practitioners assessing governance methods using synthetic data

## What This Repository Contains

The repository is designed to support several connected outputs:

- a framework for governing ML-based small business underwriting systems
- monitoring checklists for explainability, fair lending, and model-risk oversight
- implementation-oriented system designs, workflows, and templates
- practitioner-facing written work that translates the framework into usable methods
- a credit-union AI vendor-risk run kit that adapts the workflow to
  third-party underwriting-tool review, with executable linked contracts,
  evidence validation, synthetic scenarios, and deterministic reviewer outputs
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

## Project Scope

This project provides a reproducible governance evidence engine for
machine-learning-based small business credit underwriting systems. It focuses on
structured model-risk and validation records, monitoring workflows,
adverse-action reason accuracy and traceability review, model-change review,
reviewer-ready output packages, and supporting fair-lending screening triggers.

The repository is organized as a standalone technical project with public,
reviewable artifacts: schemas, templates, synthetic fixtures, public-data run
kits, tests, and configuration-driven workflow code.

## Core Use Cases

- monthly monitoring runs that compute metrics, identify threshold breaches, and
  generate evidence packs
- formal model-risk, explainability-method, validation, and monitoring-plan
  records with cross-file relationship checks
- adverse-action reason review that tests mapping quality, specificity, and
  traceability
- change-review workflows for model versions, thresholds, and reason-code
  mappings
- reviewer-preparation summaries that surface independence gaps, open findings,
  method limitations, and promotion posture without claiming validation
- AI vendor due-diligence and monitoring review for credit-union
  small-business or member-business underwriting workflows
- supporting fair-lending screening that flags disparity indicators for
  governance review

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
  Framework, run-kit, source-mapping, and article planning documents.
- `docs/releases/`
  Release notes for stable public milestones.
- `START_HERE.md`, `USE_CASES.md`, and `IMPLEMENTATION_GUIDE.md`
  Reviewer and adopter entry points.
- `schemas/`
  JSON contracts for core evidence records and the optional formal governance
  bundle, plus the separate vendor-model oversight bundle.
- `notebooks/`
  Implementation notes and future analytical notebooks.
- `src/`
  Reusable contract validation, governance-review, monitoring,
  reason-generation, model-change validation, vendor-risk validation and
  reporting, and supporting LDA assessment code.
- `data/synthetic/`
  Deterministic demonstration inputs for validation, monitoring,
  portfolio-scale workflow runs, and vendor-risk scenarios.
- `data/reference/bisg/`
  Demonstration BISG reference tables with a documented path to full Census-derived data.
- `examples/`
  Curated synthetic example outputs that can be reviewed without running code.
- `tests/`
  Validation checks for schemas, typed models, governance relationships,
  deterministic reports, synthetic-data integrity, monitoring, reason QA,
  reason generation, model-change validation, vendor oversight, and supporting
  screening modules.
- `templates/`
  Checklists and governance templates.
- `governance/`
  Control records, inventory templates, validation standards, and change logs.

## Initial Deliverables

The first phase of this repository is structured around six deliverables:

1. A flagship framework for model governance and fair-lending monitoring.
2. A practitioner-facing article aligned to the repository scope.
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

## Installation

Install from source while working in this repository:

```bash
python -m pip install -e .
```

After PyPI publication, install the released package:

```bash
python -m pip install credit-gov
```

The installed package exposes console commands for the core workflows:

```bash
credit-gov-validate data/synthetic/monthly-demo
credit-gov monitor data/synthetic/monthly-demo --evidence-root evidence
credit-gov verify-evidence evidence/<generated-evidence-pack-directory>
credit-gov change-review data/synthetic/monthly-portfolio
credit-gov vendor-validate data/synthetic/credit-union-vendor-risk/baseline-complete data/synthetic/monthly-demo
credit-gov vendor-report data/synthetic/credit-union-vendor-risk/baseline-complete data/synthetic/monthly-demo vendor-review-output
```

For the SBA public-data run kit, install the optional public-data stack:

```bash
python -m pip install -e ".[public-data]"
credit-gov-make-sba-fixture --rows 4000 --out data/sba-7a-504-FIXTURE-synthetic.csv
credit-gov-sba-to-monitoring --input data/sba-7a-504-FIXTURE-synthetic.csv --program all
```

See `docs/packaging-and-pypi-release.md` for TestPyPI, PyPI, and preservation
steps. Package distribution is a reproducibility and dissemination artifact;
it is not evidence of adoption, deployment, legal compliance, regulatory
approval, or independent validation by itself.

## Reproducibility

Run Phase 1 data-contract validation:

```bash
python scripts/validate_phase1.py
```

Generate the deterministic formal governance review summary:

```bash
python scripts/run_governance_review.py data/synthetic/monthly-demo review-output
```

Validate and report the synthetic vendor-model oversight bundle:

```bash
python scripts/validate_vendor_risk_run_kit.py data/synthetic/credit-union-vendor-risk/baseline-complete data/synthetic/monthly-demo
python scripts/build_vendor_risk_evidence_pack.py data/synthetic/credit-union-vendor-risk/baseline-complete data/synthetic/monthly-demo vendor-review-output
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

The latest documented milestone is `v0.11.0`. It adds a formal governance-
validation bundle and an executable vendor-model oversight workflow with linked
records, evidence checks, synthetic scenarios, deterministic reviewer reports,
and installed package commands. The prior `v0.10.0` milestone repaired the SBA
public-data adapter against the current official file layout and added fixed-
horizon outcome construction, explicit censoring and row dispositions, pre-
monitoring model development, out-of-time performance review, drift measures,
source and output hashes, and validated not-applicable module states. The prior
`v0.9.4` milestone ensures that the evidence-pack
verifier recognizes the explanatory README in each curated example pack while
continuing to reject every other undeclared file. It also adds verification
coverage for every checked-in pack. The prior `v0.9.3` milestone added
configured minimum-group-size and statistical-significance gates to rate-screen
escalations, explicit inconclusive results, and CI coverage for the published
evidence-verification commands. These are public technical and documentation
milestones, not proof of adoption, deployment, legal compliance, regulatory
approval, field recognition, or external validation.

The prior release, `v0.9.0`, makes the project a modern installable Python
package with `pyproject.toml`, packaged schema/reference resources, console
entry points, wheel-build CI checks, and a PyPI release guide. It is a
distribution and reproducibility milestone, not proof of adoption, deployment,
legal compliance, regulatory approval, field recognition, or external
validation. The prior release, `v0.8.0`, adds the synthetic adverse-action
reason accuracy and transparency benchmark. The benchmark is a public,
on-domain synthetic run kit for reason generation, driver-to-reason mapping,
reason QA, and
evidence-pack review under Regulation B 12 CFR 1002.9. It is not public proof
of live small-business notice accuracy, lender adoption, deployment, legal
compliance, or regulatory approval. The prior release, `v0.7.0`, adds the
model-risk oversight public-data run kit:
an adapter for real SBA 7(a)/504 FOIA loan-level data, a synthetic schema
fixture for pipeline validation, reproducibility documentation, and
scope/limitations notes. The run kit is designed to exercise model-risk
monitoring and drift reporting on real approved-loan public data. The current
adapter uses fixed-horizon charge-off labels, a pre-monitoring development
split, out-of-time scoring, source and output hashes, row-disposition counts,
and explicit not-applicable module states; it is not an
underwriting model, fairness analysis, adverse-action analysis, deployment
claim, or legal conclusion. The prior substantive analytical milestone,
`v0.6.0`, adds statistical significance testing for fair-lending screens and
optional BISG proxy monitoring on the portfolio-scale synthetic dataset. The
current main branch extends that BISG path with a bounded measurement-error
sensitivity gate for proxy-bias review.

See `docs/release-strategy.md`, `docs/releases/v0.4.0.md`,
`docs/releases/v0.4.1.md`, `docs/releases/v0.5.0.md`,
`docs/releases/v0.6.0.md`, `docs/releases/v0.6.1.md`,
`docs/releases/v0.6.2.md`, `docs/releases/v0.6.3.md`,
`docs/releases/v0.7.0.md`, `docs/releases/v0.8.0.md`,
`docs/releases/v0.9.0.md`, `docs/releases/v0.9.1.md`,
`docs/releases/v0.9.2.md`, `docs/releases/v0.9.3.md`,
`docs/releases/v0.9.4.md`, `docs/releases/v0.10.0.md`, and
`docs/releases/v0.11.0.md`.

## Data Policy

Public artifacts should use synthetic, simulated, or clearly licensed
demonstration data unless a dataset is approved and documented. Data-like files
must not be added casually. Any future non-synthetic data source should have a
documented provenance, permitted use, sensitivity classification, and reviewer.

## Near-Term Priorities

1. Obtain an independent model-risk or lending-practitioner review of a tagged
   governance bundle and preserve the review scope, identity, findings, and
   disposition.
2. Exercise the explainability-method contract against an implemented model and
   fit-for-purpose reference population, including directionality, correlation,
   reproducibility, and outcome-analysis evidence.
3. Extend monitoring regression controls beyond the implemented public-data
   drift and out-of-time performance path, while preserving version and
   evidence hashes.
4. Exercise the vendor-oversight contracts with permissioned evidence in an
   institution-controlled environment and calibrate the configurable review
   inputs to that actual use case.
5. Keep the fair-lending/LDA track as a supporting risk-screening module and add
   rigor only where data, current law, and review scope support it.

The formal governance plumbing is now implemented. The largest remaining gap is
external validation, which code, synthetic fixtures, and self-authored reports
cannot supply.

## Current Status

This repository now contains:

- a first full framework draft
- practitioner-facing article drafts and archived working drafts
- synthetic monitoring demonstration assets
- reusable monitoring and governance templates
- Phase 0 system design documents for a governance evidence engine
- Phase 1 JSON schemas, typed validation models, deterministic synthetic demo records, and validation tests
- Phase 1A cross-file evidence-integrity validation for the synthetic demo records
- an optional formal governance bundle covering risk/materiality,
  explainability-method assumptions, validation independence/findings, and a
  linked monitoring plan, plus deterministic hash-verifiable review outputs
- a Phase 2 one-command synthetic monthly monitoring workflow that emits metrics, breaches, issues, and reviewer-ready evidence packs
- a Phase 3 adverse-action reason QA workflow that checks generated reason outputs, records traceable exceptions, and adds reason QA reports to evidence packs
- a Phase 4 fair-lending screening workflow that applies configured comparison groups, creates escalation findings, and adds reviewer notes to evidence packs
- a Phase 3B adverse-action reason-generation workflow with deterministic regeneration checks
- a Phase 4B less-discriminatory-alternative assessment workflow integrated into optional monitoring evidence outputs
- a portfolio-scale synthetic monthly dataset that exercises reason generation, reason QA, fair-lending screening, and LDA assessment
- a Phase 5 model-change and validation-review workflow that compares prior and current model-version, threshold-set, and reason-code mapping records, summarizes change impact, and emits a reviewer signoff record tied to a version and evidence pack
- a model-risk oversight public-data run kit that adapts real approved-loan
  FOIA data into fixed-horizon model-risk monitoring cohorts, records source
  provenance and row dispositions, scores monitoring periods out of time, and
  marks decision-rate, override, reason, and fair-lending modules not applicable
- a synthetic adverse-action reason accuracy benchmark that demonstrates reason
  generation, driver-to-reason mapping, reason QA, and public-data limitations
  without claiming real-world notice accuracy
- a one-folder adverse-action reason run-kit landing path that explains how to
  run, review, limit, and extend the benchmark
- a credit-union AI vendor-risk run kit that maps public NCUA resource themes to
  underwriting vendor due diligence, monitoring, adverse-action reason review,
  model-change review, issue tracking, and reviewer signoff, now paired with an
  executable synthetic vendor-oversight workflow
- release strategy documentation and versioned release notes through `v0.11.0` for stable milestone preservation
- `v0.4.1` outsider-packaging notes and reviewer entry points
- repository guardrails that check required governance artifacts and data discipline

The current priority is independent review and method-level validation of the
core governance and adverse-action reason path. Executable vendor oversight is
implemented but remains synthetic and externally unvalidated. Additional
monitoring regression controls follow. Fair-lending and LDA remain supporting
risk-screening work rather than the repository's headline.
