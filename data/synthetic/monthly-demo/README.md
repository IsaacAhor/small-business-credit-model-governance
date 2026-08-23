# Monthly Demo Dataset

This dataset is deterministic, synthetic, and intended only for governance
workflow demonstration.

Purpose:

- exercise the Phase 1 schemas
- exercise the optional model-risk, explainability-method, validation, and
  monitoring-plan bundle
- show separation between underwriting and monitoring-only fields
- provide stable JSON inputs for command-line validation and tests

The governance bundle intentionally records developer self-review, pending
independent review, open findings, draft method status, and promotion not
allowed. Generate its deterministic reviewer summary with:

```bash
python scripts/run_governance_review.py data/synthetic/monthly-demo review-output
```

This dataset does not represent production lending activity or legal
compliance.
