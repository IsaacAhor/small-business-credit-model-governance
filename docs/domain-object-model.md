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
- one monitoring run can process many application decision records
- one decision record can be linked to zero or more override events
- one decision record can reference zero or more reason-code mapping outputs
- one run can create many breach records
- one issue record can group one or more related breaches
- one evidence pack manifest should reference the main records and outputs produced by a run

## Modeling Rule

Objects should stay narrow, explicit, and reviewable. If a field mixes business meaning with monitoring-only meaning, separate it. If an output could be mistaken for a legal conclusion, label it as screening or governance review instead.
