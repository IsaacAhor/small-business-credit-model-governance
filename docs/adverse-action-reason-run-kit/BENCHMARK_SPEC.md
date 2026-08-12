# Benchmark Specification

The benchmark is a synthetic small-business credit dataset designed to test
adverse-action reason generation and reason QA mechanics.

Canonical input folder:

```text
data/synthetic/adverse-action-reason-benchmark/
```

Generated evidence-pack folder:

```text
examples/evidence-packs/adverse-action-reason-benchmark/
```

## Input Records

| File | Purpose |
| --- | --- |
| `application-decision-records.json` | Application action and decision context |
| `score-outputs.json` | Model score outputs tied to applications |
| `adverse-action-driver-contributions.json` | Ranked adverse drivers for declined decisions |
| `reason-code-mappings.json` | Governed mapping from drivers to reason codes and text |
| `adverse-action-reason-outputs.json` | Generated or recorded reason outputs to test |
| `reason-fidelity-policy.json` | Synthetic source-to-notice review threshold and policy version |
| `adverse-action-notice-template.json` | Controlled rendered-reason template and version |
| `reason-selection-methods.json` | Component-specific reason-selection methods and versions |
| `model-registry-record.json` | Model record used by the evidence pack |
| `model-version-record.json` | Model version context |
| `threshold-set.json` | Monitoring thresholds |
| `outcome-records.json` | Synthetic repayment/default outcomes for shared workflow compatibility |
| `override-events.json` | Synthetic override activity for shared workflow compatibility |
| `fair-lending-screening-config.json` | Shared monitoring config for the base workflow |
| `evidence-pack-manifest.json` | Evidence-pack manifest input |

## Seeded Conditions

The dataset contains clean declined-decision examples and controlled defects:

- missing reason output for a declined decision
- unmapped reason code
- generic reason text
- driver-to-mapping mismatch
- stale mapping version
- reason output attached to a non-declined decision
- excessive reason count for one declined decision
- credit-report-only placeholder reason
- declined decision with no mapped adverse driver
- recorded output that differs from regenerated output
- principal source driver omitted from recorded reason outputs
- output driver absent from the recorded final decision component
- source-rank, decision-component, policy, mapping-effective-date, template,
  selection-method, and rendered-text provenance drift

## Benchmark Checks

The run script checks:

- declined decisions have reason outputs
- reason outputs are not attached to non-declined decisions
- reason codes exist in the governed mapping table
- reason text is specific enough for benchmark review
- mapped reason text matches the selected driver
- mapping versions match the governed mapping version
- reason counts stay within the benchmark's review threshold
- credit-report-only placeholders are not treated as sufficient explanations
- every declined decision has a mapped adverse driver
- regenerated reason outputs match recorded benchmark expectations
- source drivers and ranks reconcile to the recorded final decision component
- rendered reason text matches the governed mapping and pins a notice template
- mapping, policy, and selection-method versions are pinned to the decision

These checks are review controls, not legal conclusions.

## Successful Run

A successful run is not a clean pass with no issues. A successful run detects
the expected seeded failure types and writes a reviewer-ready evidence pack.

Expected result location:

```text
examples/evidence-packs/adverse-action-reason-benchmark/adverse_action_reason_benchmark_results.json
```

The field `expected_seeded_failures_observed` should be `true`.
