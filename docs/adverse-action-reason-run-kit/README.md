# Adverse-Action Reason Accuracy Run Kit

This folder is the reviewer and operator entry point for the adverse-action
reason accuracy and transparency benchmark.

Use this folder first if you want to understand what to run, what to inspect,
what the benchmark proves, and what it cannot prove. The canonical code, data,
tests, and generated evidence pack remain in their normal repository locations.

Before citing this work, read `LIMITATIONS.md`.

## Plain-English Scope

This run kit demonstrates a repeatable method for checking whether declined
small-business credit decisions have adverse-action reason outputs that are
specific, mapped, traceable to decision drivers, version-controlled, and
reviewable in an evidence pack.

It is a synthetic benchmark. It is not a production notice process, legal
advice, a compliance certification, lender adoption evidence, or proof of real
small-business adverse-action notice accuracy.

## Regulatory Anchor

Verified against primary CFPB materials on 2026-07-26:

- [Current Regulation B 12 CFR 1002.9](https://www.consumerfinance.gov/rules-policy/regulations/1002/9/)
  requires adverse-action notifications to include either specific reasons or
  the right to request specific reasons, subject to the business-credit rules in
  12 CFR 1002.9(a)(3).
- [The official interpretation to 12 CFR 1002.9](https://www.consumerfinance.gov/rules-policy/regulations/1002/interp-9/)
  says disclosed reasons must relate to and accurately describe factors actually
  considered or scored, principal reasons may not be omitted, generic score or
  internal-policy explanations are insufficient, and more than four reasons is
  generally not likely to be helpful.
- [CFPB Circular 2022-03](https://www.consumerfinance.gov/compliance/circulars/circular-2022-03-adverse-action-notification-requirements-in-connection-with-credit-decisions-based-on-complex-algorithms/)
  is useful background for complex algorithms, but this run kit relies on the
  current regulation and official interpretation as its primary anchor.

Do not cite federal ECOA disparate-impact or effects-test liability as current
law for this workstream.

## Where The Pieces Live

| Artifact | Location |
| --- | --- |
| Run command | `scripts/run_adverse_action_reason_benchmark.py` |
| Synthetic benchmark inputs | `data/synthetic/adverse-action-reason-benchmark/` |
| Generated reviewer pack | `examples/evidence-packs/adverse-action-reason-benchmark/` |
| Method note | `docs/adverse-action-reason-accuracy-method.md` |
| Public-data limitation note | `docs/adverse-action-public-data-limitations.md` |
| Private-data field spec | `docs/private-data-spec-adverse-action-reasons.md` |
| Regression test | `tests/test_adverse_action_reason_benchmark.py` |
| Release note | `docs/releases/v0.8.0.md` |

## Prerequisites

Run from the repository root:

```bash
python --version
```

Python 3.10 or newer is recommended. The benchmark uses the repository's
existing standard-library workflow and does not require a private dataset.

## Run The Benchmark

```bash
python scripts/run_adverse_action_reason_benchmark.py --overwrite
```

The command regenerates the curated evidence pack at:

```text
examples/evidence-packs/adverse-action-reason-benchmark/
```

## Validate The Run Kit

```bash
python -m unittest tests.test_adverse_action_reason_benchmark
python scripts/validate_phase1.py data/synthetic/adverse-action-reason-benchmark
python scripts/validate_repository.py
```

## Review The Outputs

Read these files in order:

1. `BENCHMARK_SPEC.md`
2. `EVIDENCE_PACK_REVIEW.md`
3. `examples/evidence-packs/adverse-action-reason-benchmark/README.md`
4. `examples/evidence-packs/adverse-action-reason-benchmark/adverse_action_reason_benchmark_report.md`
5. `examples/evidence-packs/adverse-action-reason-benchmark/adverse_action_reason_benchmark_results.json`
6. `examples/evidence-packs/adverse-action-reason-benchmark/reason_qa_results.json`
7. `LIMITATIONS.md`

## Expected Result

The benchmark should report that expected seeded failure types were observed.
That is success for this synthetic run. The benchmark is deliberately built with
clean cases and controlled defects so the QA workflow has something to catch.

## What Would Make It Real-World Evidence

A real-world validation run would require a private, deidentified
small-business lender, CDFI, or fintech dataset containing declined
applications, actual decision drivers, reason outputs or notice text, mapping
versions, policy thresholds, and reviewer labels. See
`PRIVATE_DATA_REQUIREMENTS.md`.
