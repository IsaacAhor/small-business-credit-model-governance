# Model Governance Review Summary

> Synthetic governance review only. This is not an independent validation, regulatory conclusion, legal opinion, or deployment approval.

## Model context

- Model: `mdl-smb-credit-xgb` — Small Business Credit Underwriting Model
- Version: `ver-2026-05`
- Intended use: Risk-rank small business applicants for manual and automated underwriting review.

## Risk-based governance

- Materiality: `moderate`
- Inherent risk / exposure: `moderate` / `low`
- Validation / monitoring rigor: `standard` / `standard`

## Explainability methods

- `xai-ranked-recorded-drivers`: Ranked recorded-driver mapping (status `draft`, directionality review `pending`)

## Validation posture

- Independence: `developer_self_review`
- Reviewer: No independent reviewer assigned
- Disposition: `pending_independent_review`
- Promotion allowed: `false`
- Open findings: `2`

## Review gaps

- **independent-validation** (`high`): Independent validation is not established by this bundle.
- **open-validation-findings** (`high`): 2 validation finding(s) remain open.
- **explanation-directionality-review** (`moderate`): Directionality review remains incomplete for: xai-ranked-recorded-drivers
- **explainability-method-approval** (`moderate`): Approved method status is not established for: xai-ranked-recorded-drivers

## Limitations

- The source dataset is synthetic and does not represent production lending decisions.
- This output summarizes governance records; it is not an independent validation, regulatory conclusion, legal opinion, or deployment approval.
