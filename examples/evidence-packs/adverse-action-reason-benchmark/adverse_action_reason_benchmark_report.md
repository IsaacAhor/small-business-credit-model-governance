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
- Real-world accuracy requires private deidentified lender/CDFI/fintech application, driver, notice, and reviewer-label data.
- HMDA can support only off-domain denial-reason mechanics, not small-business proof.
