# Start Here

This repository provides methods and executable tools for bounded reliability
assessment of machine-learning-based small-business credit underwriting. Start
with adverse-action reason review and ongoing model-risk oversight, then inspect
the records that document assumptions, findings, and follow-up.

## External review assignments

Open the [latest release](https://github.com/IsaacAhor/small-business-credit-model-governance/releases/latest)
and choose a packet under **Review this release**. The
[packet overview](docs/external-review/README.md) explains the choices:
technical execution, credit governance and adverse-action assessment, or
methodology and evaluation. Each packet contains the exact source, tasks,
materials, limitations and response format. Voluntary reviewers can start
without prior coordination; invited reviews keep their agreed terms.

If a review is already underway, reopen its saved packet and keep the original
source and instruction revisions. These documents do not establish that an
external review has occurred. The tour and commands below are general background;
they do not replace a packet's version-specific assignment.

## Fast Review Path

1. Read the [project brief](PROJECT_BRIEF.md) for the problem, contribution,
   intended users, and current limits.
2. Inspect the [adverse-action reason run kit](docs/adverse-action-reason-run-kit/README.md),
   its [terminology](docs/adverse-action-reason-run-kit/TERMINOLOGY.md), and the
   [known target limitations](docs/external-review/targets/v0.13.0.md#disclosed-target-limitations).
   Follow the supplied driver-to-mapping-to-reason-to-notice chain and its
   exceptions. Distinguish consistency from explanation faithfulness.
3. Read the [model-risk oversight run kit](docs/model-risk-oversight-run-kit/README.md)
   for SBA approved-loan monitoring, out-of-time performance, drift, source
   provenance, and data exclusions. This is the separate public-data path.
4. Inspect the [governance and validation run kit](docs/model-governance-validation-run-kit/README.md)
   and [governance review pack](examples/evidence-packs/model-governance-review/README.md)
   for risk, method assumptions, review status, monitoring plans, and open gaps.
5. Read the [evidence map](docs/evidence-map.md) for artifact-level limits and
   the [NIST AI RMF mapping](docs/ai-rmf-alignment.md) for framework context.
6. Use the [implementation guide](IMPLEMENTATION_GUIDE.md) to assess adaptation
   requirements after reviewing the methods and their limitations.

For additional scope, inspect the [vendor-risk run kit](docs/credit-union-ai-vendor-risk-run-kit/README.md)
and its [synthetic pack](examples/evidence-packs/credit-union-vendor-risk/README.md).
The [monthly portfolio pack](examples/evidence-packs/monthly-portfolio/README.md)
includes supporting significance, proxy-screening, and LDA outputs. The
[recourse run kit](docs/recourse-assessment-run-kit/README.md) is a separate,
optional synthetic assessment; its outputs are not required notice reasons.

## Role-Based Paths

Use [Use Cases](USE_CASES.md) for model-risk, validation, credit policy,
compliance, vendor-management, research, or supporting screening review.
For an external assignment, use the settled [reviewer groups](docs/external-review/reviewer-groups.md):

- Technical Implementation Reviewers
- Credit Governance and Adverse-Action Reviewers
- Methodology and Evaluation Reviewers

Select the packet based on the questions and work to be assessed. A role or title
alone does not establish independent validation of any component.

## What To Run

No execution is required to browse the curated [reason benchmark](examples/evidence-packs/adverse-action-reason-benchmark/README.md),
[governance pack](examples/evidence-packs/model-governance-review/README.md), or
[monthly portfolio pack](examples/evidence-packs/monthly-portfolio/README.md).
Inspecting those outputs is different from independently reproducing them.

For general exploration, use Python 3.10 or later and a Git checkout at the
chosen revision. Follow the [installation instructions](README.md#installation)
and use fresh output directories:

```bash
python scripts/validate_repository.py
python scripts/validate_phase1.py data/synthetic/monthly-demo
python scripts/run_adverse_action_reason_benchmark.py --output-dir review-output/reason-benchmark
python scripts/run_governance_review.py data/synthetic/monthly-demo review-output/governance
python scripts/run_monthly_monitoring.py data/synthetic/monthly-demo --evidence-root review-output/monitoring
```

Keep Windows paths short. Repository validation requires Git metadata at the
current release; the [target setup notes](docs/external-review/targets/v0.13.0.md#technical-source-setup)
provide a scoped archive-compatible sequence. Preserve failed runs before retrying.
The benchmark also writes scratch records under `evidence/`; avoid overwriting
curated examples. For SBA data acquisition, optional dependencies, fixture
validation, and real-data execution, follow the
[SBA run kit](docs/model-risk-oversight-run-kit/README.md).

## Important Limits

The reason benchmark and curated packs use synthetic data. The separate SBA
workflow uses approved-loan public data and cannot assess declined applications,
adverse-action reasons, or protected-class fairness. Each workflow has its own
source, version, assumptions, and coverage limits.

Current reason checks establish only the consistency properties they test; they
do not establish faithful model explanations or accurate live notices. The
[disclosed target limitations](docs/external-review/targets/v0.13.0.md#disclosed-target-limitations)
describe bounded corrections, residual workflow limits and incomplete benchmark
metrics. Content checks do not authorize operational use; a reproducible failure
is still a failing control.

The repository does not establish production deployment, institutional adoption,
regulatory approval, or legal compliance. Supporting fair-lending outputs are
review triggers, and recourse outputs are synthetic assessments under declared
action sets, not applicant instructions or future-outcome guarantees.
