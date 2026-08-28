# Recourse Assessment Method

## Review Question

For a validated subject, model/version, target label, method/version, and
action-set/version, does the transparent synthetic prediction provider return
the target label for any permitted declared feature state within the configured
search bound?

This is a model-query question. It is not a causal claim, applicant instruction,
reason-selection method, legal determination, or future-outcome forecast.

## Public Source Context

The design keeps three source propositions separate:

- [Regulation B, 12 CFR 1002.9](https://www.ecfr.gov/current/title-12/chapter-X/part-1002/section-1002.9)
  and its official interpretations govern adverse-action notice reasons. The
  recourse sidecar does not reinterpret or replace that required-reason layer.
- Cheon, Wernerfelt, Friedler, and Ustun,
  [*Feature Responsiveness Scores: Model-Agnostic Explanations for Recourse*](https://openreview.net/forum?id=W3wEGGKjOc),
  distinguishes feature-attribution importance from responsiveness under an
  action set. This repository cites the research concept but does not claim
  that its small finite enumerator is the authors' official implementation.
- The [CFPB adverse-action notice tech sprint](https://www.consumerfinance.gov/rules-policy/competition-innovation/cfpb-tech-sprints/electronic-disclosures-tech-sprint/)
  records participant interest in information about possible changes. It is not
  treated here as a legal mandate, adoption record, or effectiveness finding.
- The [NIST AI RMF Playbook](https://airc.nist.gov/airmf-resources/playbook/)
  supplies voluntary risk-management context for documentation, explanation
  testing, limitations, monitoring, and role-appropriate transparency. It is
  not a certification checklist.

## First-Release Provider

The executable provider is dependency-free and supports one transparent
deterministic linear-threshold model:

```text
score = intercept + sum(weight[feature] * value[feature])
prediction = target_label when score >= threshold, otherwise non_target_label
```

The provider accepts only complete, ordered feature states. Serialized models,
remote APIs, vendor-model access, production scoring, continuous optimization,
sampling, and external-provider execution are rejected in this build.

## Validation Sequence

Before evaluating a state, the command:

1. resolves the core, recourse, and output paths and rejects source/output
   overlap;
2. validates the core dataset with the unchanged mandatory validator;
3. confirms the five protected core files are present and hashes them;
4. validates all five recourse input files against mirrored JSON Schema 2020-12
   contracts and typed models;
5. confirms subject, decision, model, model-version, method-version,
   action-set-version, config, and prediction-provider relationships;
6. checks that feature order is identical across subject, model, controls, and
   every complete candidate state;
7. confirms each declared change starts at the subject baseline, ends at the
   candidate state, respects its direction, bounds, allowed values, control
   class, and primary-versus-linked role;
8. recomputes the baseline prediction and requires it to match the recorded
   eligible decision outcome; and
9. fails closed before output generation if any check fails.

The recourse module does not call the reason generator, reason-rank logic,
reason mapping, or notice renderer.

## Enumeration And Ordering

Supported candidates are sorted deterministically by:

1. number of primary action features; then
2. stable `action_id`.

This ordering exhausts declared single-primary-feature states before joint
states. The command then applies `maximum_joint_action_size` and
`maximum_evaluated_states` from the review configuration.

A candidate is evaluated only when its feasibility status is
`supported_by_declared_synthetic_assumption`. An `excluded` candidate is outside
the permitted declared set. An `unknown` candidate remains visible as
uncertainty and prevents a stronger finding.

## Linked Downstream Changes

A single-feature result means exactly one **primary** action feature. The same
candidate may contain explicitly linked downstream changes. Those linked values
are not silently held constant and are not reassigned as additional primary
actions; the prediction provider evaluates the complete declared state.

This convention is versioned in the method and action-set records. It does not
establish causal validity for the linked change.

## Feature Responsiveness Estimate

For each feature with at least one evaluated candidate where it is the sole
primary action feature, the first build reports:

```text
responsiveness_estimate =
  target-reaching evaluated single-primary-feature candidates
  divided by
  all evaluated single-primary-feature candidates for that feature
```

The estimate is relative to the declared discrete candidates, target label,
model version, action-set version, and search configuration. It is undefined
when no such candidate was evaluated. Joint-primary-feature candidates do not
contribute to a single-feature estimate.

This repository-specific finite estimate is not presented as the cited
authors' official software implementation or as a population-level causal
quantity.

## Conservative Status Logic

Status is assigned in this order:

1. unresolved action-set, method, version, certificate, or feasibility
   uncertainty forces `inconclusive`;
2. an evaluated single-primary-feature target path permits
   `single_feature_path_identified`;
3. an evaluated joint target path permits `joint_path_only_identified` only
   after every declared supported single-primary-feature candidate was
   evaluated without reaching the target;
4. no target path permits `fixed_under_declared_action_set` only when the
   method is exhaustive, every declared supported state falls inside the joint
   bound, every such state was evaluated, and the fixed-finding rule allows an
   exhaustive finding; and
5. otherwise no target path is reported as
   `no_target_path_found_within_search`.

Sampling cannot support a fixed finding in this build because sampling is not
an enabled provider mode. A future sampling adapter would have to record its
seed, sample count, uncertainty interval, and could not infer fixed status from
zero observed target states.

## Output Integrity

The generator writes to a staging directory under the separate output tree,
validates every recourse output against the closed output schema, writes
deterministic JSON and LF-normalized Markdown, fingerprints declared inputs and
outputs, and atomically places only the eleven named files.

After assessment and again during pack creation, it recomputes SHA-256 hashes
for:

- `application-decision-records.json`
- `adverse-action-driver-contributions.json`
- `reason-code-mappings.json`
- `adverse-action-reason-outputs.json`
- `rendered-adverse-action-notices.json`

Any difference fails the run. The verifier also rejects missing, undeclared, or
hash-mismatched output files.
