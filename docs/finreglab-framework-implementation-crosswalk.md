# FinRegLab 2026 Framework Implementation Crosswalk

## Purpose and source status

This crosswalk records what the repository implements, already covered, or
deliberately excludes after a complete review of FinRegLab's April 9, 2026
*Framework for Managing Machine Learning Models in Consumer Credit
Underwriting*.

The framework is a nonbinding practitioner reference. It reflects discussions
with banks in an OCC Project REACh working group, but it is not a statute,
regulation, agency rule, supervisory letter, or OCC endorsement of each method.
It focuses on consumer underwriting and large-bank practices. Any transfer to
small-business or credit-union use therefore requires a stated scope and
applicability rationale.

Primary sources rechecked on 2026-08-23:

- [FinRegLab framework landing page](https://finreglab.org/research/framework-for-managing-machine-learning-models-in-consumer-credit-underwriting/)
- [Federal Reserve SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm)
- [Current Regulation B § 1002.9](https://www.consumerfinance.gov/rules-policy/regulations/1002/9/)
- [CFPB Regulation B current-status page](https://www.consumerfinance.gov/rules-policy/regulations/1002/2026-06-30/)

SR 26-2, issued eight days after the FinRegLab report, supersedes SR 11-7. It is
risk-based supervisory guidance, expected to be most relevant to banking
organizations over $30 billion, and expressly does not create prescriptive or
enforceable standards. Regulation B § 1002.9 remains the binding anchor where
applicable: disclosed adverse-action reasons must be specific, principal, and
accurately tied to factors actually considered or scored. It does not prescribe
one explainability algorithm.

## Section-by-section decision record

| Framework section | Relevance to this repository | Repository treatment | Decision for this implementation |
| --- | --- | --- | --- |
| §§1–2, introduction and background (printed pp. 3–15) | Establishes the supervised, offline/batch ML underwriting scope and the performance/complexity tradeoff | `docs/system-boundaries.md`, model registry/version records, and public limitations define the repository's narrower small-business scope | Context only; no expansion to generative AI, online learning, marketing, servicing, fraud, or collections |
| §3, initial model design (printed pp. 16–21) | Data suitability, representativeness, target/input selection, algorithm complexity, explainability, staff expertise, vendor choice, and MLOps | Formal risk and validation records capture purpose, materiality, data constraints, explainability assumptions, evidence, findings, and limitations | Existing partial coverage retained; this tranche does not claim to validate a trained production model, development data, target, hyperparameters, or deployment environment |
| §4, adverse-action disclosures (printed pp. 22–36) | Specific and accurate principal reasons; method/reference-population/aggregation/directionality review; notice generation and periodic QA | Existing reason mappings, reason outputs, governed method records, reason QA, rendered-notice checks, and the new business-credit notice-control contract | Link vendor reason support to decision, mapping, evidence, path, retention, conditional applicability, and reviewer disposition; do not mandate SHAP, LIME, integrated gradients, PDP/ICE/ALE, or one reference population |
| §4.3.5, perturbation testing (printed pp. 33–36) | Describes one potential reason-fidelity test and acknowledges limitations and alternative practices | No public perturbation engine is added | Excluded from this tranche; the framework does not make the technique universal, and existing QA must not be mislabeled as perturbation validation or ground truth |
| §5, other model-risk concerns (printed pp. 37–46) | Risk-based rigor, effective challenge, conceptual soundness, outcomes analysis, robustness, implementation verification, monitoring, and significant-change triggers | Formal governance bundle, fixed-horizon SBA monitoring path, thresholds, change review, reason-distribution monitoring, findings, and deterministic manifests | Existing coverage retained and source framing updated to current SR 26-2; the vendor config links risk tier, thresholds, event triggers, heightened monitoring, evidence dates, and owners |
| §6.1, vendor models (printed pp. 47–48) | Vendor opacity, continuing institution responsibility, data/model/explainability/validation/monitoring information, change notice, supplemental controls, and alternative vendors/sources | Six new vendor contracts, relationship/evidence validation, seven synthetic scenarios, and deterministic reviewer reporting | Implemented as the principal new tranche because it directly closes the repository's documented third-party model-oversight gap |
| §6.2, second-look models (printed p. 49) | Special sequencing and notice questions when a second model reviews initial declines | No dedicated second-look contract or workflow | Excluded; it is a specialized deployment pattern outside the repository scope unless a later use case and evidence base justify it |
| §7, conclusion (printed p. 50) | Summarizes practitioner considerations and evolving methods | Source and limitation framing | Context only; not treated as a requirement list |
| Appendix B, credit lifecycle uses (printed pp. 52–55) | Marketing, account management, early-risk detection, collections, recovery, and post-cycle analysis | System boundaries limit the project to underwriting and related documentation/monitoring | Excluded except where a record directly supports the governed underwriting decision or its monitoring |
| Appendices C–D, algorithms and explainability tools (printed pp. 56–62) | Describes gradient boosting, neural networks, LIME, SHAP, integrated gradients, PDP, ICE, and ALE with tradeoffs | Explainability-method contract records method family, use, population, assumptions, aggregation, directionality, limitations, and tests | Catalog context only; no method is hard-coded as legally sufficient, universally reliable, or required |
| Appendix E, fair-lending background (printed p. 63) | States that federal fair-lending policy was changing and does not provide a current compliance framework | Fair-lending/LDA modules remain separate supporting risk screens; current source maps control | No new fair-lending or LDA implementation; the July 21, 2026 removal of Regulation B's effects test must be reflected in current legal framing |

## What the vendor build enforces

The executable vendor layer fails closed on missing required records, unknown
review/model/version/decision/reason links, missing evidence, unrecorded
limitations for partial or opaque components, unresolved compensating-control
decisions, high-risk profiles without heightened monitoring, component-link
mismatches, unlinked limitations or events, notice mappings that do not match
the decision's recorded reasons, and accepted reviews with a pending
material-event assessment.

It reports rather than hides partial transparency, pending conditional notice
applicability, open findings, incomplete event remediation, and notice-control
gaps. Its cadence, thresholds, source applicability, residual-risk decisions,
and signoff are reviewer inputs, not regulatory conclusions.

## What remains unproven

- No real financial institution or vendor supplied evidence for the checked-in
  fixtures.
- No practitioner has independently reviewed the new executable artifact.
- The workflow does not establish model accuracy, fitness for use, notice legal
  sufficiency, vendor reliability, safety, soundness, security, compliance,
  production deployment, institutional adoption, or regulatory approval.
- Closing those gaps requires permissioned evidence and qualified external or
  institution-specific review; additional self-authored code cannot manufacture
  that proof.
