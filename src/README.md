# Source

This directory now holds the first reusable code modules for the governance
evidence engine.

Current contents:

- `credit_gov/schemas/`
  Typed validation models and dataset-validation logic for governed records.
- `credit_gov/monitoring.py`
  Monthly monitoring workflow, metric computation, threshold comparison,
  reason-code QA, fair-lending screening, issue generation, and evidence-pack
  assembly.
- `credit_gov/validation.py`
  Phase 5 model-change and validation review: model-version, threshold-set, and
  reason-code mapping diffs, a change-impact summary with derived review actions,
  and a reviewer signoff record tied to a version and evidence pack. Runs as an
  optional monitoring step and via `scripts/run_change_validation.py`.
- `credit_gov/governance_review.py`
  Formal risk/materiality, explainability-method, validation-independence, and
  monitoring-plan review with deterministic summary and manifest outputs.
- `credit_gov/vendor_risk.py` and `credit_gov/vendor_reporting.py`
  Vendor-contract validation, cross-record and evidence checks, and
  deterministic vendor-oversight reporting for synthetic review scenarios.
- `credit_gov/cli.py`
  Command-line entry point for validating deterministic synthetic inputs.

Possible future modules include additional drift, regression-control, and
reporting utilities where a documented core use case supports them.

Code added here should remain tightly aligned to the repository's stated scope.
Utilities that affect metrics, thresholds, explanation outputs, or fairness
screening should have a linked validation note or test.
