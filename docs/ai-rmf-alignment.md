# AI RMF Alignment

This document maps this repository's small-business credit underwriting
model-governance workflow to the NIST AI Risk Management Framework (AI RMF)
functions: Govern, Map, Measure, and Manage.

The mapping is a practical orientation aid. It is not a NIST profile, NIST
endorsement, regulatory approval, legal advice, compliance certification, or a
complete institution-specific implementation.

## Use-Case Context

The repository demonstrates a governance evidence workflow around an
ML-assisted small-business credit underwriting system. It focuses on structured
model records, monitoring thresholds, adverse-action reason review,
model-change review, issue tracking, and reviewer-ready evidence packs.

The public examples use synthetic demonstration data and scoped public-data run
kits. The workflow is not an underwriting model, a production deployment, a
credit decisioning service, or proof of real-world notice accuracy.

## Alignment Summary

| AI RMF function | Repository alignment | Primary artifacts | Important limits |
| --- | --- | --- | --- |
| Govern | Defines model-governance records, control ownership, validation expectations, change logs, data policy, and evidence discipline before review outputs are interpreted. | `governance/control-matrix.md`, `governance/model-inventory-template.md`, `governance/validation-checklist.md`, `governance/data-policy.md`, `docs/evidence-map.md` | Does not replace a lender's formal governance program, legal review, board-approved policy, or three-lines-of-defense controls. |
| Map | Documents the model context, intended use, boundaries, data assumptions, reason-code mappings, thresholds, and known limits of synthetic or public data. | `docs/system-charter.md`, `docs/system-boundaries.md`, `docs/domain-object-model.md`, `schemas/`, `docs/model-risk-oversight-run-kit/README.md`, `docs/adverse-action-reason-run-kit/PUBLIC_DATA_LIMITS.md` | Does not prove that any real institution has adopted the workflow or that every deployment context has been assessed. |
| Measure | Runs validation checks, monitoring metrics, reason QA, statistical screening, BISG proxy review, measurement-error sensitivity checks, and synthetic adverse-action reason benchmark outputs. | `scripts/validate_repository.py`, `scripts/validate_phase1.py`, `scripts/run_monthly_monitoring.py`, `scripts/run_adverse_action_reason_benchmark.py`, `examples/evidence-packs/`, `docs/fair-lending-statistics.md` | Does not establish production model validity, legal compliance, fair-lending conclusions, or real-world adverse-action notice accuracy. |
| Manage | Converts monitoring breaches, reason exceptions, screening findings, and model-change differences into issue registers, reviewer notes, reports, and signoff artifacts. | `examples/evidence-packs/monthly-portfolio/issue_register.json`, `examples/evidence-packs/monthly-portfolio/monitoring_report.md`, `examples/evidence-packs/monthly-portfolio/reviewer_notes.md`, `examples/evidence-packs/monthly-portfolio/reviewer_signoff.md`, `examples/evidence-packs/monthly-portfolio/model_change_validation_report.md` | Does not perform institutional remediation, approve model promotion, or substitute for accountable human governance. |

## Practical Pattern

The repository follows a repeatable pattern:

1. Define the governed model and review boundary.
2. Configure thresholds, reason-code mappings, and review rules before a run.
3. Validate structured inputs and cross-file relationships.
4. Generate monitoring, reason-review, and change-review outputs.
5. Assemble reviewer-ready evidence packs.
6. Route breaches and exceptions to issue records and reviewer signoff.
7. Preserve limitations so outputs are not overstated.

This pattern is intended to make AI risk management reviewable in a specific
credit-governance context. It uses the AI RMF vocabulary while keeping the
credit-specific analysis grounded in separate model-risk, adverse-action,
validation, and institution-specific review requirements.

## Example Playbook Additions Suggested By This Workflow

This repository suggests several concrete examples that may help make AI RMF
Playbook guidance more operational for credit underwriting and similar
regulated decision systems:

- Require a documented model context, intended-use boundary, and non-objectives
  before measurement outputs are interpreted.
- Preserve input fingerprints and configuration snapshots so reviewers can trace
  every generated evidence pack back to the exact records used.
- Treat reason-code mappings as governed records with versioning, effective
  dates, and change review.
- Test adverse-action reason outputs for completeness, mapping traceability,
  specificity, and stability before relying on them in a review workflow.
- Use preconfigured monitoring thresholds and escalation owners to prevent
  post hoc interpretation of model-risk findings.
- Separate screening triggers from legal conclusions, especially where public or
  synthetic data cannot support the stronger conclusion.
- Use model-change validation to compare prior and current model, threshold,
  and reason-mapping records before promotion or release.
- Require reviewer notes and signoff fields that explicitly capture unresolved
  issues, accepted limitations, and follow-up actions.

## Review Path

A reviewer can inspect the AI RMF-aligned workflow without running code:

1. `PROJECT_BRIEF.md`
2. `docs/evidence-map.md`
3. `IMPLEMENTATION_GUIDE.md`
4. `examples/evidence-packs/monthly-portfolio/README.md`
5. `docs/adverse-action-reason-run-kit/README.md`
6. `docs/model-risk-oversight-run-kit/README.md`

To reproduce the main synthetic checks locally, run:

```bash
python scripts/validate_repository.py
python scripts/validate_phase1.py
python scripts/run_monthly_monitoring.py data/synthetic/monthly-portfolio --evidence-root evidence
python scripts/run_adverse_action_reason_benchmark.py --overwrite
python -m unittest discover -s tests -p "test_*.py"
```

## Source Context

The NIST AI RMF and Playbook are voluntary resources for managing AI risks and
improving trustworthy AI practices. The AIRC use-case page also states that
NIST does not validate or endorse individual use cases. This repository should
therefore be read as an independent, public technical demonstration that uses
AI RMF vocabulary, not as a NIST-recognized or NIST-approved implementation.

For the credit-union vendor-risk profile, AI RMF and SR 26-2 are voluntary or
analogous design references only. They do not create an NCUA AI requirement or
determine a credit union's legal or supervisory obligations.
