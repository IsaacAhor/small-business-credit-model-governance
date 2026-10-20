# Small Business Credit Model Governance

[![CI](https://github.com/IsaacAhor/small-business-credit-model-governance/actions/workflows/ci.yml/badge.svg)](https://github.com/IsaacAhor/small-business-credit-model-governance/actions/workflows/ci.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21614944.svg)](https://doi.org/10.5281/zenodo.21614944)

Methods, monitoring protocols, documentation standards, and Python tools for
bounded reliability assessment of machine-learning-based small-business credit
underwriting systems. The core focuses are adverse-action reason accuracy and
traceability, and ongoing model-risk oversight.

The repository provides executable synthetic demonstrations and a separate
SBA public-data monitoring workflow. Current reason checks assess consistency
and traceability across supplied driver records, mappings, reasons, and notices;
they do not establish that a reason faithfully explains an underlying model.
See [known limitations](#known-limitations) before interpreting any output.

## For Reviewers

For a new review, open the [latest release](https://github.com/IsaacAhor/small-business-credit-model-governance/releases/latest)
and choose one of the three packets under **Review this release**: technical
execution, credit governance and adverse-action assessment, or methodology
and evaluation. Each packet gives its source, tasks, materials, limitations
and response format; voluntary reviewers can start without prior coordination.
The [packet overview](docs/external-review/README.md) explains the choices.
If you already started or received a packet, keep its original instructions
and software version. The general tour below does not replace that assignment.

## Start Here

Read the [project brief](PROJECT_BRIEF.md) for a short overview or
[Start Here](START_HERE.md) for a guided review path. The core components are:

| Component | What can be inspected or run | Data and boundary |
| --- | --- | --- |
| [Adverse-action reason review](docs/adverse-action-reason-run-kit/README.md) | Deterministic selection from supplied drivers, governed mappings, reason and notice QA, and traceable exceptions. | Synthetic benchmark; record consistency does not establish model-explanation faithfulness or live notice accuracy. |
| [Ongoing model-risk oversight](docs/model-risk-oversight-run-kit/README.md) | Fixed-horizon outcome construction, out-of-time performance monitoring, drift measures, and source/output fingerprints. | SBA 7(a)/504 approved-loan public data; no declined applications, adverse-action reasons, or protected-class fairness assessment. |
| [Governance and validation records](docs/model-governance-validation-run-kit/README.md) | Linked risk/materiality, explainability-method, validation, and monitoring-plan records; reviewer summaries and open findings. | Synthetic examples document review status and gaps; the records do not independently validate a model. |

Related components have narrower roles:

- [Credit-union vendor oversight](docs/credit-union-ai-vendor-risk-run-kit/README.md)
  applies linked contracts and deterministic reporting to synthetic third-party
  underwriting-tool review scenarios.
- [Fair-lending statistics](docs/fair-lending-statistics.md), BISG sensitivity
  analysis, and bounded LDA comparisons provide supporting fair-lending risk
  screening. These are not legal conclusions.
- [Recourse assessment](docs/recourse-assessment-run-kit/README.md) is an optional
  synthetic sidecar with finite action states and conservative statuses. It is
  separate from required adverse-action reasons and notices.

## What This Repository Demonstrates

A configuration-driven workflow validates structured records, computes monitoring
metrics, compares them with versioned thresholds, records exceptions and issues,
and assembles hash-verifiable evidence packs. Reason selection consumes supplied
contribution records; it does not derive or validate those contributions against
an underlying underwriting model.

Inspect the [reason benchmark pack](examples/evidence-packs/adverse-action-reason-benchmark/README.md),
[governance review pack](examples/evidence-packs/model-governance-review/README.md),
or [monthly portfolio walkthrough](examples/evidence-packs/monthly-portfolio/README.md)
without running code. The portfolio walkthrough uses 320 synthetic decisions;
the [minimal monthly demo](examples/evidence-packs/monthly-demo/README.md)
provides a smaller controlled-breach scenario.

## Who This Repository Is For

Model-risk and validation reviewers, credit policy and compliance teams,
credit-union vendor-management reviewers, and researchers evaluating governance
methods. Use [role-based use cases](USE_CASES.md) to select a path and the
[implementation guide](IMPLEMENTATION_GUIDE.md) to assess adaptation requirements.

## What This Repository Contains

The four output categories connect methods and their assumptions, monitoring
protocols, documentation standards, and portable tools. Schemas, synthetic
fixtures, scoped public-data run kits, tests, and curated outputs make the
implemented behavior inspectable. The [evidence map](docs/evidence-map.md)
describes what individual artifacts support, and the
[NIST AI RMF mapping](docs/ai-rmf-alignment.md) provides a framework-oriented view.

## What It Does Not Claim

The repository does not establish production deployment, institutional adoption
or reliance, regulatory approval, legal compliance, or independent validation.
Public availability, a release, or a reproducible run does not establish those
outcomes. Supporting screening findings are review triggers, not legal findings.
Optional recourse outputs are not applicant advice or real-world feasibility
or future-outcome guarantees.

## Known Limitations

The [v0.13.0 target disclosures](docs/external-review/targets/v0.13.0.md#disclosed-target-limitations)
record the bounded principal-driver coverage and decision-time lifecycle
corrections, regression evidence, and remaining limits. Benchmark acceptance
still measures aggregate exception-type coverage rather than per-case accuracy.
Source-archive and Windows path constraints remain. Content checks and review
exports never grant operational authorization; the larger approval system is
deferred. Historical disclosures retain their original version scope.

The [reason method and data limits](docs/adverse-action-reason-run-kit/LIMITATIONS.md)
and [terminology](docs/adverse-action-reason-run-kit/TERMINOLOGY.md) distinguish
record-level reconciliation from explanation faithfulness and legal sufficiency.
The SBA workflow covers approved loans only; its outputs cannot assess application
decisions or adverse-action reasons. Review each run kit's assumptions and limits
before adapting it or generalizing from its results.

## License and Citation

Licensed under the [Apache License 2.0](LICENSE). Citation metadata is in
[CITATION.cff](CITATION.cff). Cite the software version actually examined and
record the review-instruction revision separately.

## Project Scope

The project supports bounded assessment of adverse-action reason accuracy and
traceability and ongoing model-risk oversight for small-business underwriting.
It connects record validation, monitoring, model-change review, issue tracking,
and reviewer documentation. Supporting screening and optional recourse work
retain their separate limits.

## Core Use Cases

- Inspect the driver-to-mapping-to-reason-to-notice chain and its exceptions.
- Monitor versioned thresholds, performance, and drift within a declared dataset.
- Document risk, method assumptions, validation status, and unresolved findings.
- Review changes to model versions, thresholds, and reason-code mappings.
- Assemble evidence packs with input/output fingerprints for subsequent review.

## Scope

The core engine works with structured batch records and declared configurations.
The optional SBA adapter fits a monitoring model for approved-loan outcomes;
it is not a production underwriting model. Institution-specific data, controls,
validation, and applicability assessment remain necessary for any adaptation.

## Repository Structure

| Directory | Contents |
| --- | --- |
| `docs/` | Methods, run kits, review procedures, framework mappings, and release notes. |
| `src/` and `scripts/` | Reusable Python modules and executable workflows. |
| `schemas/` | Contracts for governance, decisions, reasons, monitoring, vendor oversight, and recourse. |
| `data/synthetic/` | Deterministic demonstration inputs and controlled scenarios. |
| `data/reference/bisg/` | Demonstration reference tables and source documentation. |
| `examples/` | Curated synthetic outputs for inspection without execution. |
| `tests/` | Contract, behavior, packaging, and workflow checks. |
| `templates/` and `governance/` | Checklists, inventory templates, control records, and validation standards. |
| `notebooks/` | Implementation notes and analytical scaffolding. |

## Working Scope Discipline

Keep adverse-action reason accuracy and traceability and ongoing model-risk
oversight central. Explainability-method governance and
supporting fair-lending risk screening must retain their stated assumptions. Broader claims require
specific evidence beyond the demonstration artifacts.

## Evidence Standard

Distinguish intended capability, demonstrated behavior, known defects, independent
evaluation, and actual use. State the property tested, version, data, conditions,
and limits. Hash agreement supports integrity under the documented normalization
policy; it does not prove substantive correctness or authenticity.

## Installation

Use Python 3.10 or later. From a Git checkout of the chosen source revision:

```bash
python -m pip install -e .
```

The core package uses the Python standard library. Install the optional data
stack only for the [SBA run kit](docs/model-risk-oversight-run-kit/README.md):

```bash
python -m pip install -e ".[public-data]"
```

See [packaging documentation](docs/packaging-and-pypi-release.md) for distribution
procedures. This source-install path does not assume a PyPI publication.

## Reproducibility

For assigned reviews, follow the packet's exact source and commands. For general
exploration, run these from the checkout root, using fresh output directories:

```bash
python scripts/validate_repository.py
python scripts/validate_phase1.py data/synthetic/monthly-demo
python scripts/run_adverse_action_reason_benchmark.py --output-dir review-output/reason-benchmark
python scripts/run_governance_review.py data/synthetic/monthly-demo review-output/governance
python scripts/run_monthly_monitoring.py data/synthetic/monthly-demo --evidence-root review-output/monitoring
```

Repository validation requires Git metadata at the current release. Keep Windows
paths short; see the [target setup notes](docs/external-review/targets/v0.13.0.md#technical-source-setup)
for archive-compatible review commands and reported environment constraints.
Preserve failed runs before retrying. The benchmark also writes scratch records
under `evidence/`; do not overwrite the curated example packs.

Installed commands include `credit-gov validate`, `credit-gov monitor`,
`credit-gov verify-evidence`, and `credit-gov change-review`. The vendor and
recourse run kits document their separate validation and report commands.
The SBA run kit documents data acquisition, permitted inputs, optional
requirements, fixture testing, and real-data execution.

Run the repository test suite when evaluating code changes:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Versioned Releases

The latest software milestone is [v0.13.0](docs/releases/v0.13.0.md).
Releases identify stable source snapshots; development commits and later review
documentation retain their own revisions. A documentation or navigation update
does not change the software version or replace an existing review target.
See the [release strategy](docs/release-strategy.md) and [release history](docs/releases/)
for earlier milestones. Use the [latest release page](https://github.com/IsaacAhor/small-business-credit-model-governance/releases/latest)
to select a new review packet.

## Data Policy

Public artifacts use synthetic, simulated, or documented public data with
appropriate provenance and permitted use. Document each source's sensitivity,
coverage, transformations, and limitations. The SBA approved-loan workflow is
separate from the synthetic adverse-action reason benchmark; it does not supply
missing application, decision-driver, or notice data.

## Near-Term Priorities

1. Extend record-level evaluation of the corrected reason controls and
   strengthen benchmark acceptance beyond aggregate type coverage.
2. Evaluate reason methods against an implemented model and a fit-for-purpose
   reference population, with explicit faithfulness and sensitivity questions.
3. Obtain scoped independent technical, practitioner, and methodology review,
   preserving the examined version, findings, and their disposition.
4. Extend monitoring regression controls and evaluate institution-specific
   adaptation only with appropriate data and documented review scope.

## Current Status

The Python workflows, linked contracts, synthetic packs, and bounded SBA adapter
are implemented. The bounded reason-content controls have regression coverage;
method-level validation and independent review remain necessary. Governance
records expose these gaps and review status rather than certify reliability.
The vendor workflow and optional recourse sidecar remain synthetic demonstrations.
