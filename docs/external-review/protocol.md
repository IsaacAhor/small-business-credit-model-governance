# External review protocol

This procedure supports scoped review of model-governance records and
adverse-action reason traceability. Start with a selected
[review packet](README.md), which includes the routine instructions and return
requirements. This document preserves the full shared rules.
The procedure and blank records do not establish that a review has occurred.

## Choose an assignment

Use the [reviewer groups](reviewer-groups.md) to match relevant expertise to
the work: Technical Implementation Reviewers, Credit Governance and
Adverse-Action Reviewers, and Methodology and Evaluation Reviewers. Group
membership and assignment scope are recorded separately.

| Route | Work | Result within the recorded scope |
| --- | --- | --- |
| [Scoped technical review](technical-review.md) | Execute workflows, trace records, and challenge controls | Findings about tested implementation behavior |
| [Credit governance and adverse-action assessment](practitioner-assessment.md) | Inspect artifacts and work through a review task; installation is not required | Assessment of reviewability, practical barriers, and potential usefulness |
| [Methodology and evaluation assessment](methodology-assessment.md) | Assess claims, assumptions, reference answers, and evaluation design; execution is not required | Methods critique and proposed evaluation improvements, without implying verified software behavior |

Each packet includes its assignment, source identity, applicable common
scope and findings rules, essential instructions or prepared evidence, and
response requirements. Consult this protocol and the selected target sheet for
the full reference or to resolve a discrepancy before starting. The reproduction
and challenge sections apply to the technical route. Practitioner and methods
reviewers answer their packet's questions in the same shared report form;
execution records are needed only when execution is separately scoped. A combined assignment
requires separately recorded scopes and effort, plus agreement for an invited
review. Reading a methods
description does not constitute a software execution review.

## Target and common agreement

[Start with the latest release](current.md) for a new voluntary review, then
choose one of its three packets. You do not need a maintainer to assign the
listed tasks. The target sheet is a supporting source and known-issue record.
Record the exact commit; a latest-release link does not change an existing review.
Instructions may be revised separately from software: record the protocol,
brief, and target-sheet revisions as well as the source commit or manifest.
Resolve any identity mismatch before claiming reproduction or assessment of
that source. Prepared outputs must identify their source and whether the
reviewer independently regenerated them.

For a voluntary review, choose and record the questions, included workflows,
exclusions, relevant expertise, deliverables, effort cap and stopping conditions.
Use the packet's listed tasks as the default. For an invited or commissioned
review, agree these terms with the organizer before starting. Record actual
time and unfinished work. Pause at the recorded cap; an extension or retest
needs its own recorded scope and agreement for an invited assignment.
A partial review is a valid outcome with its limits recorded.
Effort estimates are planning assumptions until checked in actual reviews.

Save the packet permalink before starting: on GitHub, press **y**, then copy
the URL. Its companion documents use that revision unless recorded otherwise.
Write directly in the [shared review form](https://github.com/IsaacAhor/small-business-credit-model-governance/issues/new?template=external-review.yml);
the submitted issue is the report. A GitHub account is required and submission
is public. For offline or private work, use the [same report headings](review-record-template.md)
and an agreed private channel. Share only permitted technical content. No maintainer reply is needed
to complete the listed work. Private arrangements, compensation or additional
commissioned work require coordination; they are not implied by an open packet.

Record relevant relationships, compensation, assistance, and implementation
involvement when assessing independence. Any route may be paid or unpaid;
payment must not depend on a favorable conclusion. Affiliation alone does not
establish organizational endorsement. Use a reviewer identifier where public
attribution is not authorized. Accept an equivalent reviewer-authored format.

The default technical assignment covers reproduction, source-to-notice tracing,
and reviewer-designed challenges. Record any narrower scope first. Portfolio
monitoring, vendor oversight, recourse, public-data analysis, and comparison
studies require separate scope. Practitioner and methods tasks cover only the
artifacts, claims, and context recorded in that review.

The controls compare supplied records. Agreement cannot establish that the
drivers faithfully explain a trained model or that real notices are correct.
No route establishes production readiness, institutional adoption, or
legal compliance. Synthetic approvals and signoffs in example outputs are
separate from an actual review conclusion. Practitioner opinion alone does not
establish successful use across institutions or verified software behavior.

## Reproduce and inspect

For the technical route, obtain a fresh checkout or source extraction of the
recorded source. In a checkout, verify its commit. For an archive, record its
origin, acquisition date, SHA-256, and how source identity was checked.
Follow the target sheet's environment, reading, execution, and inspection
instructions. Preserve stdout, stderr, exit codes, elapsed time, outputs,
errors, and assistance. Use fresh output directories and preserve failed runs
before retrying. Do not overwrite curated examples.

Inspect the specified results, manifests, fingerprints, and governance report.
Recompute at least one input and output hash under the documented normalization
policy. Hash agreement verifies integrity under that policy; it does not prove
correctness or authenticity. Record operating system, Python/dependency
versions, setup changes, and whether execution used source or an installed
package. Include these records in **Assessment and evidence** or linked attachments.

Trace one consistent decision and one defective decision through supplied
driver, mapping, recorded reason, rendered notice segment, and assessment.
Record the exact files and record IDs. Explain how the expected result was
established. Generated timestamps and run identifiers can differ between runs;
compare substantive results and explain differences.

## Challenge cases

The reviewer controls case design and conclusions. Before execution, preserve
each case's inputs or delta, hashes, expected result, and independently reasoned
technical basis. Keep dated amendments to expectations. If the intended rule is
ambiguous, record a specification finding and both interpretations.

Cover these families, or explain an omission. Pair defective cases with clean
controls and include at least one additional reviewer-designed scenario.

| Family | Review question |
| --- | --- |
| Consistent chain | Does a valid chain produce an unexpected alarm? |
| Driver coverage | Is an unmapped principal driver visible when a lower-ranked mapped driver can still produce a reason? |
| Lifecycle boundaries | What happens when application and decision dates differ, including activation and retirement boundaries? |
| Record consistency | Are altered reason text, notice text, versions, or component links attributed to the correct affected record? |
| Missing or invalid input | Does the result distinguish rejected input, incomplete execution, and a control that was not assessed? |
| Scope boundary | Are limits clear when records agree but the supplied explanation has not been justified against a model? |

Use the target sheet's case directories and execution interfaces. Preserve
original inputs and controlled deltas. Follow its rules for invalid inputs,
incomplete runs, supplemental checks, and aggregate benchmark interpretation.

Report execution outcome, correct target detection, missed defects, unexpected
alarms, and unassessed controls separately. State denominators for any rates;
do not count rejected inputs or out-of-scope cases as correct detections.
Identify author-derived cases and reproductions of disclosed issues. Neither
is a wholly new reviewer discovery. Preserve failures before remediation and
use fresh variations to assess claims beyond a known regression case.

## Changing the review target

Preserve the recorded baseline and every original review. A changed candidate
needs a separate commit or inspected source manifest and patch hash. Document
what changed, which findings or conclusions may be affected, and the proposed
retest scope. Verify target-specific commands, artifacts, expected results,
and issue status before using a target sheet with another candidate.

Do not transfer an earlier conclusion to changed source automatically. Carry
unresolved findings forward with their original IDs and origins. Known defects
can be corrected while review arrangements proceed; preserving a baseline does
not require delaying fixes. Reviewers may compare that baseline with a corrected
candidate. Reproducing a disclosed issue confirms it without changing its
maintainer origin. Use fresh cases as well as regressions in a scoped retest.

## Findings, response, and verification

Give each finding a stable ID, evidence, expected and observed behavior,
affected scope, consequence, and proposed acceptance condition. Use these
working severities; retain disagreements and their rationale:

| Severity | Meaning within the recorded scope |
| --- | --- |
| Critical | Broad silent failure or invalidation of the central scoped conclusion. |
| High | A material missed defect or incorrect result in a core control. |
| Moderate | A bounded correctness, reproducibility, or reviewability problem with an explicit workable restriction. |
| Low | A local clarity or usability issue without a demonstrated material effect on the scoped result. |

An observation is a finding type and need not receive a defect severity. Zero
new findings is a valid outcome if coverage and limits are documented.

Preserve the reviewer's original conclusion. The maintainer responds
separately: agree, dispute with evidence, or defer with a reason and owner.
Track implementation and verification separately. A correction needs an exact
candidate identity, regression evidence, and a result against the acceptance
condition. State who retested and whether they helped implement the change.
Use `maintainer-verified only` or `not retested` where appropriate; do not imply
independent verification.

The reviewer completes the scoped review by returning the work performed,
omissions, findings, and their own conclusion. Completion does not depend on
the maintainer's response or a later retest. The maintainer records each
finding's disposition separately, including any response still pending.
A completed review does not require a favorable result or mean that unresolved,
disputed, deferred, or accepted-risk findings are fixed.
Neither a review nor a retest requires a new software release or tag.

Use synthetic inputs. Avoid confidential client information and unnecessary
contact or environment identifiers in shared records. Obtain permission for
reviewer attribution and third-party material before sharing. A public summary
must preserve material qualifications, relevant conflicts or compensation,
unresolved findings, and the actual scope of independent work.

For practitioner assessments, report observed task outcomes separately from
opinions about potential usefulness. Document-only comments must be labeled
as such. Findings still need artifact references, consequences, and a proposed
acceptance condition; severity can be omitted for an observation. Maintainer
responses and any follow-up remain separate dated records under these rules.

For methods assessments, distinguish a critique of described methods or supplied
evidence from source inspection, independently executed tests, and proposed
future evaluation. Do not report a proposed comparison or unrun case as a result.
Preserve unsupported claims, adverse findings, omissions, and disagreements.
The same finding, completion, response, permission, and retest rules apply.

## Method references

The distinction between availability, evaluation, and reproduced results is
informed by [ACM's artifact-review policy](https://www.acm.org/publications/policies/artifact-review-and-badging-current).
Reviewer-designed use cases and follow-up are informed by
[rOpenSci's reviewer guide](https://devguide.ropensci.org/softwarereview_reviewer.html).
Representative tasks and observation of completion, errors, and effort are
informed by [NIST's usability-testing guidance](https://www.nist.gov/programs-projects/usability-testing).
These references inform a project-specific procedure. None of these
organizations has evaluated or endorsed the project through this procedure.
