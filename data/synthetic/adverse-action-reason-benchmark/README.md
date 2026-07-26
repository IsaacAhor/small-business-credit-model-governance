# Adverse-Action Reason Accuracy Benchmark Dataset

This is a synthetic small-business credit benchmark for adverse-action reason
accuracy and transparency under Regulation B 12 CFR 1002.9.

The dataset is deliberately constructed with clean declined-decision examples
and controlled QA failures. It is not a production lending dataset, not a
notice process, not legal advice, and not evidence of lender adoption or
regulatory approval.

## Seeded Conditions

- clean declined decision with mapped principal reasons
- missing reason output for a declined decision
- unmapped reason code
- generic reason text
- driver-to-mapping mismatch
- stale mapping version
- reason output attached to a non-declined decision
- excessive reason count for one declined decision
- credit-report-only placeholder reason
- declined decision with no mapped adverse driver

## Regeneration Command

```bash
python scripts/run_adverse_action_reason_benchmark.py --overwrite
```

The generated curated example pack is written to
`examples/evidence-packs/adverse-action-reason-benchmark/`.
