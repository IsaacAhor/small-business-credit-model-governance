# Methodology and evaluation assessment

**Packet for Methodology and Evaluation Reviewers.** Assess whether the
project's proposed record-traceability method and evaluation support its stated
conclusions. This methods-only assignment uses the evidence below and requires
no installation or software execution. It does not establish independently
verified software behavior. All examples are synthetic and maintainer-prepared.

On this page: [agreement](#agree-a-methods-assignment),
[method and evidence](#method-and-evidence-to-assess),
[known limitations](#known-limitations), [questions](#assessment-questions),
and [response](#short-methods-response).

## Agree a methods assignment

Relevant experience includes credit ML, explanation evaluation, statistics,
econometrics, or empirical model-governance research. Academic and applied
research experience can both qualify. Use the
[settled group definitions](reviewer-groups.md); record actual expertise and
scope rather than infer them from a title or institutional affiliation.

- **Source:** v0.12.0, commit `3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca`,
  tree `8dc6fb0ca99a83846248ad6f239acfed7aec8632`.
- **Instructions:** record this packet's commit-pinned URL. Its companion
  protocol and target sheet use the same documentation revision unless
  separately agreed and recorded. These later instructions are absent from
  the software release archive. Resolve identity mismatches before starting;
  do not silently substitute a newer source or packet.
- **Work:** critique the four questions below for the identified claims and
  materials. Agree any narrower selection, context, exclusions, deliverables,
  return method, effort cap, and stopping point before starting. No duration
  has been established from completed external methods reviews.
- **Limits:** stop at the agreed cap and return actual effort, omissions, and
  your conclusion. A partial or inconclusive response is valid. Execution,
  broader comparison studies, public-data analysis, or a retest require an
  additional explicit scope; use the technical packet if execution is added.
- **Independence:** record relationships, compensation, assistance,
  implementation involvement, each participant's work, and personal or
  organizational capacity. Payment must not depend on favorable conclusions;
  affiliation is not organizational endorsement.

The task can be completed using this page. Linked originals are available for
verification or deeper inspection within the cap. Distinguish critique of the
description or excerpts from inspection of full sources or executed behavior.
The [shared protocol](protocol.md) supplies the full common rules; the
[target sheet](targets/v0.12.0.md) preserves source and issue references.

## Method and evidence to assess

### The proposed contribution

The project organizes versioned model-governance records, adverse-action
reason mappings, QA findings, and reproducible evidence packs. The selected
method checks consistency from supplied decision drivers through recorded
reasons to rendered notice segments. Governance records separately describe
validation independence, open findings, explanation-method review, and
promotion posture. The [project brief][project] and [method note][method]
describe the wider context; this assessment remains within the agreed subset.

For the synthetic scoring path, the declared method ranks recorded adverse
contribution magnitude and maps eligible drivers to governed reason codes.
Reasons and notices identify source components, ranks, mapping and policy
versions, selection-method versions, and templates. QA compares those supplied
records and surfaces selected inconsistencies. It does not derive independent
ground truth about the model from which the contributions supposedly came.
Method provenance and record reconciliation are distinct from explanation
faithfulness, causal truth, actionability, and legal sufficiency.

The [method registry][registry] identifies the scoring method as
`ranked-adverse-contribution` / `selver-2026-08`. Judgmental, automatic-decline,
and combined-component paths have separately identified methods. Critiquing
the scoring example does not establish results for the other paths.

### A concrete consistency example

The source's `dec-0002` is a declined scoring decision. Its supplied adverse
driver `debt_service_coverage` has magnitude `0.31`, below
`cash_flow_stability` at `0.42`. For its second reason:

| Record | Prepared value |
| --- | --- |
| Mapping `map-102`, code `RC-102` | Debt service coverage below policy range |
| Recorded reason `rso-0002-2` | Cash flow stability below policy range |
| Notice `aan-0002`, segment for `rso-0002-2` | Debt service coverage below policy range |
| Reason-QA findings for `rso-0002-2` | `notice_text_mapping_mismatch` and `rendered_notice_text_mismatch` |

Sources: [drivers][drivers], [mapping][mapping], [reason][reason],
[notice][notice], and [QA output][qa]. The mapping and rendered notice agree
with each other while the recorded reason differs. This supports a question
about internal consistency. It does not independently establish that debt
service coverage was a principal cause of a real model's adverse decision.
The discrepancy is disclosed; identifying it is not blinded discovery.

### Evaluation evidence and its limits

The prepared [benchmark report][benchmark] has 11 synthetic decisions,
10 declines, 15 recorded reason outputs, and 14 regenerated outputs. The
[benchmark implementation][benchmark-code] defines 20 expected exception types.
Its acceptance criterion checks whether those types occur somewhere in the
curated suite. The report states that expected seeded failure types were
observed. The suite intentionally includes altered records; a recorded versus
regenerated difference alone is not an accuracy estimate.

| Question or claim | Evidence available here | Conclusion not established |
| --- | --- | --- |
| Can selected record inconsistencies be described and checked? | Declared rules, controlled records, and prepared record-level QA findings | Completeness or correctness for every input |
| Does the curated run cover its expected exception types? | Aggregate presence of the 20 types defined by the benchmark | Per-record detection rate, false-alarm rate, or independent validation |
| Are drivers justified as explanations of a model? | Supplied driver magnitudes and a declared ranking/mapping convention | Explanation faithfulness, causal truth, or a uniquely correct principal-reason selection |
| Does the governance output document oversight gaps? | A separate example reports `developer_self_review`, `pending_independent_review`, promotion `false`, and two open validation findings | Completion of independent validation or authority to deploy |
| Is the approach useful across institutions or better than a simpler process? | A reproducible record structure and synthetic examples | Comparative superiority, general usefulness, adoption, or legal compliance |

The separate [governance example][governance] concerns `mdl-smb-credit-xgb`,
version `ver-2026-05`; do not merge its model identity with the reason example.
Its explanation method, `xai-ranked-recorded-drivers`, remains draft with
directionality review pending.
No independent comparative study, validated real-world reference labels, or
external reviewer performance measurements are supplied in this packet.

## Known limitations

These are maintainer disclosures for the fixed source, not reviewer discoveries.
Assess their methodological consequences; do not assume they have been repaired.

| ID | Disclosed limitation |
| --- | --- |
| KI-01 | Open: generation can skip an unmapped principal driver while emitting a lower-ranked mapped reason without flagging the omitted driver. |
| KI-02 | Open: mapping/template lifecycle checks use application date as decision date; different dates can hide expiry or wrongly flag newly active artifacts. |
| KI-03 | Open: repository validation requires Git metadata and fails in an extracted archive; this methods-only assignment does not test execution. |
| KI-04 | Environment-dependent: deep Windows paths have caused failures; a shorter-path workaround does not establish portability. |
| KI-05 | Aggregate exception-type coverage does not measure per-case accuracy or false alarms. |

The disclosed issues do not exhaust possible defects. A methods assessment can
identify unsupported claims and better tests; it does not itself fix code,
verify execution, establish real-notice accuracy, or demonstrate adoption,
production readiness, legal compliance, or effectiveness across institutions.
See the original [limitations][limits] for the wider demonstration boundary.

## Assessment questions

1. **Contribution and assumptions.** Is the proposed traceability contribution
   clearly distinguished from model explanation and legal sufficiency? Identify
   assumptions, missing definitions, and claims that should be narrowed. State
   which source or excerpt supports your assessment.
2. **Reference answers.** Is the basis for expected results independent enough
   of implementation? Identify where a declared convention is reasonable,
   debatable, or insufficient. Explain the consequences of KI-01 and KI-02
   for completeness and time-based validity. A reasoned disagreement is useful.
3. **Evaluation design.** Given KI-05, propose a bounded evaluation with explicit
   units, expected outcomes, clean controls, missed defects, unexpected alarms,
   invalid-input treatment, and denominators. Describe at least one proposed
   defect/clean-control pair and how its expected result would be justified
   before execution. This is a design proposal; do not report unrun results.
4. **Comparison and transfer.** Identify a suitable simpler comparator or
   explain why one is unnecessary. State what evidence would distinguish this
   method's value, what real-world or independent data are missing, and which
   conclusions should remain withheld. Separate proposed future study from
   comparisons actually performed.

You may challenge the tasks or suggest a narrower question. Record omissions,
navigation difficulty, assistance, and actual effort. Favorable conclusions
are not required; keep criticism, uncertainty, and negative findings intact.

## Short methods response

Return dated notes through the agreed return method using these fields or an
equivalent reviewer-authored format. No technical execution record is required
for methods-only work. Use an identifier where naming is not authorized; avoid
confidential client information and unnecessary personal details.

- Review ID/date, reviewer identifier, expertise, and group(s):
- Each participant's work and capacity; relevant relationships, compensation,
  assistance, implementation involvement, and limits on independence:
- Software: v0.12.0 / `3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca`.
  Packet URL/revision and companion instruction revisions if different:
- Agreed question, context, scope, exclusions, deliverables, effort cap,
  actual effort, omissions, and additional work separately agreed:
- Materials actually examined: excerpt / full source / independently executed
  work, with exact references; identify who performed any added execution:

| Question | Evidence and reasoning | Conclusion, uncertainty, or proposed improvement |
| --- | --- | --- |
| Contribution and assumptions | [references] | [assessment] |
| Reference answers | [references] | [assessment] |
| Evaluation design and proposed paired case | [references] | [design; distinguish unrun work] |
| Comparison and transfer | [references] | [assessment; evidence still needed] |

- Findings, if any: stable ID/date, origin, type, affected claim/source/record,
  expected versus observed condition, rationale, consequence, uncertainty,
  and acceptance condition. For defects, Critical means broad silent failure
  or invalidation of the scoped conclusion; High a material core-control miss;
  Moderate a bounded correctness/reproducibility/reviewability problem with a
  workable restriction; Low local clarity/usability without demonstrated
  material effect. Observations need not have severity; retain disagreements.
- Your conclusion: what is supported, unsupported, unexamined, or unresolved:
- Status: completed within scope / partial / blocked / withdrawn; date and
  confirmation that the account accurately describes the work:
- Sharing permission: recipients/destination, attribution or excerpts,
  qualifications, restrictions, and permission date. Leave ungranted permissions
  explicit; a completed assessment does not grant permission to share it.

Completion depends on recording the agreed work and omissions, not a favorable
result, corrected findings, a maintainer response, or retesting. Zero new findings
is valid with scope recorded. The maintainer preserves your original conclusion
and separately agrees, disputes with evidence, or defers findings with a reason
and owner. A changed source or follow-up needs its own agreement, exact identity,
acceptance conditions, verifier, and implementation-involvement record; prior
conclusions do not transfer automatically. Neither review nor retest needs a
release or tag. Shared summaries preserve adverse findings, qualifications,
conflicts/compensation, assistance, and actual scope. Full rules:
[shared procedure](protocol.md#findings-response-and-verification).

[project]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/PROJECT_BRIEF.md
[method]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/docs/adverse-action-reason-run-kit/METHOD.md
[limits]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/docs/adverse-action-reason-run-kit/LIMITATIONS.md
[registry]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/data/synthetic/adverse-action-reason-benchmark/reason-selection-methods.json
[drivers]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/data/synthetic/adverse-action-reason-benchmark/adverse-action-driver-contributions.json
[mapping]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/data/synthetic/adverse-action-reason-benchmark/reason-code-mappings.json
[reason]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/data/synthetic/adverse-action-reason-benchmark/adverse-action-reason-outputs.json
[notice]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/data/synthetic/adverse-action-reason-benchmark/rendered-adverse-action-notices.json
[qa]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/examples/evidence-packs/adverse-action-reason-benchmark/reason_qa_results.json
[benchmark]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/examples/evidence-packs/adverse-action-reason-benchmark/adverse_action_reason_benchmark_report.md
[benchmark-code]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/scripts/run_adverse_action_reason_benchmark.py
[governance]: https://github.com/IsaacAhor/small-business-credit-model-governance/blob/3baafca5b695c6f80d5c84a2c8b4fa184d6f59ca/examples/evidence-packs/model-governance-review/governance-review-report.md
