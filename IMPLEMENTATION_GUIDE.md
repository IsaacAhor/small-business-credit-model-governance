# Implementation Guide

This guide explains how an outside reviewer or potential adopter can use the
repository as a reference workflow for monthly governance review of an
ML-assisted small business credit underwriting system.

## 1. Define The Governed Model Context

Start by documenting the model, version, purpose, decision stage, owner, and
review boundaries.

Relevant artifacts:

- `governance/model-inventory-template.md`
- `schemas/model-registry-record.schema.json`
- `schemas/model-version-record.schema.json`
- `data/synthetic/monthly-demo/model-registry-record.json`
- `data/synthetic/monthly-demo/model-version-record.json`

The goal is not to prove a model is compliant. The goal is to make the model
context reviewable before monitoring outputs are interpreted.

## 2. Configure Thresholds And Review Rules

Define the monitoring thresholds, reason-code mappings, and fair-lending
screening configuration before running a review.

Relevant artifacts:

- `schemas/threshold-set.schema.json`
- `schemas/reason-code-mapping.schema.json`
- `schemas/fair-lending-screening-config.schema.json`
- `data/synthetic/monthly-demo/threshold-set.json`
- `data/synthetic/monthly-demo/reason-code-mappings.json`
- `data/synthetic/monthly-demo/fair-lending-screening-config.json`

This makes the review process auditable because findings can be traced back to
predefined rules rather than post hoc judgment.

## 3. Prepare Review Inputs

A monthly review run needs structured decision, score, reason, override, and
outcome records.

Relevant artifacts:

- `schemas/application-decision-record.schema.json`
- `schemas/score-output.schema.json`
- `schemas/adverse-action-reason-output.schema.json`
- `schemas/override-event.schema.json`
- `schemas/outcome-record.schema.json`
- `data/synthetic/monthly-demo/`

Public examples use synthetic data only. A real institution would need approved
data provenance, permitted-use review, sensitivity classification, and access
controls before applying this pattern to production or restricted records.

## 4. Validate The Inputs

Run the repository guardrails and Phase 1 validation before generating an
evidence pack:

```bash
python scripts/validate_repository.py
python scripts/validate_phase1.py
```

These checks validate required repository artifacts, markdown links, synthetic
data discipline, schema conformance, and cross-file relationships.

## 5. Generate A Monthly Evidence Pack

Run the synthetic monitoring workflow:

```bash
python scripts/run_monthly_monitoring.py data/synthetic/monthly-demo --evidence-root evidence
```

The workflow generates reviewer-ready outputs such as:

- `manifest.json`
- `config_snapshot.json`
- `input_fingerprints.json`
- `metric_results.json`
- `breach_register.json`
- `reason_qa_results.json`
- `fair_lending_screening_results.json`
- `fair_lending_escalation_register.json`
- `issue_register.json`
- `monitoring_report.md`
- `reviewer_notes.md`
- `reviewer_signoff.md`

Curated example outputs are available under
`examples/evidence-packs/monthly-demo/`.

## 6. Review Findings And Escalations

The output should be reviewed as governance evidence, not as an automatic
compliance decision.

Reviewers should ask:

- Which thresholds were breached?
- Which fair-lending screening triggers fired?
- Are adverse-action reason outputs complete, mapped, and specific enough for
  review?
- Which findings require deeper review, remediation, or accepted-risk approval?
- Are limitations and synthetic-data assumptions clearly disclosed?

## 7. Record Follow-Up

The current public workflow creates issue and signoff artifacts to demonstrate
the control pattern. A production adaptation would need institution-specific
owners, evidence retention rules, legal review, validation standards, and formal
approval workflow.

The next planned milestone is to strengthen model-change review, validation
summaries, and reviewer signoff depth.
