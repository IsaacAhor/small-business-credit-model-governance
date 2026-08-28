# Recourse Assessment Limitations

## Synthetic Demonstration Boundary

The public fixtures use fictional subjects, model values, feature controls,
action candidates, dates, owners, and identifiers. They do not contain real
applicant or lender data and do not represent a production underwriting model,
institutional policy, product eligibility rule, or deployed workflow.

Passing validation means only that the declared records are structurally and
relationally consistent under the implemented contracts.

## Action-Set Relativity

Every result is relative to one named and versioned action set. Feature
actionability can vary by applicant, institution, product, jurisdiction, time
horizon, available resources, policy, and dependency assumptions. A synthetic
action set cannot establish those facts for a real person or institution.

Unknown or unresolved feasibility must remain visible. The first build does not
infer feasibility from model coefficients, attribution ranks, correlation,
domain intuition, or the existence of a target-reaching state.

## No Causal Guarantee

A changed feature state can return a different model prediction without being a
causally attainable or stable real-world intervention. Linked features may have
dependencies not represented in the declared state. The evaluator does not
learn or certify a structural causal model.

## No Outcome Promise

A target-reaching evaluated state means only that the configured synthetic
provider returned the target label. It does not establish that a person can
make the change, preserve the change, afford the change, meet other eligibility
requirements, receive a future approval, or obtain the same result after a
model, policy, data, or product change.

## Search Limits

The first build enumerates only explicit finite action candidates. It does not
solve continuous constraints, search undeclared states, optimize cost, or prove
that the candidate list contains every realistic path.

`fixed_under_declared_action_set` is therefore deliberately narrow: it means
only that every declared supported candidate state was evaluated under the
configured bounds and none returned the target. It is not a universal
immutability finding.

Bounded search without a target returns
`no_target_path_found_within_search`. It cannot return a fixed finding.

The first executable provider accepts one subject per bundle. Supporting
multiple different baselines would require subject-scoped action candidates and
is deferred rather than approximated.

## Method Limits

The finite enumerator is a small standard-library implementation for contract
and governance testing. It is not the official implementation of *Feature
Responsiveness Scores* and does not reproduce every method, estimator,
uncertainty interval, optimization routine, or empirical result in that work.

The first build rejects sampling and external providers. It has no hard
dependency on NumPy, pandas, SciPy, scikit-learn, a solver, or third-party
recourse software.

## Required Reasons Remain Separate

Required adverse-action reasons answer a governed notice question. This
sidecar's results answer a bounded action-set query. A recorded required factor
may be unresponsive under the declared action set, and a responsive feature may
not be a required reason. Neither record overwrites, ranks, suppresses, or
reinterprets the other.

The sidecar does not render applicant language, add a notice segment, determine
legal sufficiency, or certify compliance with Regulation B or any other law.

## Model And Policy Change

A result may become stale when the prediction model, threshold, feature schema,
action set, policy, population, or time horizon changes. Exact identifiers and
versions are therefore mandatory. Stale action-set dates or nonapproved method
states force visible uncertainty.

The first build does not perform robustness testing across future versions.

## Human-Factors Limits

The public implementation has not been tested with actual applicants. It does
not evaluate comprehension, accessibility, language, error handling, complaint
handling, behavioral response, reliance risk, distress, stigma, or whether
presenting recourse information could cause harm.

Applicant-facing use would require a separate gate covering institution-specific
policy, legal review, privacy, security, causal and feasibility review,
model-change robustness, accessibility, language, HCI testing, and operational
support.

## Evidence Limits

Tests, deterministic packs, hashes, and release artifacts can establish
execution, reproducibility, and internal discipline. They do not establish:

- institutional adoption or reliance;
- independent validation or practitioner endorsement;
- production effectiveness or safety;
- regulatory approval or legal compliance;
- increased approvals, credit access, or consumer benefit; or
- broad cross-institutional utility.

Those claims would require independent evidence tied to an exact version of the
artifact and its actual context of use.
