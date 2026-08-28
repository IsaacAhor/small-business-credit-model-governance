# Unreleased: Adverse-Action Traceability Clarification And Recourse Sidecar

Status: Unreleased development line on `main` with additional working-tree
hardening. No tag or release is represented by this note. Package metadata uses
`0.12.0.dev0`; published citation metadata continues to describe the current
`v0.11.0` release.

## Scope

- Clarifies current reader-facing terminology: legacy programmatic `fidelity`
  identifiers mean record-level source-to-notice traceability and
  reconciliation, not unique explanation truth, causality, actionability,
  recourse, or legal sufficiency.
- Adds a separate optional recourse-assessment sidecar with six mirrored JSON
  Schema 2020-12 contracts, typed models, all-or-none bundle validation,
  deterministic finite enumeration, conservative statuses, and explicit
  uncertainty.
- Adds synthetic valid and invalid fixtures, a deterministic eleven-file
  reviewer pack, protected-core hash checks, standalone and installed commands,
  documentation, and focused regression coverage.
- The current working-tree hardening restricts the first provider to one
  baseline-specific subject per bundle, links feature-schema versions,
  constrains the executable withholding rule, and rejects internally or
  bundle-relationally inconsistent output records.

## Compatibility

The change does not rename or repurpose the existing reason-fidelity module,
types, keys, policies, tests, schemas, commands, historical notes, or curated
reason packs. Recourse is absent from the core mandatory schema tuple and
monthly monitoring result. Existing datasets remain valid without a recourse
bundle.

## Limits

The new module is a synthetic reviewer-facing demonstration. It does not show
real-world action-set feasibility, production model access, applicant
usefulness, institution adoption, independent validation, legal compliance,
increased approvals, or improved credit access. A prior review of another
version or layer does not validate this candidate.

## Publication Gate

Assign a final version and replace this note with a versioned release note only
after the exact tree passes source and installed-package tests, repository and
documentation checks, compatibility hash comparison, leakage review, CI, and
the normal release workflow.
