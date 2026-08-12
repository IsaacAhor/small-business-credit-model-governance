# Evidence Pack Review

This file explains how to inspect the generated adverse-action reason benchmark
evidence pack without reading the implementation first.

Evidence-pack folder:

```text
examples/evidence-packs/adverse-action-reason-benchmark/
```

Regenerate it with:

```bash
python scripts/run_adverse_action_reason_benchmark.py --overwrite
```

## Review Order

1. `README.md`
   Confirms the pack is synthetic and gives the short review sequence.
2. `adverse_action_reason_benchmark_report.md`
   Plain-language benchmark summary.
3. `adverse_action_reason_benchmark_results.json`
   Machine-readable benchmark checks and seeded failure observations.
4. `reason_qa_results.json`
   Standard reason-QA output from the shared monitoring workflow.
5. `issue_register.json`
   Review issues opened by the evidence workflow.
6. `monitoring_report.md`
   Broader monitoring-report context from the shared workflow.
7. `manifest.json`
   Evidence-pack inventory and provenance metadata.
8. `input_fingerprints.json`
   Input hashes for reproducibility review.
9. `reviewer_notes.md` and `reviewer_signoff.md`
   Reviewer-facing notes and signoff template outputs.

## What To Look For

Confirm that:

- the pack states that it is synthetic
- the benchmark result says expected seeded failures were observed
- reason-QA exceptions are traceable to specific applications and reason
  outputs
- source-to-rendered-notice fidelity reports distinguish the final decision
  component, source driver, mapping, recorded reason text, visible notice
  segment, template, policy, and method versions
- reason-code mapping problems are separated from generic monitoring metrics
- the pack does not claim legal compliance, deployment, adoption, or external
  validation
- input fingerprints and manifest files exist for reproducibility

## How To Read Failures

Failures are intentional when they match seeded benchmark conditions. They show
that the workflow can detect missing, stale, unmapped, generic, mismatched, or
out-of-scope reasons.

Unexpected failures should be treated as implementation issues and investigated
before citing the run.

## Citation Discipline

Use the evidence pack as proof of a reproducible synthetic method and reviewer-
ready packaging. Do not use it as proof of real small-business notice accuracy
or Regulation B compliance.
