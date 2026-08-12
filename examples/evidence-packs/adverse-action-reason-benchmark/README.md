# Adverse-Action Reason Benchmark Evidence Pack

This evidence pack is generated from a synthetic small-business credit benchmark. It demonstrates reason-generation and reason-QA controls under the adverse-action reason accuracy and transparency workstream.

## How To Review This Pack

1. Read `adverse_action_reason_benchmark_report.md` for the benchmark summary.
2. Read `adverse_action_reason_benchmark_results.json` for machine-readable expected and observed exception types.
3. Read `reason_qa_results.json` and `rendered_notice_qa_results.json` for source and visible-notice reconciliation.
4. Read `monitoring_report.md` for the broader evidence-pack output.

## Regeneration Command

```bash
python scripts/run_adverse_action_reason_benchmark.py --overwrite
```

## Important Limits

- Synthetic data only.
- Not a production notice process.
- Not legal advice or a Regulation B compliance certification.
- Not evidence of lender adoption, deployment, regulatory approval, or external validation.
- Public small-business data cannot currently prove actual adverse-action reason accuracy.

Expected seeded failure types observed: True.
