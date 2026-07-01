# Synthetic dataset: monthly-portfolio

Portfolio-scale synthetic dataset (320 decisions) for the monthly monitoring
demonstration. It is generated deterministically by
`scripts/build_portfolio_dataset.py` from a fixed seed, so it is reproducible
evidence rather than hand-authored fixtures.

**Everything here is synthetic. No production data, no protected-class labels,
and no legal conclusions are represented.**

## What it demonstrates

At realistic volume (versus the 2-record `monthly-demo`), the standard
monitoring run produces non-trivial, believable governance signals:

- an `override_rate` threshold breach;
- a regional fair-lending approval-rate-ratio finding (a stricter west-region
  cutoff drives the disparity);
- a small, realistic crop of adverse-action reason-QA exceptions (one declined
  decision is seeded with no generated reason);
- a less-discriminatory-alternative (LDA) assessment that flags a region-neutral
  candidate cutoff as a qualifying alternative to review.

## Additional inputs (beyond the standard Phase 1 contract)

These optional files support the reason-generation and LDA steps. They are not
part of the Phase 1 monitoring schema contract and are ignored by the core
monitoring validator:

- `adverse-action-driver-contributions.json` — per-declined-decision ranked
  driver contributions consumed by the reason-generation step.
- `alternative-model-decisions.json` — a candidate alternative model's decisions
  on the same population, consumed by the LDA assessment.
- `lda-assessment-config.json` — thresholds and group configuration for the LDA
  assessment.

## Regenerate

```bash
python scripts/build_portfolio_dataset.py
# reason outputs are (re)generated as part of the build; to regenerate alone:
python scripts/generate_adverse_action_reasons.py data/synthetic/monthly-portfolio
# verify shipped reasons match current generation logic:
python scripts/generate_adverse_action_reasons.py data/synthetic/monthly-portfolio --check
```
