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
`examples/evidence-packs/monthly-portfolio/` (portfolio scale) and
`examples/evidence-packs/monthly-demo/` (minimal controlled scenario).

## 6. Review Findings And Escalations

The output should be reviewed as governance evidence, not as an automatic
compliance decision.

Reviewers should ask:

- Which thresholds were breached?
- Which fair-lending screening triggers fired?
- Are adverse-action reason outputs complete, mapped, and specific enough for
  review?
- Which findings require deeper review, remediation, or accepted-risk approval?
- If LDA inputs are present, did the alternative assessment identify only a
  governance review trigger rather than a legal conclusion or adoption mandate?
- Are limitations and synthetic-data assumptions clearly disclosed?

## 7. Review Model Changes Before Promotion

When a model version changes, compare the prior governed records against the new
ones before promoting the new version. The Phase 5 change-validation workflow
runs automatically inside monitoring when the dataset contains a
`prior-model-version-record.json` snapshot, and it is also available standalone:

```bash
python scripts/run_change_validation.py data/synthetic/monthly-portfolio
```

It produces `model_change_validation_results.json` and
`model_change_validation_report.md` covering:

- model-version field changes, including expanded assumptions or limitations
- threshold-set changes, read as tightened or loosened where the comparison rule
  is unchanged, plus added and removed thresholds
- reason-code mapping changes, separating a structural text or driver change from
  a mapping-version bump
- a change-impact summary and the review actions required before promotion
- a reviewer signoff record tied to the specific version and evidence-pack run

Treat a material change as a trigger to document rationale and obtain independent
validation signoff, not as a determination that a change is compliant.

## 8. Apply The Credit-Union Vendor-Risk Profile When Relevant

When the governed model or decision system is provided by an AI vendor to a
credit union for small-business or member-business underwriting, review the
credit-union-specific profile:

- `docs/credit-union-ai-vendor-risk-run-kit/README.md`
- `docs/credit-union-ai-vendor-risk-run-kit/DUE_DILIGENCE.md`
- `docs/credit-union-ai-vendor-risk-run-kit/MONITORING_PROTOCOL.md`
- `docs/credit-union-ai-vendor-risk-run-kit/ADVERSE_ACTION_REVIEW.md`
- `docs/credit-union-ai-vendor-risk-run-kit/LIMITATIONS.md`

Validate the linked synthetic vendor records and generate the reviewer output:

```bash
python scripts/validate_vendor_risk_run_kit.py \
  data/synthetic/credit-union-vendor-risk/baseline-complete \
  data/synthetic/monthly-demo
python scripts/build_vendor_risk_evidence_pack.py \
  data/synthetic/credit-union-vendor-risk/baseline-complete \
  data/synthetic/monthly-demo \
  vendor-review-output
```

The executable profile does not add a new compliance claim. It records linked
vendor components, limitations, evidence, monitoring, events, notice controls,
and signoff state; validates their relationships; and packages visible gaps for
third-party underwriting-tool due diligence and ongoing vendor oversight.

## 9. Record Follow-Up

The current public workflow creates issue, change-validation, and signoff
artifacts to demonstrate the control pattern. A production adaptation would need
institution-specific owners, evidence retention rules, legal review, validation
standards, and a formal approval workflow.

The next priority is independent practitioner review of one exact tagged
artifact, followed by method-level testing and additional monitoring regression
controls. Fair-lending and LDA work remains supporting and should not displace
review of the core governance, adverse-action reason, and vendor-oversight path.
