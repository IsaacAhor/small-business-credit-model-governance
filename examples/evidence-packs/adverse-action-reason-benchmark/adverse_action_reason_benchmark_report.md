# Adverse-Action Reason Accuracy Benchmark Report

This report is synthetic governance evidence only. It does not provide legal advice, certify Regulation B compliance, or represent a production notice process.

- Workstream: Adverse-action reason accuracy and transparency under Regulation B 12 CFR 1002.9
- Dataset: `data/synthetic/adverse-action-reason-benchmark`
- Decisions reviewed: 10
- Declined decisions reviewed: 9
- Recorded reason outputs: 13
- Regenerated reason outputs: 12
- Expected seeded failure types observed: True

## Monitoring Reason QA Exceptions

- dec-0003: missing_reason_code (Declined decision has no generated adverse-action reason output.)
- dec-0004: unmapped_reason_code (Generated reason code is not present in the governed reason-code mapping.)
- dec-0005: generic_reason_text (Mapped reason text is too generic for governance review.)
- dec-0006: driver_mapping_mismatch (Generated reason driver does not match the governed mapping.)
- dec-0007: mapping_version_mismatch (Generated reason mapping version does not match the governed mapping.)
- dec-0010: missing_reason_code (Declined decision has no generated adverse-action reason output.)
- dec-0002: notice_text_mapping_mismatch (Recorded notice text does not match the governed reason text for its mapped driver.)
- dec-0003: principal_driver_omitted (A governed principal source driver is absent from the recorded reason outputs: cash_flow_stability)
- dec-0004: policy_version_mismatch (Reason output does not pin the underwriting policy version used for the decision.)
- dec-0005: decision_component_mismatch (Reason output component does not match the recorded final decision component.)
- dec-0005: selection_method_version_mismatch (Reason output selection-method identifier or version does not match its decision component.)
- dec-0006: principal_driver_omitted (A governed principal source driver is absent from the recorded reason outputs: industry_concentration)
- dec-0006: reason_not_in_actual_contributors (Reason output driver is not an adverse source driver for the recorded final decision component.)
- dec-0007: mapping_effective_date_mismatch (Reason output does not pin the effective date of its governed mapping.)
- dec-0008: source_driver_rank_mismatch (Reason output source-driver rank does not match deterministic source contribution ranking.)
- dec-0008: notice_template_version_mismatch (Reason output does not pin the governed notice-template identifier and version.)
- dec-0009: selection_method_version_mismatch (Reason output selection-method identifier or version does not match its decision component.)

## Supplemental Benchmark Exceptions

- non_declined_reason_output: Reason output is attached to a decision that was not declined.
- credit_report_only_placeholder: Mapped reason text is a credit-report-only placeholder and requires review for a specific principal reason.
- excessive_reason_count: Decision has 5 recorded reason outputs; benchmark maximum is 4.
- no_mapped_adverse_driver: Declined decision has no adverse driver that resolves to a governed reason-code mapping.
- recorded_output_differs_from_regeneration: Recorded reason outputs differ from deterministic regeneration. This is expected in the synthetic benchmark because seeded QA failures are intentionally present.

## Public-Data Boundary

No current public small-business dataset provides declined applications, disclosed reasons or notices, actual decision drivers, mapping versions, and reviewer labels.

HMDA can be used only as an off-domain mortgage-denial reason-code mechanics proxy. SBA, PPP, and CRA data cannot prove adverse-action reason accuracy because they do not provide the full chain of declined applications, reasons or notices, actual decision drivers, and reviewer labels.

## Limitations

- Synthetic small-business credit benchmark only.
- No production applicant records, lender notices, or legal conclusions are represented.
- Benchmark exceptions are governance review triggers.
- Synthetic source-to-notice checks use exact controlled mapping text; they do not assess real-world notice readability or legal sufficiency.
- The synthetic selection-method check verifies recorded method provenance and deterministic behavior, not a real creditor's selection-method sufficiency.
- Real-world accuracy requires private deidentified lender/CDFI/fintech application, driver, notice, and reviewer-label data.
- HMDA can support only off-domain denial-reason mechanics, not small-business proof.
