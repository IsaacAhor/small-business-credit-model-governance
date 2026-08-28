# Recourse Assessment Data Contracts

## Bundle Rule

A recourse input bundle is separate from the core monitoring dataset and
contains all five files below. The files are validated as an all-or-none
sidecar; none is added to the core validator's mandatory `SCHEMA_SPECS` tuple.
The first-release provider accepts exactly one subject record per bundle because
its declared action candidates are relative to one baseline.

| Bundle file | Schema | Purpose |
| --- | --- | --- |
| `recourse-subject-records.json` | `recourse-subject-record.schema.json` | Supplies separate ordered synthetic or controlled feature states linked by stable decision/model/version identifiers. |
| `recourse-method-record.json` | `recourse-method-record.schema.json` | Declares the calculation convention, implementation reference, sources, randomness policy, limitations, owner, and status. |
| `recourse-action-set.json` | `recourse-action-set.schema.json` | Versions feature control classes, directions, bounds, complete candidate states, linked changes, constraints, feasibility, and unresolved assumptions. |
| `recourse-review-config.json` | `recourse-review-config.schema.json` | Fixes the subject scope, target, eligible baseline, joint/state limits, fixed-finding rule, withholding rules, audience, and output policy before execution. |
| `synthetic-prediction-model.json` | `synthetic-prediction-model.schema.json` | Defines the transparent deterministic synthetic prediction query. |

Generated assessment records are validated against
`recourse-assessment-output.schema.json` and written as an array to
`recourse_assessment_results.json`.

All six schemas declare JSON Schema draft 2020-12, reject undeclared fields,
use stable identifier patterns, and are mirrored byte-for-byte under
`src/credit_gov/schemas/json/` for installed-package validation.

## Recourse Subject

Required fields include:

- `recourse_subject_id`, `decision_id`, `model_id`, and `version_id`;
- `feature_schema_version`;
- ordered `feature_values`;
- `source_class` and a provenance/deidentification note;
- `assessment_scope`, with an exclusion reason when excluded; and
- `result_type = recourse_input_not_applicant_instruction`.

Public fixtures must use `source_class = synthetic`. The subject file does not
extend `application-decision-record.schema.json` and does not place a feature
vector in the required-reason record. The subject feature-schema version must
match the version declared by the synthetic prediction provider.

## Recourse Method

The method record fixes:

- method identifier and version;
- name, family, implementation reference, and source citations;
- calculation mode;
- target-label interpretation;
- treatment of single-primary-feature actions and linked downstream changes;
- randomness policy and validation references;
- known limitations, owner, and status; and
- `result_type = governed_recourse_method_not_outcome_guarantee`.

The schema recognizes future `sampling` and `external_provider` modes so their
records cannot be silently relabeled, but the first executable provider rejects
those modes.

## Action Set

The action set records model/version scope, population, effective and retired
dates, time horizon, source basis, reviewer status, feature controls, explicit
candidate states, joint constraints, and unresolved assumptions.

Feature control classes are:

- `not_actionable_under_set`
- `directly_actionable`
- `conditionally_actionable`
- `derived_or_downstream`
- `unknown`

Each candidate includes:

- stable `action_id`;
- one or more `primary_action_features`;
- a complete ordered `resulting_feature_state`;
- explicit `from_value` and `to_value` changes;
- `primary` or `linked_downstream` role for every change;
- feasibility status and assumption reference.

Validation requires primary features to match primary changes exactly. Unchanged
features must retain their baseline value in the complete state. Linked changes
must use a downstream or conditional control class.

## Review Configuration

The configuration is fixed before execution and includes:

- run and assessment date;
- model/version, method/version, and action-set/version;
- ordered subject scope;
- target prediction and eligible baseline outcome;
- maximum joint-action size and evaluated-state count;
- optional sample count and seed fields reserved for a future enabled mode;
- fixed-finding rules and the executable first-release
  `withhold_on_inconclusive` rule;
- `audience = reviewer_only`;
- `output_directory_policy = separate_from_all_input_trees`; and
- `result_type = configured_recourse_review_not_applicant_advice`.

## Synthetic Prediction Model

The first provider requires a feature-schema version, ordered feature list,
exactly matching ordered coefficients, intercept, threshold, target and
non-target labels, implementation version, `synthetic_only = true`, and
`result_type = synthetic_prediction_provider_not_underwriting_model`.

Production model loading, serialized artifacts, remote scoring, and vendor
access are outside this contract.

## Assessment Output

Each output records:

- assessment, run, subject, decision, model, method, and action-set identifiers
  and versions;
- canonical input-record fingerprints;
- baseline and target predictions;
- conservative overall status;
- feature-level evaluated and target-reaching counts plus an estimate only when
  defined;
- target-reaching evaluated action IDs;
- search mode, overall and single-feature exhaustive flags, counts, limits, and
  seed when applicable;
- uncertainty, withholding, and limitation references;
- reviewer disposition and `audience = reviewer_only`; and
- `result_type = recourse_assessment_not_reason_not_notice_not_outcome_guarantee`.

Because the schema is closed, these cross-layer fields fail validation instead
of being ignored:

- `reason_code`
- `reason_rank`
- `mapping_id`
- `mapping_version`
- `disclosed_reason_text`
- `notice_template_id`
- `notice_template_version`
- `rendered_reason_text`

Typed validation also rejects internally contradictory status, path,
feature-count, search, uncertainty, withholding, or reviewer-disposition
combinations. When an output fixture is supplied with a bundle, it must match
the exact recomputed assessment rather than merely satisfy the standalone JSON
shape.

## Compatibility Boundary

No recourse field is added to the application-decision, adverse-action reason,
rendered-notice, evidence-pack-manifest, monitoring-run-result, or mandatory
core validation contracts. Existing datasets remain valid when no recourse
bundle is present.
