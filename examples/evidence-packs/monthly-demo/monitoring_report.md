# Monthly Monitoring Report

This report is deterministic, synthetic, and intended only for governance workflow demonstration.

- Run ID: `run-2026-05`
- Model ID: `mdl-smb-credit-xgb`
- Version ID: `ver-2026-05`
- Total decisions reviewed: 2
- Approval rate: 0.5
- Decline rate: 0.5
- Override rate: 0.5
- Manual review rate: 0.5

## Adverse-Action Reason QA

- Declined decisions reviewed: 1
- Generated reason outputs reviewed: 2
- QA exception count: 0
- Source-to-notice control status: `not_run_missing_source_to_notice_inputs`
- Rendered-notice control status: `not_run_missing_source_to_notice_inputs` (0 exception(s))
- Result type: screening only, not a legal conclusion

- No reason QA exceptions were generated for this run.

## Fair-Lending Screening

- Comparison groups reviewed: 2
- Screening rules applied: 3
- Screening finding count: 0
- Inconclusive threshold-observation count: 4
- Finding gate: minimum group size 30; rate screens require significance at alpha 0.05
- Result type: screening only, not a legal conclusion

- No fair-lending screening findings were generated for this run.

### Inconclusive Threshold Observations

- region: approval_rate_ratio observed 0.0 against threshold 0.8 (inconclusive_insufficient_sample); One or more comparison groups is below the configured minimum group size.
- segment: approval_rate_ratio observed 0.0 against threshold 0.8 (inconclusive_insufficient_sample); One or more comparison groups is below the configured minimum group size.
- region: override_rate_difference observed 1.0 against threshold 0.25 (inconclusive_insufficient_sample); One or more comparison groups is below the configured minimum group size.
- segment: override_rate_difference observed 1.0 against threshold 0.25 (inconclusive_insufficient_sample); One or more comparison groups is below the configured minimum group size.

## Threshold Breaches

- override_rate: observed 0.5 vs threshold 0.1 (high, owner: Credit Policy Review)

## Issue Register

- iss-0001: override_rate breached its configured threshold (0.5 vs 0.1). Owner: Credit Policy Review. Due: 2026-06-30.
