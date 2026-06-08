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
- Result type: screening only, not a legal conclusion

- No reason QA exceptions were generated for this run.

## Fair-Lending Screening

- Comparison groups reviewed: 2
- Screening rules applied: 3
- Screening finding count: 4
- Result type: screening only, not a legal conclusion

- region: approval_rate_ratio observed 0.0 against threshold 0.8 (medium, owner: Fair Lending Review)
- segment: approval_rate_ratio observed 0.0 against threshold 0.8 (medium, owner: Fair Lending Review)
- region: override_rate_difference observed 1.0 against threshold 0.25 (medium, owner: Fair Lending Review)
- segment: override_rate_difference observed 1.0 against threshold 0.25 (medium, owner: Fair Lending Review)

## Threshold Breaches

- override_rate: observed 0.5 vs threshold 0.1 (high, owner: Credit Policy Review)

## Issue Register

- iss-0001: override_rate breached its configured threshold (0.5 vs 0.1). Owner: Credit Policy Review. Due: 2026-06-30.
- iss-0002: Fair-lending screening trigger for region: approval_rate_ratio observed 0.0. Owner: Fair Lending Review. Due: 2026-06-30.
- iss-0003: Fair-lending screening trigger for segment: approval_rate_ratio observed 0.0. Owner: Fair Lending Review. Due: 2026-06-30.
- iss-0004: Fair-lending screening trigger for region: override_rate_difference observed 1.0. Owner: Fair Lending Review. Due: 2026-06-30.
- iss-0005: Fair-lending screening trigger for segment: override_rate_difference observed 1.0. Owner: Fair Lending Review. Due: 2026-06-30.
