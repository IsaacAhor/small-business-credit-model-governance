# Model-Change Validation Review

This report is deterministic, synthetic, and intended only for change-governance workflow demonstration. Findings are governance review triggers, not legal or regulatory conclusions.

- Change review ID: `chg-2026-06`
- Model ID: `mdl-smb-credit-xgb`
- Prior version: `ver-2026-05` -> current version: `ver-2026-06`
- Evidence pack run: `run-2026-06`
- Material change: True
- Change categories: model_limitations_expanded, model_change_summary_updated, threshold_removed, threshold_tightened, reason_code_added, reason_code_removed, reason_code_text_or_driver_changed, reason_code_mapping_version_bumped

## Model-Version Changes

- version_id: `ver-2026-05` -> `ver-2026-06`
- effective_date: `2026-05-01` -> `2026-06-01`
- change_summary: `Initial portfolio-scale monitoring baseline version.` -> `Portfolio-scale monthly monitoring demonstration version with 320 synthetic decisions.`
- linked_validation_record: `val-portfolio-baseline` -> `val-portfolio-demo`

- Assumptions added: none
- Assumptions removed: none
- Limitations added: ['No protected-class labels or legal conclusions are embedded.']
- Limitations removed: none

## Threshold-Set Changes

- Removed: manual_review_rate (greater_than 0.5)
- Changed (tightened): approval_rate [threshold_value 0.3 -> 0.35]
- Changed (tightened): override_rate [severity medium -> high, threshold_value 0.12 -> 0.1]

## Reason-Code Mapping Changes

- Added: RC-106 (Elevated industry risk profile)
- Removed: RC-199 (Other)
- Changed (version-only): RC-101 [mapping_version 'mapver-2026-05' -> 'mapver-2026-06']
- Changed (version-only): RC-102 [mapping_version 'mapver-2026-05' -> 'mapver-2026-06']
- Changed (version-only): RC-103 [mapping_version 'mapver-2026-05' -> 'mapver-2026-06']
- Changed (structural): RC-104 [mapping_version 'mapver-2026-05' -> 'mapver-2026-06', reason_text 'High credit utilization' -> 'Elevated credit utilization']
- Changed (version-only): RC-105 [mapping_version 'mapver-2026-05' -> 'mapver-2026-06']
- Mapping version: ['mapver-2026-05'] -> ['mapver-2026-06']

## Required Review Actions Before Promotion

- Document the rationale and expected monitoring impact for changed threshold(s) (approval_rate, override_rate) and re-baseline breach expectations for the new version.
- Confirm that removing the manual_review_rate threshold(s) is an approved governance decision with a documented compensating control.
- Verify adverse-action notices and reason-code mappings for added code(s) (RC-106) produce specific, accurate reasons consistent with Regulation B 12 CFR 1002.9.
- Confirm no active adverse-action notice depends on removed reason code(s) (RC-199).
- Review revised reason text or driver mapping for code(s) (RC-104) for continued specificity and accuracy.
- Obtain independent validation signoff tying the current version to this evidence pack before promoting the version to active, consistent with principles-based model-risk change management.

## Limitations

- Synthetic data only; no production model change is represented.
- Change materiality is a configurable governance heuristic, not a legal or regulatory determination.
- Signoff fields are illustrative placeholders; no independent validation has occurred.
- Regulatory references (Regulation B 12 CFR 1002.9 reason specificity; SR 26-2 principles-based model-risk oversight and change management) are design anchors, not evidence of compliance.
