# Scope and Limitations — SBA 7(a) Monitoring Run

A candid statement of scope and limitations. Read before reusing or reporting
this run's outputs.

## What this run IS

- A demonstration that the governance monitoring workflow runs on **real
  federal small-business lending records** (SBA 7(a)/504 FOIA), producing
  reviewer-ready evidence packs and a cross-cohort drift signal on real
  distributions.
- Evidence of **integration and reproducibility** — the defensible
  contribution — not of novel methods.

## What this run is NOT

- **Not an underwriting model.** The default-risk model is a governed-model
  stand-in so the monitoring workflow has something to monitor. It makes no
  lending recommendation and is not tuned or validated for decisioning.
- **Not adoption, deployment, or institutional reliance.** No lender uses this.
- **Not a fairness or protected-class analysis.** SBA FOIA is approved-only with
  no applicant demographics. Fair-lending / adverse-action work belongs to the
  HMDA 2025 track, where declines and self-reported demographics exist.

## Metrics that are NOT meaningful on this dataset (exclude from interpretation)

- `approval_rate` (always 1.0 — approved-only), `decline_rate` (0),
  `override_rate` (0 — no override data), `manual_review_rate` (0),
  adverse-action reason QA (no declines), and fair-lending disparity
  (no demographics). The `override-events.json` file contains a single
  clearly-labeled placeholder record solely to satisfy the workflow's
  non-empty-file requirement; it represents no real override.

## Metrics that ARE meaningful

- **Charge-off (default) rate per cohort** and its drift over time.
- **Score distribution and drift** across cohorts.
- **Portfolio-composition drift** (segment / region / channel mix).

## Data-quality handling

- Restricted to matured loans (LoanStatus PIF or CHGOFF) so the default label is
  observed, and to FY2010+ to avoid older definitional changes.
- Charge-off label = LoanStatus CHGOFF or positive GrossChargeOffAmount.
- Verify SBA column names against the current data dictionary before each run.

## Regulatory-currency reminder

No public small-business loan-level *decision* dataset (approvals + declines +
demographics) exists. Section 1071 collection begins 2028-01-01; public
availability is deferred to a future rulemaking (post-2029, undetermined). This
absence is a real transparency gap in public small-business credit data — state it plainly rather
than implying SBA or HMDA is a substitute for small-business decision data.
