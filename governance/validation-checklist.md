# Validation Checklist

Use this checklist before approving a new model version or a material change.

## Documentation

- Intended use is documented.
- Training and evaluation data sources are identified.
- Synthetic, proxy, or production data status is disclosed.
- Assumptions and exclusions are explicitly listed.
- Decision thresholds are recorded.
- Adverse-action or reason-code mapping is documented.

## Performance

- Performance metrics are defined and reproducible.
- Validation dataset is distinct from development data.
- Edge cases and adverse scenarios were tested.
- Results are compared against a baseline or prior version.

## Explainability

- Explanation method is documented.
- Explanation outputs are stable enough for governance review.
- Reason-code mapping aligns with model behavior and decision logic.
- Explanation limitations are disclosed.
- Explanation changes since the prior version are reviewed.

## Fair-Lending Screening

- Review population and comparison groups are defined.
- Disparity indicators are calculated or explicitly marked not applicable.
- Proxy-risk review is documented for key features.
- Less discriminatory alternative triggers are assessed.
- Escalation path is identified for material fairness signals.

## Thresholds and Overrides

- Threshold sensitivity is reviewed.
- Override volume and override reasons are reviewed.
- Manual review paths are documented.
- Policy overlays are listed and tied to ownership.

## Governance

- Model owner and reviewer are identified.
- Material changes since the prior version are summarized.
- Monitoring requirements are updated if needed.
- Approval decision and date are recorded.

## Operational Readiness

- Inputs needed in production are available and stable.
- Manual override or exception handling is documented.
- Rollback path exists for material regressions.
- Open risks are recorded with owners.
- Post-change monitoring date is set.
