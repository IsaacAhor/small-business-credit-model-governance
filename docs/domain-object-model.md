# Domain Object Model

## Purpose

This document defines the core domain objects that the governance evidence engine should use. These objects are conceptual anchors for later schemas, validation models, and workflow code.

## Core Objects

### Model Registry Record

Represents the durable identity of a governed model.

Key fields:

- model_id
- model_name
- business_owner
- technical_owner
- intended_use
- target_population
- status

### Model Version Record

Represents a specific governed version of a model.

Key fields:

- model_id
- version_id
- effective_date
- change_summary
- assumptions
- limitations
- linked_validation_record

### Model Risk Profile

Represents a risk-based assessment of a model version and the rigor expected of
its validation and monitoring. It is a governance assessment, not a regulatory
classification.

Key fields:

- risk_profile_id
- model_id
- version_id
- inherent_risk
- model_exposure
- model_materiality
- aggregate_dependencies
- validation_rigor
- monitoring_rigor

### Explainability Method Record

Represents a governed explanation method and the assumptions and population
boundary under which reviewers may use it.

Key fields:

- explainability_method_id
- model_id
- version_id
- method_family
- use_cases
- reference_population
- correlation_assumptions
- directionality_review
- known_limitations
- status

### Model Validation Record

Represents the scope, independence, evidence, findings, disposition, and
promotion status of a version-specific validation review. A developer
self-review cannot establish independent approval.

Key fields:

- validation_id
- model_id
- version_id
- validation_scope
- independence_status
- evidence_references
- explainability_method_ids
- findings
- overall_disposition
- promotion_allowed

### Model Monitoring Plan

Represents the risk-based protocol connecting a model version to its risk
profile, validation, explainability methods, thresholds, metrics, limitations,
change triggers, and owners.

Key fields:

- monitoring_plan_id
- model_id
- version_id
- risk_profile_id
- validation_id
- threshold_set_id
- explainability_method_ids
- metrics
- change_triggers
- reason_monitoring_scope

### Threshold Set

Represents the configured monitoring thresholds for a given version or review context.

Key fields:

- threshold_set_id
- model_id
- version_id
- metric_name
- comparison_rule
- threshold_value
- severity
- escalation_owner

### Application Decision Record

Represents a monitored underwriting decision or decision candidate.

Key fields:

- decision_id
- application_date
- segment
- score
- decision_outcome
- manual_review_flag
- override_flag

### Score Output

Represents scored output details separate from the broader decision record when needed.

Key fields:

- decision_id
- score_value
- score_band
- score_version

### Reason-Code Mapping

Represents how explanation outputs or drivers map into governed reason categories.

Key fields:

- mapping_id
- version_id
- driver_or_signal
- reason_code
- reason_text
- mapping_version

### Adverse-Action Reason Output

Represents a generated reason output tied to a monitored adverse decision.

Key fields:

- reason_output_id
- decision_id
- version_id
- reason_code
- driver_or_signal
- reason_rank
- mapping_version

### Fair-Lending Screening Config

Represents configured comparison groups and screening thresholds for governance review.

Key fields:

- screening_config_id
- model_id
- version_id
- comparison_groups
- screens

### Override Event

Represents a manual or policy override linked to a decision.

Key fields:

- override_id
- decision_id
- override_type
- override_reason
- reviewer
- override_date

### Outcome Record

Represents a later outcome used for monitoring or validation when available.

Key fields:

- outcome_id
- decision_id
- observation_period
- repayment_or_default_indicator
- realized_outcome_value

### Breach Record

Represents a threshold breach produced by the workflow.

Key fields:

- breach_id
- run_id
- metric_name
- observed_value
- threshold_value
- severity
- owner

### Issue Record

Represents a remediation or governance issue generated from one or more breaches.

Key fields:

- issue_id
- linked_breach_ids
- summary
- status
- owner
- due_date

### Evidence Pack Manifest

Represents the generated bundle of outputs for a run.

Key fields:

- run_id
- created_at
- model_id
- version_id
- input_references
- output_files
- reviewer_status

## Object Relationships

- one model registry record can have many model version records
- one model version can reference one or more threshold sets
- one model version can have a risk profile whose materiality determines the
  minimum validation and monitoring rigor
- one model version can have one or more governed explainability method records
- one model validation record covers the governed explainability methods for a
  version and records reviewer independence, findings, and promotion posture
- one monitoring plan links the risk profile, validation, explainability
  methods, and threshold set for the same model version
- one monitoring run can process many application decision records
- one decision record can be linked to zero or more override events
- one decision record can reference zero or more adverse-action reason outputs
- one adverse-action reason output should be reviewable against a governed reason-code mapping
- one monitoring run can apply one fair-lending screening config
- one fair-lending screening finding can generate one governance issue record
- one run can create many breach records
- one issue record can group one or more related breaches
- one evidence pack manifest should reference the main records and outputs produced by a run

## Modeling Rule

Objects should stay narrow, explicit, and reviewable. If a field mixes business meaning with monitoring-only meaning, separate it. If an output could be mistaken for a legal conclusion, label it as screening or governance review instead.
