# Limitations

This run kit is intentionally narrow. It demonstrates a method for adverse-
action reason accuracy review. It does not prove real-world notice accuracy.

## Strongest Truthful Claim

The repository now contains a reproducible synthetic benchmark that exercises
reason generation, reason-code mapping, reason QA, mapping-version checks,
decision-scope checks, and reviewer-ready evidence packaging for adverse-action
reason accuracy and transparency under Regulation B 12 CFR 1002.9.

## What The Benchmark Can Prove

- The repository has executable controls for reason generation and reason QA.
- The synthetic benchmark contains declined decisions, mapped decision drivers,
  reason outputs, and controlled QA failures.
- The benchmark can regenerate a reviewer-ready evidence pack.
- Tests check that expected benchmark failure types are detected.
- The method can specify what a private validation dataset would need.

## What The Benchmark Cannot Prove

- It does not prove any lender's adverse-action notices are accurate.
- It does not prove compliance with Regulation B, ECOA, FCRA, or state law.
- It does not prove institutional adoption, deployment, external validation,
  regulatory approval, market acceptance, or field recognition.
- It does not contain real applicant data, real notices, real credit decisions,
  or real reviewer labels.
- It does not show a live production notice workflow.
- Its source-to-notice check compares exact controlled synthetic reason text;
  it does not determine whether real applicant-facing language is clear,
  accurate in context, or legally sufficient.
- Its deterministic contribution ranking verifies method provenance and test
  behavior only. It does not establish that a real creditor's selection method
  is permitted or substantially similar to the methods described in the
  official interpretation.

## Public Data Boundary

No current public small-business dataset supplies the full proof chain needed
for adverse-action reason accuracy:

- submitted application
- declined action
- actual decision drivers used by the lender
- disclosed adverse-action reasons or notice text
- reason-code mapping version
- review label or ground-truth assessment

SBA, PPP, and CRA data cannot close that gap. They can support public-data
context or other monitoring exercises, but not adverse-action reason accuracy.

HMDA can be used only as an off-domain mortgage reason-code mechanics proxy if a
future run is added. It should not be labeled as small-business credit proof.

CFPB 1071 is useful future small-business application/action context. Until
public 1071 data and its final disclosed fields are available and suitable, it
should not be cited as proof of adverse-action reason accuracy.

## Candor Rules

Do not say:

- "validated on public small-business adverse-action data"
- "demonstrates lender compliance"
- "used by lenders"
- "regulator approved"
- "externally validated"
- "proves fair lending compliance"
- "proves real-world notice accuracy"

Say instead:

- "synthetic adverse-action reason accuracy benchmark"
- "public method demonstration"
- "reviewer-ready example evidence pack"
- "private deidentified lender data is required for real-world validation"

## Evidence Gap Closer

The gap closes only with independent evidence, such as:

- a private deidentified lender, CDFI, or fintech validation run
- a practitioner or counsel review letter that evaluates the method
- a public issue, pull request, replication, or review from a credible external
  model-risk, compliance, credit-policy, or fair-lending practitioner
- a documented pilot that preserves deidentification, provenance, and review
  labels without claiming more than the data supports
