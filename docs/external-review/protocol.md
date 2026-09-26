# External technical review protocol

This procedure supports a scoped review of model-governance records and
adverse-action reason traceability. It asks a reviewer to run the software,
trace results to inputs, challenge controls, and report limitations. The
procedure and its blank record do not establish that an external review has
occurred.

## Review target and scope

The initial target is the existing **v0.12.0** source snapshot:

- Commit: `3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca`.
- Tree: `8dc6fb0ca99a83846248ad6f239acfed7aec8632`.
- [Pinned source](https://github.com/IsaacAhor/small-business-credit-model-governance/tree/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca).
- Data: synthetic demonstration records.

Record the URL and revision of this protocol separately: these instructions
were added after the target software snapshot. A documentation update does
not change that snapshot. A changed software candidate needs its own commit
or source manifest and patch hash; never label it unchanged v0.12.0.

The default assignment covers reproduction, source-to-notice tracing, and
reviewer-designed challenge cases. Agree any narrower scope before work
starts. Portfolio monitoring, vendor oversight, recourse, public-data
analysis, comparison studies, and observed user tasks require separate scope.

The controls compare supplied records. Agreement among those records cannot
establish that the supplied drivers faithfully explain a trained model or
that real notices are correct. This review does not establish production
readiness, institutional adoption, or legal compliance. Synthetic approvals
and signoffs in example outputs are separate from an actual review conclusion.

Use the [technical review record](review-record-template.md), or an equivalent
record in the reviewer's own format. Agree the questions, expertise needed,
effort, deliverables, and completion conditions. Record relevant relationships,
compensation, and assistance when assessing independence. Compensation must
not depend on a favorable conclusion. Affiliation alone is not organizational
endorsement.

## Reproduce and inspect

Use a fresh checkout or source extraction of the pinned commit. Keep Windows
paths short. In a checkout, verify `git rev-parse HEAD`. For an archive, record
its origin, acquisition date, SHA-256, and how its source identity was checked.
Resolve an uncertain source identity before claiming reproduction.

Read these files in that snapshot:

- `PROJECT_BRIEF.md`.
- `docs/adverse-action-reason-run-kit/METHOD.md`.
- `docs/adverse-action-reason-run-kit/LIMITATIONS.md`.
- `docs/adverse-action-reason-run-kit/TERMINOLOGY.md`.
- `docs/adverse-action-reason-run-kit/EVIDENCE_PACK_REVIEW.md`.
- `docs/model-governance-validation-run-kit/README.md`.

Run the following from the source root, one command at a time. Record the
operating system, Python version, commands, exit codes, elapsed time, outputs,
errors, and assistance. These scoped source commands were checked with Python
3.13.3; report the environment actually used. They do not test an installed
wheel. Use fresh output directories and preserve failed runs before retrying.

```text
python --version
python scripts/validate_phase1.py data/synthetic/adverse-action-reason-benchmark
python -m unittest discover -s tests -p test_phase3_reason_qa.py
python -m unittest discover -s tests -p test_adverse_action_reason_benchmark.py
python scripts/run_adverse_action_reason_benchmark.py --output-dir review-output/reason-benchmark
python scripts/run_governance_review.py data/synthetic/monthly-demo review-output/governance
```

The two test files contain six tests at the target commit. The benchmark also
writes scratch records under `evidence/` in the isolated source directory.
Do not overwrite curated examples. `scripts/validate_repository.py` requires
Git metadata at this version and is excluded from this archive-compatible
sequence.

Inspect the benchmark report, `reason_qa_results.json`,
`rendered_notice_qa_results.json`, `manifest.json`, and
`input_fingerprints.json` in `review-output/reason-benchmark/`. Inspect
`review-output/governance/governance-review-report.md` for open findings,
limitations, and promotion posture. Recompute at least one input and output
hash using the documented normalization policy. Hash agreement verifies
integrity under that policy; it does not prove correctness or authenticity.

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

Place synthetic challenge data in a new directory under `review-inputs/` inside
the isolated source root. Preserve the original inputs and controlled changes.
For a dataset at `review-inputs/case-001`, use:

```text
python scripts/validate_phase1.py review-inputs/case-001
python scripts/run_monthly_monitoring.py review-inputs/case-001 --evidence-root review-output/case-001
python scripts/run_adverse_action_reason_benchmark.py review-inputs/case-001 --output-dir review-output/case-001-benchmark
```

Preserve validation errors and run later stages only where meaningful. The
monthly command reports the generated run directory. The benchmark adds
supplemental checks but retains the curated suite's fixed expectation of 20
exception types. A clean or small custom case may return exit code 1 because
it lacks that entire suite. Inspect `missing_expected_exception_types` and
findings for the target decision; distinguish that condition from an execution
failure. Aggregate success is not proof that the target defect was detected.

Report execution outcome, correct target detection, missed defects, unexpected
alarms, and unassessed controls separately. State denominators for any rates;
do not count rejected inputs or out-of-scope cases as correct detections.
Identify author-derived cases and reproductions of disclosed issues. Neither
is a wholly new reviewer discovery. Preserve failures before remediation and
use fresh variations to assess claims beyond a known regression case.

## Disclosed target limitations

These are maintainer observations for the pinned target, not external review
findings. They remain open or limited as described. The reviewer should assess
their consequences and can dispute the intended behavior or severity.

| ID | Behavior or limitation | Review treatment |
| --- | --- | --- |
| KI-01 | Generation skips an unmapped driver. A lower-ranked mapped reason can be emitted without a finding for the omitted principal driver. | Open. Exercise mixed mapped/unmapped cases and define the coverage rule. |
| KI-02 | Mapping and notice-template lifecycle checks use application date as decision date. A later decision can miss expiry or incorrectly flag a newly active artifact. | Open. Test both directions and exact date boundaries. |
| KI-03 | Repository validation requires Git metadata and fails in an extracted source archive. | Open. Distinguish checkout validation from the scoped source commands above. |
| KI-04 | Deep Windows paths have caused execution failures that disappeared with a shorter path. | Environment-dependent. Report setup constraints; a workaround does not establish general portability. |
| KI-05 | Benchmark acceptance checks whether expected exception types appear somewhere, not per-case accuracy or false-alarm performance. | Metric limitation. Inspect record-level outcomes independently. |

Reproducing a known defect can complete a review task while confirming a
failing control. Do not report that control as passing because its failure was
expected. The disclosed issues do not exhaust possible defects.

## Findings, response, and verification

Give each finding a stable ID, evidence, expected and observed behavior,
affected scope, consequence, and proposed acceptance condition. Use these
working severities; retain disagreements and their rationale:

| Severity | Meaning within the agreed scope |
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

A completed review documents the agreed work, omissions, reviewer conclusion,
and disposition of findings. It does not require a favorable result or mean
that unresolved, disputed, deferred, or accepted-risk findings are fixed.
Neither a review nor a retest requires a new software release or tag.

Use synthetic inputs. Avoid confidential client information and unnecessary
contact or environment identifiers in shared records. Obtain permission for
reviewer attribution and third-party material before sharing. A public summary
must preserve material qualifications, relevant conflicts or compensation,
unresolved findings, and the actual scope of independent work.

## Method references

The distinction between availability, evaluation, and reproduced results is
informed by [ACM's artifact-review policy](https://www.acm.org/publications/policies/artifact-review-and-badging-current).
Reviewer-designed use cases and follow-up are informed by
[rOpenSci's reviewer guide](https://devguide.ropensci.org/softwarereview_reviewer.html).
This is a project-specific procedure; neither organization has evaluated or
endorsed the project through this protocol.
