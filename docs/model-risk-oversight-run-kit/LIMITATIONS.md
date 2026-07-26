# Scope and Limitations - Model-Risk Oversight Public-Data Run

A candid statement of scope and limitations. Read before reusing or reporting
this run's outputs.

## What this run IS

- A demonstration that the governance monitoring workflow runs on **real
  federal small-business lending records** (SBA 7(a)/504 FOIA), producing
  reviewer-ready evidence packs and a cross-cohort drift signal on real
  distributions.
- Evidence of **integration and reproducibility** - the defensible
  contribution - not of novel methods.

## What this run is NOT

- **Not an underwriting model.** The default-risk model is a governed-model
  stand-in so the monitoring workflow has something to monitor. It makes no
  lending recommendation and is not tuned or validated for decisioning.
- **Not adoption, deployment, or institutional reliance.** No lender uses this.
- **Not a fairness or protected-class analysis.** SBA FOIA is approved-only
  with no applicant demographics. Fair-lending and adverse-action work requires
  a different dataset. HMDA can support only off-domain mechanics, not small-
  business proof.

## Metrics that are NOT meaningful on this dataset (exclude from interpretation)

- `approval_rate` (always 1.0 - approved-only), `decline_rate` (0),
  `override_rate` (0 - no override data), `manual_review_rate` (0),
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

## Public-Data Reminder

Current public small-business loan-level datasets do not provide the full
application decision chain needed for decline, adverse-action, or applicant-
level fairness claims. Future public small-business lending data may improve
context, but SBA or HMDA should not be treated as a substitute for small-
business decision-driver and notice data.
