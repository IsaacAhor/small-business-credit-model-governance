# Synthetic Vendor Oversight Review

> Demonstration records only. This report is not a legal opinion, compliance certification, regulatory approval, institutional adoption claim, or production validation.

## Review context

- Review: `vrr-synthetic-underwriting-2026`
- Fictional vendor / product: `vnd-example-analytics` / `prd-example-underwriting-api`
- Product version: `synthetic-2.1`
- Review period: `2026-05-01` through `2026-05-31`
- Decision impact / authority: `recommendation` / `institution`
- Risk tier: `high`
- Review status: `accepted_with_conditions`

## Applicability record

- `regulation-b-1002-9` — class `binding_when_applicable`, status `applicable`, checked `2026-08-23`
- `sr-26-2-section-vii` — class `voluntary_or_analogous`, status `not_applicable`, checked `2026-08-23`

## Component inventory and transparency

- `vmc-synthetic-reason-service` — `explanation_service`, role `explanation_only`, transparency `transparent`
- `vmc-synthetic-underwriting-model` — `model`, role `advisory`, transparency `partial`

## Limitations and compensating controls

- `vml-synthetic-proprietary-detail` — The fictional vendor overview omits training code and complete development-data details. Control: Use institution-owned outcome monitoring, reason QA, volume limits, and change review. Residual decision: `accepted_with_controls`.

## Monitoring and heightened review

- Cadence: monthly synthetic review
- Rationale: Monthly review is an illustrative institution choice for the high-risk synthetic profile and is not a regulatory schedule.
- Heightened monitoring: `configured`

## Vendor events and change review

- No vendor events are recorded for this synthetic review period.

## Business-credit notice controls

- `bcn-synthetic-decision-0002` for `dec-0002` — path `written_notice_with_reasons`, specific-reason review `completed`, disposition `accepted_with_conditions`

## Open findings and review gaps

- No open finding is recorded in the synthetic review record.
- Gap **vendor-transparency-limited** (`moderate`): Partial or opaque vendor information is recorded for: vmc-synthetic-underwriting-model
- Gap **conditional-notice-applicability-pending** (`moderate`): One or more conditional FCRA, E-SIGN, or Section 1071 determinations remain pending for: bcn-synthetic-decision-0002

## Output limitations

- All vendor, product, institution, reviewer, contract, and event records in the checked-in fixture are synthetic.
- This output does not establish institutional adoption, model accuracy, notice legal sufficiency, compliance, safety, soundness, security, reliability, or regulatory approval.
- Source applicability and risk acceptance require institution-specific legal, compliance, model-risk, security, and business review.
