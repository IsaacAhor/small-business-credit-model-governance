# Practitioner assessment

**Packet for Credit Governance and Adverse-Action Reviewers.** Assess whether
the prepared records below help you trace an adverse-action reason, recognize
a governance gap, and decide what to inspect next. No Python installation or
software execution is required. All examples are synthetic and prepared by the
maintainer; inspecting them does not establish independently verified behavior.

If you arrived by browsing the repository, choose a packet from the
[latest release](https://github.com/IsaacAhor/small-business-credit-model-governance/releases/latest)
before starting. If you already received or started this packet, keep its
recorded version and scope.

On this page: [start](#choose-scope-and-start),
[materials](#prepared-review-materials), [tasks](#inspect-and-assess),
[limitations](#known-limitations), and [response](#short-response).

## Choose scope and start

For a voluntary review, use the tasks below, choose and record an effort cap,
and begin. No maintainer agreement is required. Record any narrower scope and
omissions; partial work is welcome. An invited or commissioned review follows
its agreed scope, effort and return method.

Relevant experience includes credit-model risk, underwriting governance,
adverse-action review, or review of credit-model documentation. Fit follows
expertise and the assigned work, not job title or affiliation. The
[shared group definitions](reviewer-groups.md) govern the group names.

- **Software and prepared records:** v0.12.0, commit
  `3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca`;
  tree `8dc6fb0ca99a83846248ad6f239acfed7aec8632`.
- **Instructions:** save this packet's permalink: on GitHub, press **y** and
  copy the resulting URL. Its companion
  protocol and target sheet use the same documentation revision unless
  separately agreed and recorded. These instructions postdate the software
  release and are not in its archive. Resolve any source or instruction
  mismatch before starting; do not switch to a newer version automatically.
- **Scope:** the four tasks below, selected artifacts, and your stated review
  context. Record exclusions, deliverables and your effort cap; an invited
  review uses its agreed terms. Two to four hours is an untested planning allowance for a
  first assessment, not a measured completion time. Narrow scope if needed.
- **Stopping point:** stop at your recorded cap and report actual effort and
  unfinished work. An extension or retest needs a separate recorded scope and
  agreement for an invited assignment. A partial assessment is
  valid. A broader portfolio, vendor, recourse, public-data, or comparison
  assessment needs its own scope.
- **Independence:** record relevant relationships, compensation, assistance,
  implementation involvement, and personal or organizational capacity.
  Payment, if any, must not depend on a favorable conclusion. Affiliation
  alone does not imply organizational endorsement.

The selected evidence is included below. Linked originals and the
[fixed target sheet](targets/v0.12.0.md) are available for deeper inspection
within the effort cap; record any additional materials or help used.

## Prepared review materials

### Project and method

The workflow organizes decision records, supplied adverse drivers, governed
reason mappings, recorded reasons, rendered notice segments, and QA findings.
For the scoring example here, supplied adverse contribution magnitudes are
ranked and mapped to controlled reason codes. The checks compare the records
and their version references. Agreement among records cannot establish that
the supplied drivers faithfully explain a trained model or that a notice is
legally sufficient. Full background: [project brief][project],
[method][method], and [limitations][limits].

### Material A: trace decision dec-0002

This selected excerpt retains the material values needed for the trace task.
It is not the complete dataset. Use the linked source records to inspect
additional fields. In the [decision record][decision], `dec-0002` is declined,
its component is `scoring`, its application date is `2026-07-02`, and its
decision timestamp is `2026-07-02T11:00:00Z`. Its policy is `polver-2026-08`.

| Record or field | First reason | Second reason |
| --- | --- | --- |
| Supplied adverse driver | `cash_flow_stability` | `debt_service_coverage` |
| Supplied contribution magnitude | `0.42` | `0.31` |
| Source component | `scoring` | `scoring` |
| Mapping ID / reason code | `map-101` / `RC-101` | `map-102` / `RC-102` |
| Governed mapping text | Insufficient cash flow stability | Debt service coverage below policy range |
| Reason output ID | `rso-0002-1` | `rso-0002-2` |
| Recorded reason text | Insufficient cash flow stability | Cash flow stability below policy range |
| Recorded reason rank / source-driver rank | `1` / `1` | `2` / `2` |
| Rendered notice text | Insufficient cash flow stability | Debt service coverage below policy range |

Provenance: [supplied drivers][drivers], [mappings][mappings],
[recorded reasons][reasons], and [rendered notice][notices]. Both mappings use
`mapver-2026-07`, effective `2026-07-01`, with no retirement date. Both reason
outputs identify `ranked-adverse-contribution` / `selver-2026-08` and policy
`polver-2026-08`. Notice `aan-0002` and the reason outputs identify template
`aat-small-business-reason` / `tplver-2026-07`; each notice segment references
the reason output ID and code shown above.

The prepared [reason-QA output][qa] reports these two decision-level findings:

| Finding ID | Affected reason output | Comparison reported |
| --- | --- | --- |
| `rex-dec-0002-notice_text_mapping_mismatch` | `rso-0002-2` | Recorded reason text differs from governed mapping text |
| `rex-dec-0002-rendered_notice_text_mismatch` | `rso-0002-2` | Rendered notice text differs from recorded reason text |

The [notice-QA summary][notice-qa] has aggregate counts and types; it does not
identify the decision by itself. This is a disclosed discrepancy, not a blinded
discovery test. Assess the chain and the adequacy of the evidence; disagreement
with an interpretation or proposed control is welcome.

### Material B: governance review gap

The separate [governance report][governance] describes synthetic model
`mdl-smb-credit-xgb`, version `ver-2026-05`. It is a different example from
`dec-0002`; do not join their model or version records.

| Report field | Prepared value |
| --- | --- |
| Independence | `developer_self_review` |
| Reviewer | No independent reviewer assigned |
| Disposition | `pending_independent_review` |
| Promotion allowed | `false` |
| Open validation findings | `2` |
| Explanation method | `xai-ranked-recorded-drivers`; status `draft`, directionality review `pending` |

Its review-gap entries are `independent-validation` and
`open-validation-findings` (both high), and
`explanation-directionality-review` and `explainability-method-approval`
(both moderate). These are prepared governance-record findings, not an
independent assessment by the person reading this packet. The number of open
validation findings and the number of report gap entries are different counts.

### Material C: benchmark context

The prepared [benchmark report][benchmark] covers 11 synthetic decisions,
including 10 declines, with 15 recorded and 14 regenerated reason outputs.
It reports that the expected seeded failure types were observed. That is
aggregate exception-type coverage, not a measured per-record accuracy or
false-alarm rate. The recorded/regenerated difference is intentional in the
seeded suite. It does not make an arbitrary mismatch acceptable.

## Inspect and assess

Work from Materials A-C; use originals where useful and record what you used.
No regeneration is required. The following are the requested tasks:

1. **Trace a reason.** Reconstruct both reason chains in Material A. Identify
   the exact records and comparisons that are consistent or discrepant, any
   missing information, and what the findings do and do not establish.
2. **Assess a review gap.** Select an incomplete or unassessed control in
   Material B. Explain what its status permits you to conclude and what
   remains unknown. Do not treat a synthetic signoff or status as approval.
3. **Specify the next action.** For either task, state what information or
   inspection you would request, who would need to provide it, and what would
   resolve the concern. Supplied records do not prove the underlying model.
4. **Assess practical fit.** In your stated review context, explain where this
   method and evidence structure could help, what is unnecessary or missing,
   implementation barriers, and whether a simpler approach would suffice.

Record navigation difficulty, assistance, actual effort, and incomplete tasks.
Separate observed task performance from opinion about potential usefulness.
No favorable usefulness conclusion is required. Critical, mixed, inconclusive,
or document-only responses are valid when labeled with their actual scope.

## Known limitations

These maintainer-disclosed issues apply to the fixed target. They are not new
reviewer discoveries, and the examples above do not resolve them.

| ID | Issue and implication for this assessment |
| --- | --- |
| KI-01 | Generation can skip an unmapped principal driver while emitting a lower-ranked mapped reason without flagging the omitted driver. A populated reason list is insufficient evidence of coverage. |
| KI-02 | Mapping and template lifecycle checks use application date as decision date. Different dates can hide expiry or wrongly flag a newly active artifact. The same-day example does not assess that boundary. |
| KI-03 | Repository validation requires Git metadata and fails in an extracted archive. This task requires no execution and does not assess portability. |
| KI-04 | Deep Windows paths have caused execution failures; shorter paths were a workaround, not proof of general portability. |
| KI-05 | Benchmark acceptance checks exception-type presence somewhere in the suite, not per-case accuracy or false-alarm performance. |

The first two remain open implementation issues; KI-03 is also open, KI-04 is
environment-dependent, and KI-05 is a metric limitation. The disclosures do
not exhaust possible defects. No conclusion here establishes verified software
behavior, model-explanation faithfulness, real-notice accuracy, effectiveness
across institutions, adoption, production readiness, or legal compliance.

## Short response

**[Write your review][review-form].** Complete the shared form directly; the
submitted issue is your report. Confirm its prefilled software identity, paste
your saved packet permalink, and select your reviewer group. Keep the version
you actually reviewed even if a newer release is available.

In **Assessment and evidence**, answer the tasks above: the reason trace,
governance gap and next action, and practical fit/barriers. Identify the
artifacts and record IDs you examined, task completion, difficulty and help
needed. Distinguish inspection of prepared outputs from any independent
execution, and observed outcomes from opinions about potential usefulness.

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

[project]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/PROJECT_BRIEF.md
[method]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/docs/adverse-action-reason-run-kit/METHOD.md
[limits]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/docs/adverse-action-reason-run-kit/LIMITATIONS.md
[decision]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/data/synthetic/adverse-action-reason-benchmark/application-decision-records.json
[drivers]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/data/synthetic/adverse-action-reason-benchmark/adverse-action-driver-contributions.json
[mappings]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/data/synthetic/adverse-action-reason-benchmark/reason-code-mappings.json
[reasons]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/data/synthetic/adverse-action-reason-benchmark/adverse-action-reason-outputs.json
[notices]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/data/synthetic/adverse-action-reason-benchmark/rendered-adverse-action-notices.json
[qa]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/examples/evidence-packs/adverse-action-reason-benchmark/reason_qa_results.json
[notice-qa]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/examples/evidence-packs/adverse-action-reason-benchmark/rendered_notice_qa_results.json
[governance]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/examples/evidence-packs/model-governance-review/governance-review-report.md
[benchmark]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/examples/evidence-packs/adverse-action-reason-benchmark/adverse_action_reason_benchmark_report.md
