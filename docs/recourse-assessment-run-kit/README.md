# Recourse Assessment Run Kit

## Purpose

This run kit adds a separate, optional reviewer-facing assessment of whether a
configured target prediction is reached by any explicitly declared synthetic
feature state. It standardizes method, action-set, version, uncertainty,
validation, and evidence-pack records around that bounded question.

It does not modify the required adverse-action reason workflow. The controlling
architecture is:

```text
required-reason layer
  recorded decision process -> declared selection convention -> mapping
  -> reason output -> rendered notice segment -> reason QA

recourse sidecar
  decision/model identifiers -> separate synthetic subject -> versioned method
  -> versioned action set -> synthetic prediction provider
  -> separate reviewer assessment and evidence pack
```

There is no path from a recourse result back into reason selection, reason rank,
reason code, mapping, disclosed text, notice template, or notice rendering.

## Quick Start From A Source Checkout

Validate the baseline bundle against the unchanged adverse-action benchmark:

```bash
python scripts/validate_recourse_run_kit.py \
  data/synthetic/adverse-action-reason-benchmark \
  data/synthetic/recourse-assessment/baseline
```

Generate a separate reviewer pack outside both input trees:

```bash
python scripts/build_recourse_evidence_pack.py \
  data/synthetic/adverse-action-reason-benchmark \
  data/synthetic/recourse-assessment/baseline \
  tmp/recourse-review-pack
```

Installed-package commands use the same positional order:

```bash
credit-gov-recourse-validate CORE_DATASET RECOURSE_BUNDLE
credit-gov-recourse-report CORE_DATASET RECOURSE_BUNDLE OUTPUT_DIR
```

The report command refuses an output directory that equals, contains, or sits
inside either input tree. It also rehashes five protected core files after the
assessment and fails if any changed.

The first-release provider accepts exactly one subject per bundle because every
declared candidate state is relative to that subject's recorded baseline. A
later multi-subject provider would require subject-scoped candidates rather than
silently reusing one baseline-specific action set.

## Fixture Matrix

| Fixture | Expected result |
| --- | --- |
| `baseline` | One single-primary-feature path reaches the target; another evaluated feature is unresponsive. |
| `joint-only` | All declared single-primary-feature states are exhausted without a target path; one two-primary-feature state reaches the target. |
| `fixed-under-action-set` | Complete finite enumeration finds no target state and supports only the qualified fixed-under-set label. |
| `bounded-search-inconclusive` | The state limit is reached without a target path; the result is `no_target_path_found_within_search`, never fixed. |
| `unknown-assumption-inconclusive` | An unresolved feasibility assumption forces `inconclusive` and a withheld disposition. |
| `invalid-baseline-mismatch` | Model recomputation conflicts with the recorded baseline outcome and fails closed. |
| `invalid-missing-action-set-version` | The action-set contract omits its version and fails validation. |
| `invalid-cross-layer-field` | A recourse output includes `reason_code` and fails the closed output schema. |

All public records are fictional. They do not represent an applicant, lender,
vendor, underwriting model, deployment, or institutional policy.

## Status Vocabulary

| Status | Minimum support required |
| --- | --- |
| `single_feature_path_identified` | At least one evaluated permitted state with one primary action feature returns the target prediction. |
| `joint_path_only_identified` | The recorded single-primary-feature search is exhaustive, none reaches the target, and an evaluated joint-primary-feature state does. |
| `fixed_under_declared_action_set` | Every declared supported state is exhaustively enumerated under the configured joint bound and none returns the target. |
| `no_target_path_found_within_search` | No evaluated state returns the target, but search is not exhaustive. |
| `inconclusive` | Feasibility, version, method, certificate, or other declared uncertainty prevents a stronger finding. |
| `not_assessed` | The subject is explicitly excluded with a documented reason. |

These labels describe only the configured model query and declared action set.
They do not predict real-world feasibility or future lending outcomes.

## Evidence-Pack Files

The generator produces exactly eleven files:

- `manifest.json`
- `input_fingerprints.json`
- `output_fingerprints.json`
- `recourse_method_snapshot.json`
- `action_set_snapshot.json`
- `review_config_snapshot.json`
- `recourse_assessment_results.json`
- `recourse_qa_results.json`
- `recourse_review_report.md`
- `reviewer_notes.md`
- `reviewer_signoff.md`

The checked-in deterministic example is under
`examples/evidence-packs/recourse-assessment/`.

## What The Run Kit Demonstrates

The implementation demonstrates closed contracts, exact version linkage,
baseline recomputation, explicit full-state candidates, linked-change handling,
bounded and exhaustive status logic, visible uncertainty, deterministic
reporting, bundle-relative output verification, and protected-core hash
stability.

It does not demonstrate action-set realism, causal feasibility, production
model access, applicant usefulness, institutional adoption, independent
validation, legal compliance, increased approvals, or improved credit access.
See `LIMITATIONS.md` before interpreting any result.
