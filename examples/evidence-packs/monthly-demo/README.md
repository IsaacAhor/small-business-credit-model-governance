# Monthly Demo Evidence Pack

This folder contains a curated synthetic evidence pack generated from
`data/synthetic/monthly-demo/`.

It allows a reviewer to inspect the workflow output without running the code.
The files are demonstration-only artifacts and do not contain real applicant,
borrower, lender, or institution data.

## How To Review This Pack

Use this order if you are reviewing the pack for the first time:

1. Read `monitoring_report.md` for the plain-language summary.
2. Open `metric_results.json` to inspect the computed monitoring metrics.
3. Open `breach_register.json` and `issue_register.json` to see how threshold
   breaches become tracked governance issues.
4. Open `reason_qa_results.json` and `reason_stability_report.json` to inspect
   adverse-action reason QA outputs.
5. Open `fair_lending_screening_results.json` and
   `fair_lending_escalation_register.json` to inspect screening triggers and
   escalation records.
6. Open `reviewer_notes.md` and `reviewer_signoff.md` to see how a human review
   step is represented.

## Included Outputs

- `manifest.json`
  Identifies the evidence-pack run and included artifacts.
- `config_snapshot.json`
  Preserves the configuration used for the synthetic review.
- `input_fingerprints.json`
  Records source-input fingerprints for traceability.
- `model_record.json`
  Captures the governed model context.
- `threshold_set.json`
  Lists configured thresholds used for monitoring comparisons.
- `metric_results.json`
  Contains computed monitoring metrics.
- `breach_register.json`
  Records threshold breaches.
- `reason_qa_results.json`
  Records adverse-action reason QA checks and exceptions.
- `reason_stability_report.json`
  Summarizes reason-code stability indicators.
- `fair_lending_screening_results.json`
  Records fair-lending screening triggers.
- `fair_lending_escalation_register.json`
  Converts screening findings into escalation records.
- `issue_register.json`
  Tracks resulting governance issues.
- `monitoring_report.md`
  Provides a readable summary of the synthetic monthly review.
- `reviewer_notes.md`
  Documents review notes and limits.
- `reviewer_signoff.md`
  Provides an illustrative signoff placeholder.

## Important Limits

- Synthetic data only.
- Screening outputs are governance review triggers, not legal conclusions.
- This evidence pack does not claim production deployment or lender adoption.
- Reviewer signoff fields are illustrative placeholders.

## Regeneration Command

```bash
python scripts/run_monthly_monitoring.py data/synthetic/monthly-demo --evidence-root evidence
```

## Related Entry Points

- `../../../START_HERE.md`
- `../../../USE_CASES.md`
- `../../../IMPLEMENTATION_GUIDE.md`
