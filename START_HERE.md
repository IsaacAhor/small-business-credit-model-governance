# Start Here

This repository is a public demonstration of a repeatable governance workflow for
machine-learning-based small business credit underwriting systems.

It is intended for reviewers who need to understand what the repository shows,
how the pieces fit together, and which artifacts to inspect first.

## Fast Review Path

Use this path if you have limited time and want the clearest view of the work:

1. Read `PROJECT_BRIEF.md` for the problem, contribution, users, and current
   limitations.
2. Read `docs/evidence-map.md` to see what each artifact supports and what it
   does not prove.
3. Inspect `examples/evidence-packs/monthly-portfolio/README.md` for the
   curated portfolio-scale evidence-pack outputs (320 synthetic decisions,
   including statistical significance results, BISG proxy screening, and the
   LDA assessment).
4. Inspect `examples/evidence-packs/adverse-action-reason-benchmark/README.md`
   for the synthetic adverse-action reason accuracy benchmark and its public-
   data limits.
5. Review `examples/evidence-packs/monthly-portfolio/monitoring_report.md` for
   the plain-language output of a synthetic monthly governance review at
   portfolio scale. A minimal controlled-breach scenario is also available
   under `examples/evidence-packs/monthly-demo/`.
6. Read `IMPLEMENTATION_GUIDE.md` if you want to understand how an institution
   could adapt the workflow.

## Role-Based Paths

Use `USE_CASES.md` if you are reviewing from a specific role:

- model-risk or validation reviewer
- fair-lending or compliance reviewer
- credit policy or underwriting governance lead
- fintech governance or product risk lead
- researcher or external reviewer

## What To Run

The repository can be reviewed without running code by inspecting the curated
example outputs under `examples/evidence-packs/monthly-portfolio/` (portfolio
scale) and `examples/evidence-packs/monthly-demo/` (minimal controlled
scenario) and `examples/evidence-packs/adverse-action-reason-benchmark/`
(adverse-action reason accuracy benchmark).

If you want to reproduce the synthetic workflow locally, run:

```bash
python scripts/validate_repository.py
python scripts/validate_phase1.py
python scripts/run_monthly_monitoring.py data/synthetic/monthly-portfolio --evidence-root evidence
python scripts/run_adverse_action_reason_benchmark.py --overwrite
python -m unittest discover -s tests -p "test_*.py"
```

## Important Limits

This repository uses synthetic demonstration data. It does not claim production
deployment, lender adoption, regulatory approval, independent recognition, or
legal compliance certification.

Fair-lending outputs are screening triggers for governance review, not legal
conclusions. Adverse-action reason QA outputs are review checks, not legal
advice.
