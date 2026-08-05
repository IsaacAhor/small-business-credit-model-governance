# Use Cases

This file explains how different outside reviewers or potential adopters can use
the repository without needing to understand every implementation detail first.

## Model-Risk or Validation Reviewer

Use the repository to inspect how a model governance workflow can organize
model records, version context, thresholds, monitoring outputs, breaches, issues,
and reviewer-ready evidence packs.

Start with:

- `docs/system-charter.md`
- `docs/system-boundaries.md`
- `docs/domain-object-model.md`
- `examples/evidence-packs/monthly-portfolio/monitoring_report.md`
- `examples/evidence-packs/monthly-portfolio/reviewer_signoff.md`

What to evaluate:

- whether the model/version/run relationships are traceable
- whether monitoring thresholds are explicit
- whether breaches and issues are linked to reviewer action
- whether limitations are documented separately from findings

## Fair-Lending or Compliance Reviewer

Use the repository to inspect how fair-lending screening can be treated as a
governed review trigger rather than an unsupported legal conclusion.

Start with:

- `docs/adverse-action-reason-run-kit/README.md`
- `docs/adverse-action-reason-run-kit/METHOD.md`
- `docs/adverse-action-reason-run-kit/PUBLIC_DATA_LIMITS.md`
- `examples/evidence-packs/adverse-action-reason-benchmark/README.md`
- `templates/fair-lending-monitoring-checklist.md`
- `schemas/fair-lending-screening-config.schema.json`
- `examples/evidence-packs/monthly-portfolio/fair_lending_screening_results.json`
- `examples/evidence-packs/monthly-portfolio/fair_lending_escalation_register.json`
- `examples/evidence-packs/monthly-portfolio/reviewer_notes.md`

What to evaluate:

- whether comparison groups and thresholds are configured before review
- whether adverse-action reason outputs are traceable to governed mappings
- whether public-data limits are stated without overclaiming
- whether outputs distinguish screening findings from legal conclusions
- whether escalations are assigned an owner, severity, status, and due date
- whether recurring findings could be routed to deeper review

## Credit Policy or Underwriting Governance Lead

Use the repository to understand how underwriting governance can connect model
configuration, threshold review, overrides, reason-code mappings, and issue
tracking.

Start with:

- `governance/model-inventory-template.md`
- `governance/control-matrix.md`
- `templates/model-governance-checklist.md`
- `examples/evidence-packs/monthly-portfolio/threshold_set.json`
- `examples/evidence-packs/monthly-portfolio/issue_register.json`
- `examples/evidence-packs/adverse-action-reason-benchmark/reason_qa_results.json`

What to evaluate:

- whether policy thresholds are visible and reviewable
- whether overrides and manual-review activity are monitored
- whether reason-code mappings are tied to governed records
- whether issues are traceable to specific monitoring outputs

## Fintech Governance or Product Risk Lead

Use the repository as a reference structure for a lightweight governance evidence
workflow that can sit around an underwriting model or decision system.

Start with:

- `IMPLEMENTATION_GUIDE.md`
- `docs/control-workflow.md`
- `schemas/README.md`
- `data/synthetic/monthly-demo/README.md`
- `examples/evidence-packs/monthly-portfolio/README.md`

What to evaluate:

- what minimum governance records would need to exist before monitoring
- what can be automated in a batch workflow
- what should remain subject to human review
- where institution-specific policy, legal review, and validation judgment are
  still required

## Credit-Union Vendor-Management or CUSO Reviewer

Use the repository to inspect how a credit union could organize due diligence,
monitoring, adverse-action review, model-change review, and issue escalation
for an AI-enabled third-party small-business or member-business underwriting
tool.

Start with:

- `docs/credit-union-ai-vendor-risk-run-kit/README.md`
- `docs/credit-union-ai-vendor-risk-run-kit/DUE_DILIGENCE.md`
- `docs/credit-union-ai-vendor-risk-run-kit/MONITORING_PROTOCOL.md`
- `docs/credit-union-ai-vendor-risk-run-kit/ADVERSE_ACTION_REVIEW.md`
- `docs/credit-union-ai-vendor-risk-run-kit/LIMITATIONS.md`
- `governance/control-matrix.md`
- `examples/evidence-packs/monthly-portfolio/reviewer_signoff.md`

What to evaluate:

- whether the due-diligence questions would surface product function, model
  transparency, introduced risks, business-model fit, vendor safeguards,
  reliability, and controls
- whether the monitoring protocol is realistic for smaller or mid-sized credit
  unions
- whether adverse-action reason support is reviewed separately from broad
  vendor claims
- whether fair-lending and bias-risk prompts are treated as governance review
  triggers, not automatic legal conclusions
- whether the run kit makes clear that third-party outsourcing does not remove
  the credit union's need for oversight

## Researcher or External Reviewer

Use the repository to assess whether the work is concrete, reviewable, and
adaptable across institutions.

Start with:

- `PROJECT_BRIEF.md`
- `docs/evidence-map.md`
- `docs/ai-rmf-alignment.md`
- `docs/release-strategy.md`
- `docs/releases/v0.4.0.md`
- `docs/releases/v0.8.0.md`
- `docs/framework-draft.md`

What to evaluate:

- whether the contribution is more than a concept note
- whether the artifacts are public and reproducible
- whether the AI RMF mapping is concrete enough to guide review without
  implying NIST endorsement or compliance certification
- whether the limitations are stated honestly
- whether the adverse-action benchmark is presented as synthetic proof of method, not real-world validation
- whether future milestones are specific enough to support continued work

## Common Misuses To Avoid

Do not use this repository as:

- proof of production deployment
- legal advice
- a regulatory compliance certification
- a substitute for institution-specific model validation
- evidence of external adoption unless separate adoption evidence exists
- evidence of NCUA approval, endorsement, or acceptance
