# Monthly Monitoring Report

This report is deterministic, synthetic, and intended only for governance workflow demonstration.

- Run ID: `run-2026-07-adverse-action`
- Model ID: `mdl-adverse-reason-benchmark`
- Version ID: `ver-2026-07-adverse-action`
- Total decisions reviewed: 11
- Approval rate: 0.0909
- Decline rate: 0.9091
- Override rate: 0.0909
- Manual review rate: 0.3636

## Adverse-Action Reason QA

- Declined decisions reviewed: 10
- Generated reason outputs reviewed: 15
- QA exception count: 18
- Source-to-notice control status: `ran_synthetic_source_to_rendered_notice_controls`
- Rendered-notice control status: `ran_synthetic_rendered_notice_controls` (1 exception(s))
- Result type: screening only, not a legal conclusion

- dec-0003: missing_reason_code (Declined decision has no generated adverse-action reason output.)
- dec-0004: unmapped_reason_code (Generated reason code is not present in the governed reason-code mapping.)
- dec-0005: generic_reason_text (Mapped reason text is too generic for governance review.)
- dec-0006: driver_mapping_mismatch (Generated reason driver does not match the governed mapping.)
- dec-0007: mapping_version_mismatch (Generated reason mapping version does not match the governed mapping.)
- dec-0010: missing_reason_code (Declined decision has no generated adverse-action reason output.)
- dec-0002: notice_text_mapping_mismatch (Recorded notice text does not match the governed reason text for its mapped driver.)
- dec-0003: principal_driver_omitted (A governed principal source driver is absent from the recorded reason outputs: scoring:cash_flow_stability)
- dec-0004: policy_version_mismatch (Reason output does not pin the underwriting policy version used for the decision.)
- dec-0005: decision_component_mismatch (Reason output component does not match the recorded final decision component.)
- dec-0005: selection_method_version_mismatch (Reason output selection-method identifier or version does not match its decision component.)
- dec-0006: principal_driver_omitted (A governed principal source driver is absent from the recorded reason outputs: automatic_denial:industry_concentration)
- dec-0006: reason_not_in_actual_contributors (Reason output driver is not an adverse source driver for the recorded source component.)
- dec-0007: mapping_effective_date_mismatch (Reason output does not pin the effective date of its governed mapping.)
- dec-0008: source_driver_rank_mismatch (Reason output source-driver rank does not match deterministic source contribution ranking.)
- dec-0008: notice_template_version_mismatch (Reason output does not pin the governed notice-template identifier and version.)
- dec-0009: selection_method_version_mismatch (Reason output selection-method identifier or version does not match its decision component.)
- dec-0002: rendered_notice_text_mismatch (Rendered notice reason text does not match the recorded reason output.)

## Fair-Lending Screening

- Comparison groups reviewed: 2
- Screening rules applied: 3
- Screening finding count: 0
- Inconclusive threshold-observation count: 0
- Finding gate: minimum group size 30; rate screens require significance at alpha 0.05
- Result type: screening only, not a legal conclusion

- No fair-lending screening findings were generated for this run.

### Inconclusive Threshold Observations

- No threshold observations were classified as inconclusive.

## Threshold Breaches

- No threshold breaches were generated for this run.

## Issue Register

- iss-0001: Reason QA exception for dec-0003: missing_reason_code. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0002: Reason QA exception for dec-0004: unmapped_reason_code. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0003: Reason QA exception for dec-0005: generic_reason_text. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0004: Reason QA exception for dec-0006: driver_mapping_mismatch. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0005: Reason QA exception for dec-0007: mapping_version_mismatch. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0006: Reason QA exception for dec-0010: missing_reason_code. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0007: Reason QA exception for dec-0002: notice_text_mapping_mismatch. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0008: Reason QA exception for dec-0003: principal_driver_omitted. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0009: Reason QA exception for dec-0004: policy_version_mismatch. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0010: Reason QA exception for dec-0005: decision_component_mismatch. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0011: Reason QA exception for dec-0005: selection_method_version_mismatch. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0012: Reason QA exception for dec-0006: principal_driver_omitted. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0013: Reason QA exception for dec-0006: reason_not_in_actual_contributors. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0014: Reason QA exception for dec-0007: mapping_effective_date_mismatch. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0015: Reason QA exception for dec-0008: source_driver_rank_mismatch. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0016: Reason QA exception for dec-0008: notice_template_version_mismatch. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0017: Reason QA exception for dec-0009: selection_method_version_mismatch. Owner: Model Risk Governance. Due: 2026-06-30.
- iss-0018: Reason QA exception for dec-0002: rendered_notice_text_mismatch. Owner: Model Risk Governance. Due: 2026-06-30.
