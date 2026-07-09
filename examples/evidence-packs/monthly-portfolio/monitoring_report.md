# Monthly Monitoring Report

This report is deterministic, synthetic, and intended only for governance workflow demonstration.

- Run ID: `run-2026-06`
- Model ID: `mdl-smb-credit-xgb`
- Version ID: `ver-2026-06`
- Total decisions reviewed: 320
- Approval rate: 0.4813
- Decline rate: 0.5188
- Override rate: 0.1375
- Manual review rate: 0.1469

## Adverse-Action Reason QA

- Declined decisions reviewed: 166
- Generated reason outputs reviewed: 506
- QA exception count: 1
- Result type: screening only, not a legal conclusion

- dec-0090: missing_reason_code (Declined decision has no generated adverse-action reason output.)

## Fair-Lending Screening

- Comparison groups reviewed: 2
- Screening rules applied: 3
- Screening finding count: 2
- Result type: screening only, not a legal conclusion

- region: approval_rate_ratio observed 0.5105 against threshold 0.8 (medium, owner: Fair Lending Review)
  Statistical test: two_proportion_z_test_pooled | p = 0.000385 | significant at alpha 0.05
- segment: approval_rate_ratio observed 0.767 against threshold 0.8 (medium, owner: Fair Lending Review)
  Statistical test: two_proportion_z_test_pooled | p = 0.130721 | not significant at alpha 0.05

## BISG Proxy Screening

- Method: Bayesian Improved Surname Geocoding (`bisg-2026-06-monthly`)
- Decisions matched to demographic inputs: 320 of 320
- Reference group: white | alpha: 0.05
- Significant finding count: 0
- Result type: probabilistic proxy screening, not observed demographics or a legal conclusion

- No statistically significant proxy-group approval-rate gaps were identified.

## Less-Discriminatory-Alternative Assessment

- Assessment ID: `lda-2026-06-monthly`
- Comparison group: monitoring.region
- Baseline disparity ratio: 0.5105 | separation: 0.2276
- Alternative disparity ratio: 0.7628 | separation: 0.2713
- Disparity improvement: 0.2523 | separation change: 0.0437
- Qualifying alternative identified: True
- Recommendation: Candidate alternative reduces group approval-rate disparity while holding predictive separation within tolerance. Trigger a documented less-discriminatory-alternative review under the governance framework.
- Result type: synthetic assessment trigger, not a legal conclusion

## Threshold Breaches

- override_rate: observed 0.1375 vs threshold 0.1 (high, owner: Credit Policy Review)

## Issue Register

- iss-0001: override_rate breached its configured threshold (0.1375 vs 0.1). Owner: Credit Policy Review. Due: 2026-06-30.
- iss-0002: Reason QA exception for dec-0090: missing_reason_code. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0003: Fair-lending screening trigger for region: approval_rate_ratio observed 0.5105. Owner: Fair Lending Review. Due: 2026-06-30.
- iss-0004: Fair-lending screening trigger for segment: approval_rate_ratio observed 0.767. Owner: Fair Lending Review. Due: 2026-06-30.
