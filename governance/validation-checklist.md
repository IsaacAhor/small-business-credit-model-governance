# Validation Checklist

Use this checklist before approving a new model version or a material change.

## Documentation

- Intended use is documented.
- Training and evaluation data sources are identified.
- Assumptions and exclusions are explicitly listed.
- Decision thresholds are recorded.

## Performance

- Performance metrics are defined and reproducible.
- Validation dataset is distinct from development data.
- Edge cases and adverse scenarios were tested.
- Results are compared against a baseline or prior version.

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
