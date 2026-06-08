# Monthly Demo Evidence Pack

This folder contains a curated synthetic evidence pack generated from
`data/synthetic/monthly-demo/`.

It allows a reviewer to inspect the workflow output without running the code.
The files are demonstration-only artifacts and do not contain real applicant,
borrower, lender, or institution data.

## Included Outputs

- `manifest.json`
- `config_snapshot.json`
- `input_fingerprints.json`
- `model_record.json`
- `threshold_set.json`
- `metric_results.json`
- `breach_register.json`
- `reason_qa_results.json`
- `reason_stability_report.json`
- `fair_lending_screening_results.json`
- `fair_lending_escalation_register.json`
- `issue_register.json`
- `monitoring_report.md`
- `reviewer_notes.md`
- `reviewer_signoff.md`

## Important Limits

- Synthetic data only.
- Screening outputs are governance review triggers, not legal conclusions.
- This evidence pack does not claim production deployment or lender adoption.
- Reviewer signoff fields are illustrative placeholders.

## Regeneration Command

```bash
python scripts/run_monthly_monitoring.py data/synthetic/monthly-demo --evidence-root evidence
```
