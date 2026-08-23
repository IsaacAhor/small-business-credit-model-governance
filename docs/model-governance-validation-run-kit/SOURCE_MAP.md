# Source-to-Control Map

## Source Status

This map separates three source classes:

1. **Binding law or regulation where applicable:** Regulation B, including 12
   CFR 1002.9 adverse-action notification and specific-reason requirements.
2. **Current supervisory guidance:** the April 17, 2026 revised interagency
   model-risk guidance, published as Federal Reserve SR 26-2, OCC Bulletin
   2026-13, and FDIC FIL-16-2026. It is principles-based, risk-based, and subject
   to agency and institution applicability; the Federal Reserve states that it
   is expected to be most relevant to banking organizations over $30 billion.
3. **Nonbinding practitioner reference:** FinRegLab's April 9, 2026 *Framework
   for Managing Machine Learning Models in Consumer Credit Underwriting*. It was
   shaped through discussions with banks in an OCC Project REACh working group,
   but it is not an OCC rule, bulletin, supervisory letter, or endorsement of
   every technique. It predates SR 26-2 by eight days and reflects consumer
   underwriting and large-bank experience.

Primary links:

- FinRegLab framework and report:
  <https://finreglab.org/research/framework-for-managing-machine-learning-models-in-consumer-credit-underwriting/>
- Federal Reserve SR 26-2:
  <https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm>
- Regulation B, 12 CFR 1002.9:
  <https://www.ecfr.gov/current/title-12/chapter-X/part-1002/section-1002.9>

## Control Mapping

| Topic | Source status | Repository implementation | What remains unproven or incomplete |
| --- | --- | --- | --- |
| Risk profile, inherent risk, exposure, purpose, and materiality | SR 26-2 risk-based supervisory guidance; FinRegLab practice context | `model-risk-profile.json` and schema require version-specific rationale, dependencies, and commensurate rigor | The synthetic rating is not an institution's regulatory classification or risk-committee decision |
| Aggregate dependencies | SR 26-2 sound-practice concept | Risk profile requires explicit shared-data/method dependencies | No enterprise model inventory or aggregate-risk measurement is performed |
| Independent validation and effective challenge | SR 26-2 supervisory guidance subject to applicability; FinRegLab describes bank sequencing and independence | Validation record distinguishes developer self-review, independent internal, independent external, and pending assignment; semantic rules prohibit self-review approval | No independent reviewer has reviewed the checked-in bundle |
| Conceptual soundness and fitness for use | SR 26-2 and FinRegLab practice | Validation scope, evidence links, findings, limitations, and disposition are structured | The example does not validate a trained production model, data suitability, target design, or hyperparameters |
| Explainability-method choice and intended use | FinRegLab practitioner reference; model-risk guidance supplies broader governance context | Method records require method family/version, uses, scope, implementation reference, owner, and status | No method is approved or shown fit for a real lender's use case |
| Reference population, feature-correlation assumptions, aggregation, and directionality | FinRegLab technical practice; not a prescribed legal method | Method records require population boundary, rationale, correlation assumptions, aggregation rationale, and directionality-review status | Directionality remains pending; no empirical population study is included |
| Adverse-action reasons | Regulation B is binding on covered creditors and transactions; the law requires specific principal reasons, but does not prescribe one explainability algorithm | Existing reason mappings and outputs are linked to a governed method record and a monitoring-plan scope | The synthetic mapping does not establish accuracy or legal sufficiency for a real notice |
| Reproducibility and implementation controls | SR 26-2 sound practice and FinRegLab practice | Deterministic validation, output hashing, packaged schemas, and regression tests | Reproducible repository output is not production implementation verification |
| Robustness, stability, and outcomes analysis | SR 26-2 sound-practice expectations; FinRegLab discusses out-of-time, perturbation, and swap-set analyses | Existing SBA path includes fixed-horizon outcomes, out-of-time review, and drift; governance record can cite outcome-analysis evidence | The monthly synthetic governance fixture does not perform model robustness, sensitivity, or swap-set validation |
| Monitoring plans and change triggers | SR 26-2 guidance; FinRegLab describes practices that vary by model and institution | Monitoring plan links risk, validation, methods, thresholds, metrics, limitations, triggers, and owners | Synthetic thresholds are illustrative and not calibrated to an institution's risk tolerance |
| Reason-code distribution monitoring | FinRegLab describes this as a practice used by some banks, not a universal mandate | Monthly workflow measures reason distributions and the plan records a bounded reason-review scope | Distribution stability alone does not establish reason accuracy or notice compliance |
| Vendor model oversight | SR 26-2 includes vendor-product validation; FinRegLab discusses information and oversight constraints | Documentation profile and a version-unassigned executable implementation plan exist | Structured vendor records, vendor evidence, and executable vendor reporting are not yet implemented |
| Fair-lending and LDA analysis | Separate law, policy, and risk considerations; FinRegLab's 2026 edition does not treat these in depth because federal policy was changing | Supporting screening modules remain clearly labeled as governance review triggers | They are not the repository's core control theory and do not establish a legal violation or qualifying alternative in practice |

## Interpretation Rule

A row marked implemented means that a contract, validator, command, or
demonstration output exists and is tested. It does not mean that an institution
has adopted the control, that a regulator requires the exact implementation, or
that an independent party has validated it.
