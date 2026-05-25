# Small Business Credit Model Governance

This repository is the working home for a lightweight but defensible model-governance framework for small-business credit decisioning.

The immediate goal is to make it easy to:

- document the model and its intended use
- track data, assumptions, thresholds, and changes
- capture validation evidence and review outcomes
- support internal review, audit readiness, and future regulatory expansion

## Scope

This repo is currently scaffolded as a governance-first repository. It is set up to support:

- policy and control documentation
- model inventory and version tracking
- validation and monitoring artifacts
- implementation work once code and data assets are added

It does not yet assume a specific modeling stack. That is deliberate.

## Initial Repository Layout

```text
.github/
  ISSUE_TEMPLATE/
  workflows/
docs/
governance/
README.md
CONTRIBUTING.md
```

## Working Approach

Use this repository to separate governance evidence from future implementation details:

- `docs/` holds project-facing documents such as roadmap and operating notes
- `governance/` holds reusable templates for inventory, validation, and change control
- future code, notebooks, or pipelines can be added later under clearly named directories once the modeling approach is chosen

## Near-Term Priorities

1. Define the model use case, decision boundary, and business owner.
2. Create the first model inventory entry.
3. Define validation criteria before model development expands.
4. Add implementation directories once the technical stack is selected.

## Review Standard

Changes to this repository should be reviewable by someone who needs to answer:

- what changed
- why it changed
- what governance impact it has
- whether validation or monitoring requirements need to be updated

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution expectations and the PR checklist.
