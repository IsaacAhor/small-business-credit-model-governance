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
specific, mapped, source-reconciled to recorded decision drivers,
version-controlled, and reviewable in an evidence pack.

It is a synthetic benchmark. It is not a production notice process, legal
advice, a compliance certification, lender adoption evidence, or proof of real
small-business adverse-action notice accuracy.

## Regulatory Anchor

Verified against current primary CFPB and eCFR materials on 2026-08-12:

- [Current Regulation B 12 CFR 1002.9](https://www.consumerfinance.gov/rules-policy/regulations/1002/9/)
  requires adverse-action notifications to include either specific reasons or
  the right to request specific reasons, subject to the business-credit rules in
  12 CFR 1002.9(a)(3).
- [The official interpretation to 12 CFR 1002.9](https://www.consumerfinance.gov/rules-policy/regulations/1002/interp-9/)
  says disclosed reasons must relate to and accurately describe factors actually
  considered or scored, principal reasons may not be omitted, generic score or
  internal-policy explanations are insufficient, and more than four reasons is
  generally not likely to be helpful.
- [Current eCFR text for 12 CFR 1002.9](https://www.ecfr.gov/current/title-12/chapter-X/part-1002/subpart-A/section-1002.9)
  provides a current regulatory-text cross-check.
- [CFPB Circular 2022-03](https://www.consumerfinance.gov/compliance/circulars/circular-2022-03-adverse-action-notification-requirements-in-connection-with-credit-decisions-based-on-complex-algorithms/)
  is withdrawn CFPB guidance as of May 12, 2025. It may be useful historical
  background for complex-algorithm concerns, but this run kit relies on the
  current regulation and official interpretation as its primary anchor.

Do not cite federal ECOA disparate-impact or effects-test liability as current
law for this workstream.

## Where The Pieces Live

| Artifact | Location |
| --- | --- |
| Run command | `scripts/run_adverse_action_reason_benchmark.py` |
| Synthetic benchmark inputs | `data/synthetic/adverse-action-reason-benchmark/` |
| Generated reviewer pack | `examples/evidence-packs/adverse-action-reason-benchmark/` |
| Method note | `docs/adverse-action-reason-run-kit/METHOD.md` |
| Public-data limitation note | `docs/adverse-action-reason-run-kit/PUBLIC_DATA_LIMITS.md` |
| Private-data field spec | `docs/adverse-action-reason-run-kit/PRIVATE_DATA_SPEC.md` |
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

1. `METHOD.md`
2. `PUBLIC_DATA_LIMITS.md`
3. `PRIVATE_DATA_SPEC.md`
4. `BENCHMARK_SPEC.md`
5. `EVIDENCE_PACK_REVIEW.md`
6. `examples/evidence-packs/adverse-action-reason-benchmark/README.md`
7. `examples/evidence-packs/adverse-action-reason-benchmark/adverse_action_reason_benchmark_report.md`
8. `examples/evidence-packs/adverse-action-reason-benchmark/adverse_action_reason_benchmark_results.json`
9. `examples/evidence-packs/adverse-action-reason-benchmark/reason_qa_results.json`
10. `LIMITATIONS.md`

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

## Source-To-Rendered-Notice Traceability And Reconciliation Controls

The synthetic benchmark now exercises a separate source-to-rendered-notice control
chain. For each declined decision in the benchmark, it records and checks:

1. the final decision component and underwriting policy version;
2. the adverse source drivers and their deterministic synthetic rank;
3. the selected reason's governed mapping identifier, version, and effective date;
4. the separate rendered notice segment, recorded reason output, and governed
   notice-template version; and
5. the reason-selection method identifier and version.

The checks flag missing principal source drivers, output drivers not found in
the recorded final component, rank drift, template or mapping version drift,
and source-to-text mismatches. These are reproducible governance review
triggers, not a semantic readability review, a legal conclusion, or a claim
that the synthetic method is a permitted reason-selection method for a lender.
See `TERMINOLOGY.md` for the narrow compatibility meaning of legacy programmatic
identifiers that contain the word `fidelity`.
