# Start Here

This repository is a public demonstration of a repeatable governance workflow for
machine-learning-based small business credit underwriting systems.

It is intended for reviewers who need to understand what the repository shows,
how the pieces fit together, and which artifacts to inspect first.

## External review assignments

The [reviewer groups](docs/external-review/reviewer-groups.md) define the
expertise and scope for implementation, credit-governance/adverse-action,
and methodology/evaluation assessment.

For external review, choose a [scoped technical review](docs/external-review/technical-review.md)
with execution and challenge cases, or a
[practitioner assessment](docs/external-review/practitioner-assessment.md)
of prepared artifacts with no installation required. Both use the
[shared procedure](docs/external-review/protocol.md) and an agreed
[source target](docs/external-review/current.md). Each route records
its actual scope and limitations; these documents do not establish that an
external review has occurred.

For an agreed external review, follow the selected brief and target sheet.
The general project tour and commands below are optional background; they are
not the assignment checklist and do not replace its version-specific commands.

## Fast Review Path

Use these references for a broader overview of the project:

1. Read `PROJECT_BRIEF.md` for the problem, contribution, users, and current
   limitations.
2. Read `docs/evidence-map.md` to see what each artifact supports and what it
   does not prove.
3. Read `docs/ai-rmf-alignment.md` for a NIST AI RMF-oriented view of how
   the workflow maps to Govern, Map, Measure, and Manage.
4. Read `docs/model-governance-validation-run-kit/README.md` and inspect
   `examples/evidence-packs/model-governance-review/README.md` for the formal
   risk, explainability, validation, monitoring, and gap records.
5. Read `docs/adverse-action-reason-run-kit/README.md` for the synthetic
   adverse-action reason accuracy benchmark, run command, evidence-pack review
   path, and public-data limits.
6. Read `docs/recourse-assessment-run-kit/README.md` to inspect the separate
   optional action-set assessment, conservative statuses, and curated reviewer
   pack without conflating it with required adverse-action reasons.
7. Read `docs/credit-union-ai-vendor-risk-run-kit/README.md` if you are
   reviewing an AI-enabled credit-union underwriting vendor, CUSO relationship,
   or third-party small-business/member-business lending tool. Inspect
   `examples/evidence-packs/credit-union-vendor-risk/README.md` for the
   deterministic synthetic vendor-oversight output.
8. Review `examples/evidence-packs/monthly-portfolio/monitoring_report.md` for
   the plain-language output of a synthetic monthly governance review at
   portfolio scale. Its significance, proxy-screening, and LDA outputs are
   supporting risk screens rather than the primary review path. A minimal
   controlled-breach scenario is also available under
   `examples/evidence-packs/monthly-demo/`.
9. Read `IMPLEMENTATION_GUIDE.md` if you want to understand how an institution
   could adapt the workflow.

## Role-Based Paths

Use `USE_CASES.md` if you are reviewing from a specific role, including a
credit-union vendor-risk review role:

- model-risk or validation reviewer
- recourse or explanation-method reviewer
- fair-lending or compliance reviewer
- credit policy or underwriting governance lead
- credit-union vendor-management or CUSO reviewer
- fintech governance or product risk lead
- researcher or external reviewer

## What To Run

The repository can be reviewed without running code by inspecting the curated
example outputs under `examples/evidence-packs/monthly-portfolio/` (portfolio
scale) and `examples/evidence-packs/monthly-demo/` (minimal controlled
scenario) and `docs/adverse-action-reason-run-kit/README.md`
(adverse-action reason accuracy benchmark landing path). For a credit-union
third-party underwriting-tool review, also inspect
`docs/credit-union-ai-vendor-risk-run-kit/README.md` and
`examples/evidence-packs/credit-union-vendor-risk/README.md`.
For the separate recourse sidecar, inspect
`examples/evidence-packs/recourse-assessment/`.

If you want to reproduce the synthetic workflow locally, run:

```bash
python scripts/validate_repository.py
python scripts/validate_phase1.py
python scripts/validate_vendor_risk_run_kit.py data/synthetic/credit-union-vendor-risk/baseline-complete data/synthetic/monthly-demo
python scripts/run_governance_review.py data/synthetic/monthly-demo review-output
python scripts/run_monthly_monitoring.py data/synthetic/monthly-portfolio --evidence-root evidence
python scripts/run_adverse_action_reason_benchmark.py --overwrite
python scripts/validate_recourse_run_kit.py data/synthetic/adverse-action-reason-benchmark data/synthetic/recourse-assessment/baseline
python scripts/build_recourse_evidence_pack.py data/synthetic/adverse-action-reason-benchmark data/synthetic/recourse-assessment/baseline tmp/recourse-review-pack
python -m unittest discover -s tests -p "test_*.py"
```

## Important Limits

This repository uses synthetic demonstration data. It does not claim production
deployment, lender adoption, regulatory approval, independent recognition, or
legal compliance certification.

Fair-lending outputs are screening triggers for governance review, not legal
conclusions. Adverse-action reason QA outputs are review checks, not legal
advice. Recourse outputs are synthetic reviewer assessments under declared
action sets, not applicant instructions, real-world feasibility findings, or
future-outcome guarantees.
