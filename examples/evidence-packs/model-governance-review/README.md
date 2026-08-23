# Synthetic Model-Governance Review Example

This directory contains the deterministic reviewer summary generated from the
optional governance bundle in `data/synthetic/monthly-demo/`.

## Review Order

1. Read `governance-review-report.md` for the concise posture and gaps.
2. Inspect `governance-review-summary.json` for structured risk, method,
   validation, and monitoring facts.
3. Use `governance-review-manifest.json` to verify the input and output hashes.

The example is intentionally candid: validation is a developer self-review,
independent review is pending, findings remain open, and promotion is not allowed.
Synthetic data only. Nothing in this pack establishes production
performance, legal compliance, regulatory approval, or independent validation.

## Regeneration Command

```bash
python scripts/run_governance_review.py data/synthetic/monthly-demo examples/evidence-packs/model-governance-review --overwrite
```
