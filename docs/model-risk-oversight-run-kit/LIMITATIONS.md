# Scope and Limitations: SBA Public-Data Monitoring Run

## What the run demonstrates

- Ingestion of current-layout SBA 7(a)/504 FOIA approved-loan files with
  source hashes and row-level disposition accounting.
- Fixed-horizon charge-off labeling based on `FirstDisbursementDate`,
  `ChargeOffDate`, and `AsOfDate`.
- A pre-monitoring development split, out-of-time scoring, outcome performance,
  and numeric and categorical drift measurements.
- Generation of traceable monitoring artifacts with explicit module-
  applicability decisions and output hashes.

These are implementation and reproducibility results. They are not proof of
production use, institutional adoption, independent validation, field impact,
or regulatory compliance.

## Source boundary

SBA FOIA files contain booked or approved loans. They do not contain the full
application and decision population. They also lack model-driver provenance,
adverse-action notices, review and override events, and applicant protected-
class fields.

Consequently, the following modules are `not_applicable`:

- approval and decline rates;
- manual-review rates;
- override monitoring;
- adverse-action reason and notice QA; and
- fair-lending or protected-class disparity screening.

The generated inputs for these modules are empty where appropriate. No
placeholder override, reason mapping, protected-class value, or synthetic zero
is presented as an observed SBA fact.

## Outcome definition and censoring

The default label is a charge-off whose recorded `ChargeOffDate` falls on or
before the configured number of months after `FirstDisbursementDate`. A row is
eligible only when its `AsOfDate` reaches that horizon. Charge-offs after the
horizon are nondefaults at the horizon, not lifetime nondefaults.

Status normalization removes spaces and punctuation, so the current `P I F`
value is recognized as `PIF`. A seasoned `EXEMPT` active, disbursed loan is a
nondefault at the horizon. Canceled records, unsupported statuses, unseasoned
records, invalid core fields, and charge-off signals without an event date are
excluded and counted separately.

This definition does not correct for every possible administrative lag,
recovery, servicing change, guarantee purchase, prepayment, or SBA reporting
revision. Review the current data dictionary and disposition counts for every
run.

## Model boundary

The regularized logistic regression is a governed-model stand-in for testing
monitoring controls. It uses loan amount, term, jobs, two-digit NAICS,
business type, region, delivery method, and program. It does not make a lending
recommendation and has not been validated for underwriting.

Development rows precede the configured monitoring-start date. Monitoring rows
are not used to fit the model. Development performance is therefore labeled
in-sample, while the monitoring section is out-of-time. The reported metrics do
not establish causal validity, stability in production, or fitness for a
particular institution.

The cross-cohort summaries use each full cohort. Evidence-pack inputs may use a
bounded sample to control artifact size, and the threshold register inside such
a pack therefore evaluates the sample, not the full cohort. A run intended to
produce full-population breach decisions must set the sample limit at or above
the cohort size.

## Drift boundary

PSI is reported for score, amount, term, program, NAICS sector, business type,
region, and delivery method relative to the development population. Bands of
less than 0.10, 0.10 to less than 0.25, and 0.25 or more are demonstration
review bands. They are not universal validation standards or automatic model-
change decisions.

## Privacy and publication

The adapter does not retain borrower names or street addresses. Raw downloads
and run directories should remain outside version control. If a small output
subset is intentionally published, review it independently, retain its source
and output hashes, and preserve all limitations with it.
