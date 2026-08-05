# Credit Union AI Vendor-Risk Run Kit

This run kit is a credit-union-facing profile for reviewing AI or ML-enabled
third-party tools used in small-business or member-business credit
underwriting. It maps public NCUA risk-management themes to the repository's
existing governance artifacts: model records, monitoring thresholds,
adverse-action reason review, model-change review, issue tracking, and
reviewer signoff.

The run kit is intended for credit-union vendor-management, compliance,
credit-policy, model-risk, internal-audit, and product-risk reviewers. It is
also useful for fintech or CUSO teams preparing evidence that a credit union
would need to review before using an AI-enabled underwriting product.

## Scope

Use this run kit when an AI or ML-enabled third-party product may affect:

- small-business or member-business credit underwriting
- application intake, scoring, pricing, routing, or approval recommendations
- adverse-action reason generation or notice support
- manual-review queues, overrides, or exception handling
- ongoing portfolio monitoring for an automated or model-assisted credit
  workflow
- vendor-provided model scores, rules, explanations, or decision APIs

This run kit does not cover every AI use at a credit union. It is intentionally
narrow. General chatbots, deposit-account screening, cryptocurrency services,
identity verification, servicing automation, collections automation, and fraud
tools may raise related controls, but they are outside this run kit unless they
directly affect a covered credit underwriting decision or its documentation.

## Source Grounding

This profile is informed by public NCUA and federal resources. The source map is
in [SOURCE_MAP.md](SOURCE_MAP.md).

Key public themes:

- NCUA says credit unions may use AI when implemented in a safe, sound, and
  compliant manner.
- NCUA says AI is supervised within the existing supervisory framework, with
  focus on safety and soundness, applicable compliance obligations, internal
  controls, ongoing risk monitoring, and third-party due diligence.
- NCUA says credit unions using AI vendors should understand how the product
  functions, risks introduced by the AI technology, fit with the credit union's
  business model, and the vendor's safeguards, reliability, and controls.
- NCUA third-party guidance emphasizes planning, risk assessment, due diligence,
  legal review, ongoing controls, monitoring, reporting, and the credit union's
  continuing responsibility for outsourced functions.
- NCUA's Regulation B guide includes adverse-action notice review questions for
  small-business and larger business credit.

## Review Path

1. Define the vendor and use case.
   Use [DUE_DILIGENCE.md](DUE_DILIGENCE.md) to record the vendor, product,
   underwriting function, decision role, data inputs, outputs, and business fit.

2. Map vendor evidence to repo artifacts.
   Use the existing repo records and templates:
   `governance/model-inventory-template.md`,
   `governance/control-matrix.md`,
   `templates/model-governance-checklist.md`, and
   `docs/evidence-map.md`.

3. Review adverse-action reason support.
   Use [ADVERSE_ACTION_REVIEW.md](ADVERSE_ACTION_REVIEW.md) with the
   adverse-action reason run kit:
   `docs/adverse-action-reason-run-kit/README.md`.

4. Define ongoing monitoring.
   Use [MONITORING_PROTOCOL.md](MONITORING_PROTOCOL.md) to set cadence,
   metrics, thresholds, breach handling, issue ownership, model-change review,
   and board or management reporting.

5. Preserve limitations.
   Use [LIMITATIONS.md](LIMITATIONS.md) before citing the artifact. The run kit
   is a public documentation profile. It is not a legal opinion, NCUA approval,
   regulatory compliance certification, production deployment, or external
   validation.

## Minimum Evidence Package

A credit union or reviewer using this profile should be able to assemble:

- AI vendor inventory record
- business-fit and risk-tolerance assessment
- vendor due-diligence questionnaire and responses
- model transparency and limitation record
- adverse-action reason review checklist
- data-security and access-control review
- ongoing monitoring thresholds and cadence
- model-change notification and review process
- issue register and remediation log
- management or board reporting summary
- reviewer signoff tied to a specific vendor product, model version, and review
  period

## Repository Mapping

| Vendor-risk need | Existing repository artifact |
| --- | --- |
| Model and version context | `governance/model-inventory-template.md`; `schemas/model-registry-record.schema.json`; `schemas/model-version-record.schema.json` |
| Monitoring thresholds and breaches | `schemas/threshold-set.schema.json`; `src/credit_gov/monitoring.py`; `examples/evidence-packs/monthly-portfolio/monitoring_report.md` |
| Adverse-action reason generation and QA | `docs/adverse-action-reason-run-kit/`; `src/credit_gov/generation.py`; `src/credit_gov/monitoring.py` |
| Model-change review | `scripts/run_change_validation.py`; `examples/evidence-packs/monthly-portfolio/model_change_validation_report.md` |
| Issue and remediation tracking | `examples/evidence-packs/monthly-portfolio/issue_register.json`; `.github/ISSUE_TEMPLATE/validation-finding.md`; `.github/ISSUE_TEMPLATE/monitoring-breach.md` |
| Reviewer signoff | `examples/evidence-packs/monthly-portfolio/reviewer_signoff.md` |
| Public-data model-risk demonstration | `docs/model-risk-oversight-run-kit/README.md` |
| Claim discipline | `docs/evidence-map.md`; `docs/release-strategy.md`; `START_HERE.md` |

## Reviewer Questions

The most useful independent review questions are:

- Does this profile ask for the evidence a credit union would need to evaluate
  an AI-enabled underwriting vendor?
- Are the adverse-action reason review questions specific enough for practical
  Regulation B oversight?
- Are the monitoring metrics and escalation paths realistic for a smaller or
  mid-sized credit union?
- Does the profile correctly distinguish vendor due diligence, model-risk
  review, compliance review, cybersecurity review, and legal judgment?
- What evidence would be missing before a credit union could rely on this
  workflow in a real vendor-management process?
