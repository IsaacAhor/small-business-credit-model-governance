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
- `examples/evidence-packs/monthly-demo/monitoring_report.md`
- `examples/evidence-packs/monthly-demo/reviewer_signoff.md`

What to evaluate:

- whether the model/version/run relationships are traceable
- whether monitoring thresholds are explicit
- whether breaches and issues are linked to reviewer action
- whether limitations are documented separately from findings

## Fair-Lending or Compliance Reviewer

Use the repository to inspect how fair-lending screening can be treated as a
governed review trigger rather than an unsupported legal conclusion.

Start with:

- `templates/fair-lending-monitoring-checklist.md`
- `schemas/fair-lending-screening-config.schema.json`
- `examples/evidence-packs/monthly-demo/fair_lending_screening_results.json`
- `examples/evidence-packs/monthly-demo/fair_lending_escalation_register.json`
- `examples/evidence-packs/monthly-demo/reviewer_notes.md`

What to evaluate:

- whether comparison groups and thresholds are configured before review
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
- `examples/evidence-packs/monthly-demo/threshold_set.json`
- `examples/evidence-packs/monthly-demo/issue_register.json`

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
- `examples/evidence-packs/monthly-demo/README.md`

What to evaluate:

- what minimum governance records would need to exist before monitoring
- what can be automated in a batch workflow
- what should remain subject to human review
- where institution-specific policy, legal review, and validation judgment are
  still required

## Researcher or Independent Reviewer

Use the repository to assess whether the work is concrete, reviewable, and
portable beyond a single employer.

Start with:

- `PROJECT_BRIEF.md`
- `docs/evidence-map.md`
- `docs/release-strategy.md`
- `docs/releases/v0.4.0.md`
- `docs/framework-draft.md`

What to evaluate:

- whether the contribution is more than a concept note
- whether the artifacts are public and reproducible
- whether the limitations are stated honestly
- whether future milestones are specific enough to support continued work

## Common Misuses To Avoid

Do not use this repository as:

- proof of production deployment
- legal advice
- a regulatory compliance certification
- a substitute for institution-specific model validation
- evidence of external adoption unless separate adoption evidence exists
