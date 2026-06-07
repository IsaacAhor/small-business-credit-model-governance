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

Next pending task:

- implement the first one-command monitoring workflow that consumes the Phase 1
  validated synthetic inputs and emits metrics, breaches, and an evidence pack

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

## Phase 4: Fair-Lending Screening and Escalation

Deliverables:

- configurable comparison groups
- approval-rate and ratio screens
- override-rate and reason-code concentration screens
- escalation rules
- issue record generation
- reviewer notes template

Acceptance criteria:

- screening metrics are configuration-driven
- breach records identify the crossed threshold
- outputs avoid unsupported legal conclusions
- issue records include severity, owner, status, and due date

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

## Evidence Pack Standard

Every executable run should create a timestamped evidence folder containing:

- `manifest.json`
- `config_snapshot.json`
- `input_fingerprints.json`
- `model_record.json`
- `threshold_set.json`
- `metric_results.json`
- `breach_register.json`
- `issue_register.json`
- `monitoring_report.md`
- `reviewer_signoff.md`

## First Build Target

The first serious build target is:

> A one-command monthly monitoring run that validates synthetic data, computes
> configured monitoring metrics, identifies threshold breaches, and emits a
> reviewer-ready evidence pack.
