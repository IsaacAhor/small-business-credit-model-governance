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

Acceptance criteria:

- changes produce a clear impact summary
- validation reports reference assumptions, metrics, breaches, and limitations
- signoff records are tied to a specific model version and evidence pack

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
- `v0.5.0`: Phase 5 model-change and validation-review workflow.

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
