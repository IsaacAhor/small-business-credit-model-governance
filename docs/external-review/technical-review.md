# Scoped technical review

**Packet for Technical Implementation Reviewers.** Assess whether selected
model-governance and adverse-action traceability controls behave as described.
This assignment requires source inspection, software execution, and independent
challenge design. It covers the recorded workflows, not the whole repository.
The data and examples are synthetic; disclosed defects remain part of the target.

If you arrived by browsing the repository, choose a packet from the
[latest release](https://github.com/IsaacAhor/small-business-credit-model-governance/releases/latest)
before starting. If you already received or started this packet, keep its
recorded version and scope.

On this page: [start](#choose-scope-and-start),
[known issues](#known-issues-in-this-target), [setup](#obtain-the-fixed-source),
[reproduction](#reproduce-and-inspect), [challenges](#design-and-run-challenges),
and [write your review](#work-and-return).

## Choose scope and start

For a voluntary review, use the tasks below, choose and record an effort cap,
and begin. No maintainer agreement is required. Record any narrower scope and
omissions; partial work is welcome. An invited or commissioned review follows
its agreed scope, effort and return method.

You should be able to execute and inspect Python workflows and assess credit-model
governance or reason traceability. If expertise is split, identify each person's
assigned work and conclusion. The [reviewer groups](reviewer-groups.md) describe
qualifications; a second role held by one person is not a second independent review.

- **Software:** v0.12.0, commit `3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca`,
  tree `8dc6fb0ca99a83846248ad6f239acfed7aec8632`.
- **Instructions:** save this packet's permalink: on GitHub, press **y** and
  copy the resulting URL. The companion
  protocol and target sheet use that documentation revision unless a different
  revision is explicitly agreed and recorded. The instructions postdate the
  software release and are absent from its archive. Resolve identity mismatches
  before claiming reproduction; a later release does not change this assignment.
- **Scope:** reproduction, source-to-notice tracing, and reviewer-designed
  challenges below. Record the included artifacts, exclusions, deliverables,
  effort cap and stopping point before starting; agree changes to an invited
  assignment with its organizer.
  Portfolio monitoring, vendor oversight, recourse, public-data analysis, and
  comparison studies require separate scope.
- **Effort:** no project-specific duration has been established by completed
  external technical reviews. Record actual time; stop at the recorded cap and
  report unfinished work. A partial review is valid. Any extension or retest
  needs a separate recorded scope and agreement for an invited assignment;
  it is not a requirement for completing this review.
- **Independence:** record relevant relationships, compensation, assistance,
  implementation involvement, and personal or organizational capacity. Payment,
  if any, must not depend on a favorable result. Affiliation is not endorsement.

This packet includes the routine instructions. The [shared protocol](protocol.md)
remains the full reference for agreements, findings, response, retest, and sharing;
the [fixed target sheet](targets/v0.12.0.md) preserves the source-specific record.

## Known issues in this target

These are maintainer-disclosed observations, not external reviewer discoveries.
They do not exhaust possible defects. Assess their consequences and challenge
the intended behavior or severity where justified.

| ID | Behavior or limitation | Required treatment within scope |
| --- | --- | --- |
| KI-01 | Generation skips an unmapped driver; a lower-ranked mapped reason can be emitted without flagging the omitted principal driver. | Open. Exercise mixed mapped/unmapped drivers and establish the coverage rule. |
| KI-02 | Mapping and notice-template lifecycle checks use application date as decision date. Different dates can hide expiry or wrongly flag a newly active artifact. | Open. Test both directions and exact activation/retirement boundaries. |
| KI-03 | Repository validation requires Git metadata and fails in an extracted source archive. | Open. The archive-compatible commands below exclude `scripts/validate_repository.py`. |
| KI-04 | Deep Windows paths have caused execution failures that disappeared with shorter paths. | Environment-dependent. Use a short extraction path and record the constraint; a workaround does not prove portability. |
| KI-05 | Benchmark acceptance checks whether expected exception types appear somewhere, not per-case accuracy or false-alarm performance. | Inspect results for the intended records independently of aggregate success. |

Reproducing a disclosed defect can complete a task while confirming a failing
control. Do not mark the control as passing because the failure was expected.

## Obtain the fixed source

Use a fresh isolated directory with Python 3.10 or later. The scoped commands
were checked with Python 3.13.3; record your actual environment. They use the
source and standard library, not an installed wheel or optional public-data tools.

For a Git checkout, run these commands one at a time from a short parent path:

```text
git clone --no-checkout https://github.com/IsaacAhor/small-business-credit-model-governance.git review-source
cd review-source
git checkout --detach 3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca
git rev-parse HEAD
```

The last result must match the commit above. Alternatively, download the
[fixed source archive][archive], extract it to a short path, and work from its
source root. Record archive origin, acquisition date, SHA-256, and how the
extracted source identity was verified. Resolve uncertainty before claiming
reproduction. Keep these later review instructions available separately.

### Required source inspection

Read these files in the fixed source; the links open that exact revision.
They are source material for implementation review, not a second assignment.

| File | Inspect for |
| --- | --- |
| [PROJECT_BRIEF.md][project] | Intended contribution and scope |
| [METHOD.md][method] | Supplied-driver ranking, mapping, and record reconciliation |
| [LIMITATIONS.md][limits] | Synthetic boundary and claims that the results cannot establish |
| [TERMINOLOGY.md][terminology] | Traceability versus model-explanation faithfulness, actionability, and recourse |
| [EVIDENCE_PACK_REVIEW.md][pack-guide] | Evidence inventory and interpretation; use this packet's fresh-output commands, not the guide's overwrite example |
| [Governance run-kit README][governance-guide] | Risk, validation, monitoring, and promotion records |

In brief, the controls compare supplied decision components and drivers with
governed mappings, recorded reasons, rendered notice segments, and version
references. Consistent records do not prove the drivers faithfully explain a
trained model. Inspect the implementation behind any conclusion about behavior.

## Reproduce and inspect

Run from the fixed source root, one command at a time. Preserve stdout, stderr,
exit codes, elapsed time, errors, outputs, and assistance. Record OS, Python and
dependency versions, setup changes, and source versus installed-package execution.
Use fresh output directories; preserve failed runs before retrying. Do not
overwrite curated examples.

```text
python --version
python scripts/validate_phase1.py data/synthetic/adverse-action-reason-benchmark
python -m unittest discover -s tests -p test_phase3_reason_qa.py
python -m unittest discover -s tests -p test_adverse_action_reason_benchmark.py
python scripts/run_adverse_action_reason_benchmark.py --output-dir review-output/reason-benchmark
python scripts/run_governance_review.py data/synthetic/monthly-demo review-output/governance
```

The two test files contain six tests at this source commit. The benchmark also
writes scratch records under `evidence/` in the isolated source directory.
These scoped commands do not evaluate all project functions.

### Expected observations and inspection

The prepared baseline benchmark covers 11 decisions, 10 declined decisions,
15 recorded reason outputs, and 14 regenerated outputs. Expected seeded
exception types are present. This is a reproduction reference, not a statement
that the controls are correct. Compare substantive results and explain differences;
generated timestamps and run identifiers can differ.

Inspect these files in `review-output/reason-benchmark/`:

- `adverse_action_reason_benchmark_report.md` and
  `adverse_action_reason_benchmark_results.json`: reported counts, seeded
  conditions, aggregate coverage, and missing expected exception types.
- `reason_qa_results.json`: decision-level exceptions. The separate
  `rendered_notice_qa_results.json` contains an aggregate notice-QA summary;
  it cannot identify the affected decision on its own.
- `manifest.json`, `input_fingerprints.json`, and `output_fingerprints.json`:
  provenance, expected files, and integrity records.

Inspect `review-output/governance/governance-review-report.md` for open findings,
limitations, and promotion posture. The prepared example reports
`developer_self_review`, `pending_independent_review`, promotion `false`, and
two open validation findings. Its synthetic approvals or signoffs do not
establish an actual independent assessment or permission to deploy.

Recompute at least one input and one output SHA-256. For an input, normalize
CRLF to LF, then remaining CR to LF, and compare with its entry in
`input_fingerprints.json`. Hash output file bytes without normalization and
compare with `output_fingerprints.json`; the fingerprint file itself is excluded.
The implementation is in [monitoring.py][monitoring]. Record files, procedure,
expected hashes, and observed hashes. Integrity is not correctness or authenticity.

Trace one consistent decision and one defective decision through supplied
driver, mapping, recorded reason, rendered notice segment, and QA assessment.
Use source files under `data/synthetic/adverse-action-reason-benchmark/`:
`application-decision-records.json`, `adverse-action-driver-contributions.json`,
`reason-code-mappings.json`, `adverse-action-reason-outputs.json`, and
`rendered-adverse-action-notices.json`. Record exact IDs and establish the
expected result independently. The disclosed defective example `dec-0002`
includes `rso-0002-2` with recorded reason text inconsistent with its mapping
and rendered notice. It is a starting reference, not a fresh challenge case.

## Design and run challenges

Before execution, preserve each case's input files or controlled delta, hashes,
expected outcome, and independently reasoned technical basis. Date amendments
to expectations. If the intended rule is ambiguous, record a specification
finding and both interpretations. You control case design and conclusions.

Cover each family below or explain its omission. Pair defects with clean
controls and include at least one additional reviewer-designed scenario.

| Family | Question to test |
| --- | --- |
| Consistent chain | Does a valid chain produce an unexpected alarm? |
| Driver coverage | Is an unmapped principal driver visible when a lower-ranked mapped driver can still produce a reason? |
| Lifecycle boundaries | What happens when application and decision dates differ, including activation and retirement boundaries? |
| Record consistency | Are altered reason text, notice text, versions, or component links attributed to the correct affected record? |
| Missing or invalid input | Are rejected input, incomplete execution, and an unassessed control distinguished? |
| Scope boundary | Are limits clear when records agree but the supplied explanation has not been justified against a model? |

Copy the relevant synthetic dataset to a new directory under `review-inputs/`
inside the isolated source root. Keep the original and record every controlled
change. For a dataset at `review-inputs/case-001`, use:

```text
python scripts/validate_phase1.py review-inputs/case-001
python scripts/run_monthly_monitoring.py review-inputs/case-001 --evidence-root review-output/case-001
python scripts/run_adverse_action_reason_benchmark.py review-inputs/case-001 --output-dir review-output/case-001-benchmark
```

Preserve validation errors and run later stages only where meaningful. The
monthly command reports its generated directory. The benchmark adds supplemental
checks but retains the curated suite's fixed expectation of 20 exception types.
A clean or small custom case can return exit code 1 because it lacks that entire
suite. Inspect `missing_expected_exception_types` and the target record's findings;
distinguish incomplete aggregate coverage from an execution failure. Aggregate
success does not prove detection of the intended defect.

Report execution outcome, correct target detection, missed defects, unexpected
alarms, and unassessed controls separately. State denominators for rates; rejected
inputs and out-of-scope cases are not correct detections. Label author-derived
cases and disclosed-issue reproductions. Neither is a wholly new reviewer
discovery. Preserve failures before remediation and use fresh variations beyond
known regression cases.

## Work and return

**[Write your review][review-form].** Complete the shared form directly; the
submitted issue is your report. Confirm its prefilled software identity, paste
your saved packet permalink, and select your reviewer group. Keep the version
you actually reviewed even if a newer release is available.

In **Assessment and evidence**, include the execution record, consistent and
defective traces, input/output integrity checks and challenge results from the
tasks above. Preserve commands, environment, exit codes, elapsed time, logs,
original inputs and controlled deltas/hashes, dated expectations and technical
basis, observations, clean controls and the additional reviewer-designed case.
Distinguish correct target detection, missed defects, unexpected alarms and
unassessed controls; give denominators for rates and explain omitted work.
Link or attach supporting evidence with run/case IDs. Archive users also record
origin, acquisition date, SHA-256 and source-identity verification.

Use **Findings** for evidence-backed observations or defects and **Conclusion
and limitations** for your own assessment, omissions and completion status.
Record reviewer context and sharing permissions in the form. Partial, negative
and inconclusive reviews are valid; completing a review does not depend on a
maintainer reply, corrected findings or a later retest.

Submission requires a GitHub account and creates a public issue. Save its URL.
For private or offline work, use the [same report headings](review-record-template.md)
and an agreed private channel. This is an alternative way to write the same
report; no second report or pull request is required. Share only permitted
material and exclude confidential client information and unnecessary details.

The maintainer preserves your original conclusion and records responses
separately. Retests identify the changed source, scope, acceptance conditions,
verifier and implementation involvement, with separate agreement for invited
work. Earlier conclusions do not transfer automatically. Neither review nor
retest requires a release or tag. Full [response, sharing and retest rules](protocol.md#findings-response-and-verification)
remain applicable.

[review-form]: https://github.com/IsaacAhor/small-business-credit-model-governance/issues/new?template=external-review.yml&source=v0.12.0+%2F+3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca

[archive]: https://github.com/IsaacAhor/small-business-credit-model-governance/archive/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca.zip
[project]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/PROJECT_BRIEF.md
[method]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/docs/adverse-action-reason-run-kit/METHOD.md
[limits]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/docs/adverse-action-reason-run-kit/LIMITATIONS.md
[terminology]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/docs/adverse-action-reason-run-kit/TERMINOLOGY.md
[pack-guide]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/docs/adverse-action-reason-run-kit/EVIDENCE_PACK_REVIEW.md
[governance-guide]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/docs/model-governance-validation-run-kit/README.md
[monitoring]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/src/credit_gov/monitoring.py
