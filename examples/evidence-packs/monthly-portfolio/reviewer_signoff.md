# Reviewer Signoff

This artifact supports governance workflow demonstration only.

- Run ID: `run-2026-06`
- Model ID: `mdl-smb-credit-xgb`
- Version ID: `ver-2026-06`
- Reviewer status: `pending_review`
- Review summary: Escalation recommended

## Model-Change Validation Signoff

- Prior version: `ver-2026-05` -> current version: `ver-2026-06`
- Evidence pack run: `run-2026-06`
- Validation owner: Independent Model Validation
- Promotion gate: `independent_validation_signoff`
- Material change: True
- Validation status: `pending_review`

Required before promotion to active:

- Document the rationale and expected monitoring impact for changed threshold(s) (approval_rate, override_rate) and re-baseline breach expectations for the new version.
- Confirm that removing the manual_review_rate threshold(s) is an approved governance decision with a documented compensating control.
- Verify adverse-action notices and reason-code mappings for added code(s) (RC-106) produce specific, accurate reasons consistent with Regulation B 12 CFR 1002.9.
- Confirm no active adverse-action notice depends on removed reason code(s) (RC-199).
- Review revised reason text or driver mapping for code(s) (RC-104) for continued specificity and accuracy.
- Obtain independent validation signoff tying the current version to this evidence pack before promoting the version to active, consistent with principles-based model-risk change management.

Independent validation reviewer: ____________________

Validation signoff date: ____________________

Reviewer: ____________________

Date: ____________________
