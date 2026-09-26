# Technical review record template

Use for the [scoped technical route](technical-review.md) under the
[shared procedure](protocol.md). Practitioner-only assessments use the short
response in the [practitioner brief](practitioner-assessment.md). This is a blank
record, not a completed review or approval. An equivalent reviewer-authored
format is welcome. Keep original conclusions and later responses separately
identifiable. Include only information authorized for the intended recipients.

Reviewers complete the assignment, execution, findings, conclusion, and sharing
sections. The maintainer adds responses separately. Complete verification and
disposition only when the corresponding follow-up occurs; they may remain
pending when the reviewer returns the review.

## Assignment and provenance

- Review identifier and dates:
- Protocol, assignment brief, and target-sheet URLs and exact revisions:
- Software commit, version, and tree or source manifest:
- Archive origin, SHA-256, and source-identity verification, if applicable:
- Review question, included workflows, exclusions, and agreed deliverables:
- Agreed effort cap, stopping conditions, and separately agreed retest scope:
- Reviewer identifier and relevant expertise:
- Personal or organizational capacity, where authorized:
- Material relationships, compensation, assistance, and implementation
  involvement affecting independence; limits on the conclusions supported:
- Who designed cases, ran commands, and assessed results:
- Actual effort, scope changes, and reasons:

Use a reviewer identifier where public attribution has not been authorized.
Do not include unnecessary contact details or confidential contractual terms.
Do not claim independence without enough information to assess it.

## Materials and execution

| Material or workflow | Revision/hash and relevant record IDs | Action performed | Omitted or unavailable scope |
| --- | --- | --- | --- |
| [complete] | [complete] | [read / inspected output / executed / challenged] | [complete] |

Operating system, Python/dependency versions, setup, and relevant constraints:

| Run ID | Command | Input/configuration hashes | Exit code, elapsed time, assistance | Output reference/hash and outcome |
| --- | --- | --- | --- | --- |
| [complete] | [complete] | [complete] | [complete] | [complete / failed / not run; details] |

Consistent-decision trace: driver -> mapping -> reason -> notice -> assessment:

Defective-decision trace and correct target finding:

Integrity check: selected input/output, normalization policy, calculated and
recorded hashes, and result:

Explain what successful execution and seeded-type coverage establish, and
what remains unassessed:

## Expectations fixed before execution

Preserve this table's date/hash before running the cases. Record later
amendments and reasons without replacing the original expectations.

| Case ID / family | Designer and origin | Input or delta hash / target IDs | Expected result and technical basis | Date |
| --- | --- | --- | --- | --- |
| [complete] | [reviewer-designed / author-derived / disclosed-issue reproduction] | [complete] | [complete; explain any disputed rule] | [complete] |

Additional reviewer-designed scenario, clean controls, omitted families and
reasons:

## Observations after execution

| Case / run ID | Input validity and execution | Findings for target records | Comparison with expectation | Misses / unexpected alarms / not assessed |
| --- | --- | --- | --- | --- |
| [complete] | [complete] | [IDs and references] | [pass / fail / inconclusive / not tested / not applicable, with reason] | [complete] |

Counts and denominators, if reporting rates:

Disclosed issues reproduced, new findings, and untested assumptions:

## Reviewer findings and conclusion

Repeat for each finding; zero new findings is permitted.

- Finding ID, title, date, and origin:
- Type: defect / specification ambiguity / limitation / observation:
- Severity: Critical / High / Moderate / Low, or not applicable:
- Affected claim, candidate, workflow, files, and record IDs:
- Reproduction steps and input/output references:
- Expected versus observed behavior and technical basis:
- Consequence, scope, uncertainty, and any use restriction:
- Proposed acceptance condition:

Reviewer conclusion in the reviewer's own words:

What worked, what failed, what was not tested, and conclusions not supported:

Review status: completed within scope / partial / blocked / withdrawn;
date and explanation:

Reviewer confirmation that this accurately describes the work performed:

## Maintainer response

Preserve the original review. Add dated responses without rewriting its
findings, severity assessments, or conclusion.

| Finding ID | Response and evidence | Owner / target date | Implementation status | Exact correction and regression reference | Residual limitation |
| --- | --- | --- | --- | --- | --- |
| [complete] | [agree / dispute / defer; rationale] | [complete] | [open / planned / implemented / deferred / disputed] | [reference or none] | [complete] |

Severity disagreements, accepted-risk decisions, and review dates/triggers:

## Verification and disposition

| Finding ID | Exact candidate identity | Verifier, date, implementation involvement | Tests and observed results | Verification status | Acceptance condition met? |
| --- | --- | --- | --- | --- | --- |
| [complete] | [commit or source manifest plus patch hash] | [complete] | [references] | [not retested / maintainer-verified only / independently verified / retest failed / inconclusive] | [result and remaining gap] |

Closure decision and supporting evidence, or unresolved disposition:

Remaining limitations, failed retests, and scope of any independent verification:

## Sharing and attribution

Intended recipients or destination and approved scope of sharing:

Authorized reviewer attribution and third-party material, if any:

Material qualifications, conflicts or compensation that must accompany a
shared conclusion:

Permission reference/date and restrictions:

A completed review does not itself grant permission to identify a reviewer,
circulate their response, or imply an organization's endorsement. Sharing a
summary must not omit adverse findings or qualifications that change its
meaning. Keep detailed administrative records separate from this technical
record.
