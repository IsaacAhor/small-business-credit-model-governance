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
- `credit_gov/cli.py`
  Command-line entry point for validating deterministic synthetic inputs.

Possible future modules:

- drift detection helpers
- reporting or checklist generation utilities

Code added here should remain tightly aligned to the repository's stated scope.
Utilities that affect metrics, thresholds, explanation outputs, or fairness
screening should have a linked validation note or test.
