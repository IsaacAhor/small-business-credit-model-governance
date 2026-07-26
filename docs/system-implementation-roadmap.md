# System Implementation Roadmap

## Purpose

This roadmap defines the next implementation stage for the repository. The goal
is to evolve from framework documents and starter templates into a repeatable
credit model governance evidence engine for small business underwriting models.

The system should support model risk, compliance, validation, and governance
review. It should not claim to provide legal advice, production underwriting, or
automatic regulatory compliance.

## Target System

The target system is a batch, configuration-driven Python workflow that:

- validates structured model governance inputs
- runs monitoring and reason-code quality checks
- compares results against configured thresholds
- records breaches and issues
- generates reviewer-ready evidence packs

## Design Anchors

The implementation should align with recognized financial-institution control
concepts:

- model inventory
- model versioning
- effective challenge
- outcomes analysis
- ongoing monitoring
- change management
- issue and remediation tracking
- adverse-action reason review
- fair-lending screening
- vendor model oversight

## Phase 0: System Design

Deliverables:

- `docs/system-charter.md`
- `docs/system-boundaries.md`
- `docs/control-workflow.md`
- `docs/domain-object-model.md`

Acceptance criteria:

- the system problem is defined clearly
- users and roles are documented
- non-objectives are explicit
- the evidence-pack workflow is understandable before code is written

## Phase 1: Data Contracts

Deliverables:

- JSON schemas under `schemas/`
- typed validation models under `src/credit_gov/schemas/`
- deterministic synthetic demo inputs under `data/synthetic/`
- schema validation tests

Status:

- Phase 1 is now implemented with JSON schemas under `schemas/`, typed validation
  models under `src/credit_gov/schemas/`, deterministic synthetic demo inputs
  under `data/synthetic/monthly-demo/`, and command-line validation through
  `python scripts/validate_phase1.py`.

Initial contracts:

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

Acceptance criteria:

- demo records can be validated from the command line
- invalid records produce specific validation errors
- synthetic data status is disclosed
- underwriting fields are separated from monitoring-only fields

## Phase 1A: Evidence Integrity Hardening

Deliverables:

- cross-file validation for decision IDs, model IDs, version IDs, run IDs, threshold metrics, breach records, and manifest references
- invalid relationship tests for broken references and mismatched relationships
- tests for relationship validation and CLI failure behavior

Status:

- Phase 1A is implemented with cross-file relationship checks in the Phase 1 validator and tests for broken decision references, mismatched version context, invalid breach metrics, missing manifest references, and CLI failure behavior.

Acceptance criteria:

- score, override, and outcome records reference existing decision records
- threshold, breach, reason-code, manifest, model, and version records agree on model/version/run context where applicable
- breach metrics are present in the configured threshold set
- manifest input references point to files present in the dataset
- invalid relationship scenarios fail with specific errors

## Phase 2: Monthly Monitoring Workflow

Deliverables:

- CLI command for a demo monitoring run
- metric computation module
- threshold comparison module
- breach register output
- timestamped evidence pack folder
- Markdown monitoring report
- unit tests for metric logic

Status:

- Phase 2 is now implemented with a one-command workflow in
  `scripts/run_monthly_monitoring.py`, deterministic metric computation and
  threshold evaluation in `src/credit_gov/monitoring.py`, reviewer-ready
  evidence-pack generation under `evidence/`, and tests covering controlled-
  breach and no-breach scenarios.

Initial metrics:

- approval rate
- decline rate
- score distribution
- override rate
- manual review rate
- reason-code distribution
- population or feature drift
- configured fair-lending screening indicators

Acceptance criteria:

- one command creates a complete evidence pack
- outputs are deterministic for the same inputs
- at least one demo scenario generates no breach
- at least one demo scenario generates controlled breaches

## Phase 3: Adverse-Action Reason QA

Deliverables:

- reason-code mapping schema
- reason-code QA checks
- reason-code stability report
- traceable exception samples
- report section in the evidence pack

Status:

- Phase 3 is now implemented with an adverse-action reason output schema,
  typed validation model, relationship validation, reason QA checks for missing,
  unmapped, generic, driver-mismatched, and mapping-version-mismatched reason
  outputs, evidence-pack reason QA outputs, and tests for clean and exception
  scenarios.

Checks:

- missing reason code
- unmapped reason code
- generic reason text
- reason code not tied to configured decision driver
- reason-code distribution shift after model or threshold change

Acceptance criteria:

- reason exceptions are traceable to source decision records
- reason mapping versions are recorded
- reports distinguish QA exceptions from legal conclusions

## Phase 3B: Adverse-Action Reason Generation

Deliverables:

- reason-generation module that derives adverse-action reasons from ranked,
  per-decision driver contributions and the governed reason-code mapping
- generation CLI with a `--check` drift mode
- provenance summary of declined decisions with and without generated reasons

Status:

- Phase 3B is implemented in `src/credit_gov/generation.py` and
  `scripts/generate_adverse_action_reasons.py`. Reasons are generated only for
  declined decisions, ranked by contribution magnitude, and mapped to governed
  reason codes. Generation is deliberately separate from the Phase 3 reason QA,
  which then reviews the generated output. The portfolio dataset's shipped
  reasons are provably regenerable (`--check`).

Acceptance criteria:

- generation is deterministic and reproducible from inputs
- reasons are produced only for declined decisions and mapped to governed codes
- a declined decision with no mapped driver produces no reason, which reason QA
  surfaces as a missing-reason exception

## Phase 3C: Adverse-Action Reason Accuracy Benchmark

Deliverables:

- synthetic adverse-action reason benchmark dataset
- benchmark runner that reuses monthly monitoring and adds benchmark-specific
  reason accuracy checks
- curated example evidence pack
- method, public-data limitation, and private-data specification notes

Status:

- Phase 3C is implemented as the `v0.8.0` synthetic adverse-action reason
  accuracy milestone. It demonstrates public, on-domain reason generation,
  driver-to-reason mapping, reason QA, supplemental benchmark exception checks,
  and evidence-pack review without claiming real-world notice accuracy or legal
  compliance.

Acceptance criteria:

- expected seeded reason QA failures are observed
- benchmark outputs remain synthetic and non-legal-conclusion labeled
- public-data limitations are documented before any public proxy is introduced
- private-data requirements are explicit for future real-world validation

## Phase 4: Fair-Lending Screening and Escalation

Deliverables:

- configurable comparison groups
- approval-rate and ratio screens
- override-rate and reason-code concentration screens
- escalation rules
- issue record generation
- reviewer notes template

Status:

- Phase 4 is now implemented with configurable comparison groups, approval-rate
  ratio screens, override-rate difference screens, reason-code concentration
  screens, escalation findings, issue records, reviewer notes, evidence-pack
  fair-lending outputs, and tests for triggered and clean scenarios.

Acceptance criteria:

- screening metrics are configuration-driven
- breach records identify the crossed threshold
- outputs avoid unsupported legal conclusions
- issue records include severity, owner, status, and due date

## Phase 4B: Less-Discriminatory-Alternative (LDA) Assessment

Deliverables:

- LDA assessment module comparing a baseline model to a candidate alternative
  on the same synthetic population
- predictive-separation and group-disparity metrics per model
- qualifying-alternative decision rule with a documented governance recommendation
- optional integration into the monitoring evidence pack and a standalone CLI

Status:

- Phase 4B is implemented in `src/credit_gov/lda.py`,
  `scripts/run_lda_assessment.py`, and an optional hook in the monitoring
  workflow. When `lda-assessment-config.json` and
  `alternative-model-decisions.json` are present, the run emits
  `lda_assessment_results.json` and a report section. A candidate qualifies when
  it reduces group approval-rate disparity by at least a configured margin while
  holding predictive separation within tolerance.

Acceptance criteria:

- assessment is deterministic and synthetic, with explicit non-legal-conclusion framing
- a qualifying alternative is a documented review trigger, not a mandate
- datasets without LDA inputs run unchanged

## Phase 5: Change and Validation Review

Deliverables:

- model-version comparison workflow
- threshold-set comparison workflow
- reason-code mapping comparison workflow
- validation summary report
- reviewer signoff artifact

Status:

- Phase 5 is implemented in `src/credit_gov/validation.py`,
  `scripts/run_change_validation.py`, and an optional hook in the monitoring
  workflow. When `prior-model-version-record.json` is present, the run compares
  the prior model-version, threshold-set, and reason-code mapping records to the
  current dataset records, emits `model_change_validation_results.json` and
  `model_change_validation_report.md`, adds a report section, and writes a
  reviewer signoff record tied to the current version and evidence-pack run. The
  threshold diff reads value changes as tightened or loosened where the
  comparison rule is unchanged; the reason-code diff separates a structural
  text/driver change from a mapping-version bump. Prior threshold and reason-code
  snapshots are each optional within the review. Datasets without Phase 5 inputs
  run unchanged.

Acceptance criteria:

- changes produce a clear impact summary
- validation reports reference assumptions, metrics, breaches, and limitations
- signoff records are tied to a specific model version and evidence pack

Open follow-ups (not blocking Phase 5):

- drift logic and regression controls (tracked under the Phase 8 rigor track)
- external practitioner review of the change-review outputs

## Phase 6: Vendor Model Oversight

Deliverables:

- vendor model metadata fields
- opaque-score limitation fields
- challenger or benchmark comparison hooks
- heightened monitoring configuration
- vendor oversight report section

Acceptance criteria:

- third-party model components can be recorded without overstating transparency
- limitations are documented separately from internal validation gaps
- vendor oversight outputs map to model risk governance concepts

## Target Repository Shape

```text
src/credit_gov/
  registry/
  monitoring/
  validation/
  reasons/
  fairness/
  drift/
  governance/
  reporting/
  schemas/
  cli.py

schemas/
configs/
data/synthetic/
examples/
evidence/
tests/
docs/
```

## Release Milestones

Stable public milestones should be tagged as versioned releases once the
corresponding phase is implemented, documented, and validated through the normal
repository workflow.

- `v0.4.0`: Phase 4 fair-lending screening demo and reviewer-facing evidence
  package.
- `v0.4.1`: outsider packaging patch with reviewer and implementation guides.
- `v0.5.0`: Phase 3B adverse-action reason generation, Phase 4B LDA
  assessment, and portfolio-scale synthetic dataset.
- `v0.6.0`: Phase 8 statistical significance testing and BISG proxy
  monitoring on the portfolio-scale synthetic dataset; current main extends
  that path with measurement-error sensitivity gates.
- `v0.7.0`: model-risk oversight public-data run kit for model-risk monitoring
  and drift reporting on real approved-loan FOIA data.
- `v0.8.0`: synthetic adverse-action reason accuracy benchmark and evidence pack.

## Evidence Pack Standard

Every executable run should create a timestamped evidence folder containing:

- `manifest.json`
- `config_snapshot.json`
- `input_fingerprints.json`
- `model_record.json`
- `threshold_set.json`
- `metric_results.json`
- `breach_register.json`
- `reason_qa_results.json`
- `reason_stability_report.json`
- `fair_lending_screening_results.json`
- `fair_lending_escalation_register.json`
- `issue_register.json`
- `monitoring_report.md`
- `reviewer_notes.md`
- `reviewer_signoff.md`

## First Build Target

The first serious build target is:

> A one-command monthly monitoring run that validates synthetic data, computes
> configured monitoring metrics, identifies threshold breaches, and emits a
> reviewer-ready evidence pack.

## Phase 8: Analytical Rigor and External Corroboration

Priority track ahead of the remaining Phase 5 to 7 items. Raises analytical
rigor rather than building production infrastructure.

The remaining deliverables converge on a single build: a reproducible run
on recognizable public data that trains a simple, interpretable reference
model. That one artifact simultaneously supplies a real model for the
workflow to govern, real driver contributions for reason generation, real
geography for full Census-derived BISG tables, a real basis for regression
controls, and the candidate space for the LDA search.

Deliverables:

- protected-class proxy estimation (e.g., BISG) for fair-lending screening
  (initial implementation shipped in v0.6.0; measurement-error sensitivity
  gates now ship on main; full Census-derived reference tables arrive with the
  public-data run)
- statistical significance testing (shipped in v0.6.0) and regression
  controlling for legitimate credit factors
- an LDA step that searches candidate models and documents the
  performance-versus-disparity tradeoff
- a run on a recognizable public dataset alongside the synthetic data,
  including a simple interpretable reference model trained on that data

Acceptance criteria:

- fair-lending outputs report a proxy method, an effect size, and a significance
  result, not only a raw approval-rate ratio
- the LDA output shows more than one generated candidate and a documented
  tradeoff, with explicit synthetic and non-legal-conclusion framing
- the public-dataset run is reproducible and separated from the synthetic demo
- framing stays state-law and risk-management oriented, not federal
  disparate-impact compliance

Status:

- BISG proxy estimation, posterior-predictive bootstrap inference, and
  measurement-error sensitivity gates shipped in `src/credit_gov/bisg.py` and
  `src/credit_gov/stats.py`, wired into the monitoring run and evidence pack
  (see `docs/fair-lending-statistics.md`)
- LDA candidate search and the public-dataset run remain open
