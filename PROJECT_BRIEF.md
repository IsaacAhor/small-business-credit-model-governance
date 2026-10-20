# Project Brief

## Problem

Reviewers of machine-learning-based small-business credit underwriting need to
trace adverse-action reasons, assess the methods that produced them, and monitor
model behavior over time. Structured records and reproducible checks can support
that work, but record consistency alone does not establish model reliability.

## Project Contribution

This repository develops methods, monitoring protocols, documentation standards,
and Python tools for bounded reliability assessment, focused on adverse-action
reason accuracy and traceability and ongoing model-risk oversight.

## What This Repository Demonstrates

- **Reason review:** deterministic selection from supplied driver records,
  governed mappings, reason and notice QA, and traceable exceptions in a
  synthetic benchmark.
- **Ongoing oversight:** an SBA 7(a)/504 approved-loan public-data adapter with
  fixed-horizon outcomes, out-of-time performance review, drift measures,
  source provenance, and input/output fingerprints.
- **Review documentation:** linked risk, explainability-method, validation, and
  monitoring records, with summaries of open findings and review status.
- **Related workflows:** synthetic credit-union vendor oversight, supporting
  fair-lending risk screening, and a separate optional recourse sidecar.

Use [Start Here](START_HERE.md) for the core review sequence. For an assigned
review, keep the software version and instructions in the selected
[review packet](docs/external-review/README.md).

## Current Limitations

- The reason benchmark uses supplied synthetic records. It does not establish
  explanation faithfulness, causal attribution, or live notice accuracy.
- The [v0.13.0 target disclosures](docs/external-review/targets/v0.13.0.md#disclosed-target-limitations)
  identify bounded reason-control corrections, remaining content/authorization
  boundaries, aggregate benchmark limits, and source-archive/Windows constraints.
- SBA data cover approved loans; they cannot evaluate declined applications,
  adverse-action reasons, or protected-class fairness.
- Governance records and reproducible outputs do not independently validate a
  model. No production deployment, institutional adoption, regulatory approval,
  or legal compliance is established by these artifacts.
- Supporting screening findings are review triggers, not legal conclusions;
  optional recourse outputs do not establish real-world feasibility.

## Intended Users

Model-risk and validation teams, credit policy and compliance reviewers,
credit-union vendor-management reviewers, and researchers examining governance
methods. See [role-based use cases](USE_CASES.md) and the
[implementation guide](IMPLEMENTATION_GUIDE.md) for adaptation requirements.
