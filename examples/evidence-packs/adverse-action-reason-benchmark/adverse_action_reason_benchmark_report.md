# Adverse-Action Reason Accuracy Benchmark Report

This report is synthetic governance evidence only. It does not provide legal advice, certify Regulation B compliance, or represent a production notice process.

Benchmark success means expected seeded failure types were detected. It does not establish a passed reason-content review. Operational authorization is not provided.

- Workstream: Adverse-action reason accuracy and transparency under Regulation B 12 CFR 1002.9
- Dataset: `data/synthetic/adverse-action-reason-benchmark`
- Decisions reviewed: 11
- Declined decisions reviewed: 10
- Recorded reason outputs: 15
- Regenerated reason outputs: 14
- Expected seeded failure types observed: True

## Monitoring Reason QA Exceptions

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
- dec-0010: principal_driver_unmapped (A principal source driver within the configured review limit has no governed mapping: scoring:external_vendor_watchlist_signal)
- dec-0010: principal_driver_omitted (A governed principal source driver is absent from the recorded reason outputs: scoring:external_vendor_watchlist_signal)
- dec-0002: rendered_notice_text_mismatch (Rendered notice reason text does not match the recorded reason output.)

## Supplemental Benchmark Exceptions

- non_declined_reason_output: Reason output is attached to a decision that was not declined.
- credit_report_only_placeholder: Mapped reason text is a credit-report-only placeholder and requires review for a specific principal reason.
- excessive_reason_count: Decision has 5 recorded reason outputs; benchmark maximum is 4.
- no_mapped_adverse_driver: Declined decision has no adverse driver that resolves to a governed reason-code mapping.
- recorded_output_differs_from_regeneration: Recorded reason outputs differ from deterministic regeneration. This is expected in the synthetic benchmark because seeded QA failures are intentionally present.

## Public-Data Boundary

This run uses synthetic small-business credit records. It does not evaluate real-world reason accuracy or establish whether a suitable public dataset exists.

This benchmark assesses synthetic record consistency. Any proposed real-world evaluation must justify its data, decision-process reference, reason records and review evidence for the specific accuracy claim. Portfolio, lending-volume or off-domain reason-code mechanics results alone do not establish that claim.

## Limitations

- Synthetic small-business credit benchmark only.
- No production applicant records, lender notices, or legal conclusions are represented.
- Benchmark exceptions are governance review triggers.
- Synthetic source-to-rendered-notice checks reconcile controlled notice segments to recorded reason outputs; they do not assess real-world notice readability or legal sufficiency.
- The synthetic selection-method check verifies recorded method provenance and deterministic behavior, not a real creditor's selection-method sufficiency.
- Evaluating actual reason accuracy requires evidence linking the relevant decision process to disclosed reasons, with a justified reference and stated limits; public or private status alone does not establish suitability.
- An HMDA mortgage-denial mechanics exercise would not establish small-business reason accuracy.
