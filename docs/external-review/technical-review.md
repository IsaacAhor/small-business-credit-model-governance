# Scoped technical review

Assess whether selected model-governance and adverse-action traceability
controls behave as described. This assignment includes software execution and
reviewer-designed challenges. It covers the agreed workflows, not every part
of the project.

## Agree before starting

- [Select a review target](current.md) and record its exact source and
  instruction revisions, including disclosed unresolved issues.
- Read the [common agreement](protocol.md#target-and-common-agreement), including
  expertise, independence, compensation, source identity, and scope limits.
- Agree deliverables, an effort cap, and a stopping point. No project-specific
  duration has been established from completed external reviews. Record actual
  effort; stop and report unfinished work at the cap.
- Agree any narrower scope explicitly. Retesting is a separate commitment.

The reviewer should be able to execute and inspect Python workflows and assess
credit-model governance or reason traceability. If expertise is split across
reviewers, identify each person's work and conclusion separately.

## Work and return

1. Follow the target sheet's setup, reading list, and commands. Record source
   identity, environment, execution outcomes, errors, and assistance.
2. Apply the procedure's [reproduction and inspection requirements](protocol.md#reproduce-and-inspect):
   inspect the reports, check input/output integrity, and trace a consistent
   decision and a defective decision through their records.
3. Apply the [challenge requirements](protocol.md#challenge-cases): establish
   expectations before execution, pair defects with clean controls, and include
   a fresh reviewer-designed case. Explain any omitted families.
4. Return the [technical review record](review-record-template.md), or an
   equivalent account of materials, results, findings, and your own conclusion.

Distinguish a command that ran, a correctly detected target defect, a missed
defect, an unexpected alarm, and an unassessed control. A reproduced disclosed
defect remains a failing product behavior. Prepared examples and existing tests
do not replace independent case design.

Completion means the agreed work and omissions are recorded. It does not
require a favorable conclusion or correction of every finding. The maintainer
responds separately under the [findings and verification procedure](protocol.md#findings-response-and-verification).
Any later retest identifies the exact candidate, acceptance condition, work
performed, verifier, and implementation involvement. A release or tag is not
required.

These synthetic record checks do not establish model-explanation faithfulness,
real-notice accuracy, institutional adoption, or legal compliance. Sharing a
review or identifying its reviewer requires the permissions in the procedure.
