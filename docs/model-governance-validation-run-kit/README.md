# Model-Governance Validation Run Kit

This run kit adds a reviewer-facing governance layer to the synthetic monthly
dataset. It records model risk and materiality, explainability-method design,
validation posture, and risk-based monitoring in four linked contracts. A
deterministic command validates the complete bundle and emits a summary, report,
and hash manifest.

The run kit is a technical demonstration. It is not an independent validation,
legal opinion, regulatory conclusion, compliance certification, or deployment
approval.

## Why This Layer Exists

Monitoring outputs alone do not show why a particular degree of review is
appropriate, which explainability method is governed, whether validation is
independent, or how open findings affect promotion. The bundle makes those
relationships explicit and machine-checkable.

The design is informed by FinRegLab's April 9, 2026 *Framework for Managing
Machine Learning Models in Consumer Credit Underwriting*. That publication is a
practitioner framework shaped through an OCC Project REACh working group; it is
not a statute, regulation, agency rule, or supervisory issuance. It also focuses
on consumer underwriting and large-bank practices. This repository uses it as a
technical reference, not as authority that makes every practice mandatory or
directly transferable to every small-business credit context.

Current supervisory grounding remains the interagency April 17, 2026 revised
model-risk guidance (Federal Reserve SR 26-2 / OCC Bulletin 2026-13 / FDIC
FIL-16-2026), subject to its risk-based scope and institution applicability.
Regulation B, 12 CFR 1002.9, separately supplies the binding adverse-action
notice requirements where applicable.

## Bundle Contracts

See `SOURCE_MAP.md` for the source class, implementation status, and unproven
boundary of each control.

The optional bundle is all-or-nothing. Existing datasets without any of these
files remain backward compatible. If one is present, all four must be present,
valid, linked to the same model/version context, and included in the evidence
manifest:

- `model-risk-profile.json` records purpose, inherent risk, exposure,
  materiality, aggregate dependencies, and commensurate validation/monitoring
  rigor.
- `explainability-method-records.json` records intended uses, reference
  population, correlation assumptions, aggregation rationale, directionality
  review, limitations, and test references for each governed method.
- `model-validation-record.json` records scope, reviewer independence, evidence,
  findings, disposition, and promotion status. Developer self-review cannot be
  labeled approved or promotion-ready.
- `model-monitoring-plan.json` links risk, validation, explainability, thresholds,
  metrics, limitations, change triggers, and review ownership.

## Run

From a source checkout:

```bash
python scripts/run_governance_review.py data/synthetic/monthly-demo examples/evidence-packs/model-governance-review --overwrite
```

From an installed package:

```bash
credit-gov-governance-review data/synthetic/monthly-demo review-output
```

Without `--overwrite`, the command fails if any of its three named outputs
already exists. With `--overwrite`, it replaces only those named files.

## Outputs

- `governance-review-summary.json`: normalized reviewer facts and explicit gaps
- `governance-review-report.md`: concise human-readable review path
- `governance-review-manifest.json`: SHA-256 hashes for seven inputs and the two
  substantive outputs

The checked-in example deliberately reports developer self-review, a pending
independent review, open findings, draft method status, and promotion not
allowed. These are accurate limitations, not defects to hide.

## What Would Close The Main Gaps

1. An independent model-risk or lending practitioner reviews a tagged artifact,
   records identity and scope, and provides findings that can be preserved.
2. The method record is tested against an implemented model and a fit-for-purpose
   reference population, with directionality and correlation assumptions
   reviewed.
3. Open findings are remediated or formally accepted with evidence and dates.
4. Monitoring metrics and thresholds are calibrated to a documented use case
   rather than copied from the synthetic fixture.

Code cannot manufacture independent review or institutional use. Those remain
external evidence events.

## Optional Linked Recourse Sidecar

`docs/recourse-assessment-run-kit/README.md` documents a separate optional
sidecar for bounded action-set queries. It may share stable decision, model,
version, and run context, but it does not extend this governance bundle or the
mandatory core dataset. Its subject features, method, action set, prediction
provider, results, QA, manifest, and reviewer files remain separate.

The sidecar does not change explainability-method approval, validation
disposition, promotion status, required adverse-action reasons, or rendered
notice records. A review of this governance bundle does not automatically
validate a later recourse release.
