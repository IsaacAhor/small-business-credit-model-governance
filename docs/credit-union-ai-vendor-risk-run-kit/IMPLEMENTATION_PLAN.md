# Credit Union AI Vendor-Risk Implementation Plan

## Purpose

This document is the public build authority for extending the Credit Union AI
Vendor-Risk Run Kit from a documentation profile into a reproducible, synthetic
vendor-oversight workflow. It defines milestone sequencing, scope, data
contracts, validation behavior, fixture set, test coverage, and release gates.

The work concerns AI or ML-enabled third-party products used in small-business
or member-business credit underwriting. It leads with model-risk governance,
adverse-action reason accuracy and traceability, and ongoing oversight evidence.

This is a technical implementation specification. It is not legal advice, a
compliance certification, an NCUA requirement, or evidence of credit-union
adoption or external validation.

## Milestone Sequence

The work is split into a completed documentation milestone and a separately
versioned executable milestone.

| Milestone | Purpose | Executable vendor oversight |
| --- | --- | --- |
| v0.9.2 | Correct material source-mapping and reviewability gaps in v0.9.1 and add this implementation plan. | No |
| v0.11.0 | Implements synthetic vendor-risk records, validation, evidence-pack generation, fixtures, commands, and tests. | Yes |

The v0.9.2 milestone established the accurate public baseline. Version 0.11.0
adds the separately reviewed executable build. Neither milestone may be
described as production deployment, legal
compliance, regulator approval, credit-union adoption, or external validation.

## Scope And Non-Goals

### In Scope

- AI or ML-enabled third-party components that affect small-business or
  member-business application intake, scoring, pricing, routing, approval
  recommendation, underwriting decision support, adverse-action reason support,
  manual review, overrides, or ongoing monitoring.
- Vendor due diligence, decision authority, model/data transparency limits,
  contract evidence, monitoring, material changes, issue escalation, and
  reviewer signoff as structured synthetic records.
- Regulation B adverse-action reason traceability, conditional business-credit
  notice controls, and evidence-retention prompts.
- Security and operational event records that enable an institution to perform
  its own escalation assessment.

### Explicitly Out Of Scope

- A determination that a credit union, CUSO, lender, vendor, product, contract,
  notice, or workflow is compliant, safe, sound, fair, secure, reliable, or
  approved.
- Production integrations, real member/applicant data, real vendor-confidential
  data, legal interpretations, or a complete inventory of state-law
  requirements.
- General-purpose AI governance, unrelated consumer-credit workflows,
  fraud-only tools, servicing, collections, or marketing.
- Automated suspicious-activity reporting, regulator notification, legal-notice
  delivery, or automated legal conclusions. The tool records facts and prompts
  for review; the institution remains responsible for any determination/action.
- A federal ECOA disparate-impact compliance conclusion. Any bias or
  fair-lending signal is a secondary risk-management prompt requiring
  institution-specific compliance, legal, and model-risk review.

## Source And Applicability Discipline

Every public control must identify its source class and applicability condition.
The source map must not treat law, NCUA guidance, voluntary frameworks, and
institution-specific decisions as interchangeable.

| Source class | Implementation use | Required treatment |
| --- | --- | --- |
| Binding law or regulation | Defines a conditional record/control requirement. | State applicability, cite the source, preserve its checked-on date, and do not infer universal coverage. |
| NCUA guidance or examination resource | Informs questions, evidence requests, and oversight design. | Describe as guidance/supervisory theme, not an AI-specific binding rule. |
| Voluntary or analogous framework | Provides optional vocabulary or a design benchmark. | Label it voluntary or analogous; never call it an NCUA requirement. |
| Institution-specific policy, contract, or legal decision | Sets actual thresholds, notice treatment, escalation, and acceptance. | Keep it configurable and require the reviewer to record its basis. |

The v0.9.2 source map must classify and qualify, at a minimum:

- NCUA Artificial Intelligence resources;
- NCUA third-party relationship guidance, including Letters to Credit Unions
  07-CU-13 and 01-CU-20;
- NCUA compliance-management and Regulation B resources;
- NCUA CUSO guidance, including a current-regulatory-status qualifier where
  historical fair-lending language differs from current Regulation B treatment;
- 12 CFR Part 723, only when the institution determines that its commercial
  lending provisions apply;
- Regulation B, including 12 CFR 1002.9 and 1002.12;
- applicable retention, consumer-report, electronic-disclosure, and
  small-business-lending-data requirements, including FCRA, E-SIGN, and
  Regulation B Subpart B, only when their own conditions are met;
- NCUA security/cyber resources and the institution's need to assess a
  third-party event promptly; and
- NIST AI RMF and SR 26-2 only as voluntary or analogous model-risk references,
  not credit-union mandates.

## Authoritative References

The sources below were rechecked on 2026-08-08. They let reviewers inspect
the basis for this plan without converting a source into a universal
requirement. SOURCE_MAP.md remains the detailed source-to-control crosswalk.

| Source | Class | Build relevance |
| --- | --- | --- |
| [NCUA Artificial Intelligence resources](https://ncua.gov/regulation-supervision/regulatory-compliance-resources/artificial-intelligence-ai) | NCUA guidance | AI risk management, third-party due diligence, monitoring, board/management oversight, and the technology-neutral supervisory context. |
| [07-CU-13: Evaluating Third-Party Relationships](https://ncua.gov/regulation-supervision/letters-credit-unions-other-guidance/evaluating-third-party-relationships-0) and [01-CU-20: Due Diligence Over Third-Party Service Providers](https://ncua.gov/regulation-supervision/letters-credit-unions-other-guidance/due-diligence-over-third-party-service-providers) | NCUA guidance | Risk tiering, due diligence, contracts, ongoing controls, reporting, and continuing institution responsibility. |
| [NCUA Compliance Management Systems](https://ncua.gov/regulation-supervision/manuals-guides/federal-consumer-financial-protection-guide/compliance-management/compliance-management-systems-and-compliance-risk) and [NCUA Regulation B guide](https://ncua.gov/regulation-supervision/manuals-guides/federal-consumer-financial-protection-guide/compliance-management/lending-regulations/equal-credit-opportunity-act-regulation-b) | NCUA guidance | Governance ownership, monitoring, corrective action, and business-credit review prompts. |
| [12 CFR Part 723](https://www.ecfr.gov/current/title-12/chapter-VII/subchapter-A/part-723) | Binding regulation when applicable | Commercial-lending policy, risk management, and third-party lending-personnel decision authority. |
| [12 CFR 1002.9](https://www.consumerfinance.gov/rules-policy/regulations/1002/9/) and [12 CFR 1002.12](https://www.consumerfinance.gov/rules-policy/regulations/1002/12/) | Binding regulation when applicable | Business-credit adverse-action notice paths, specific-reason controls, and record-retention prompts. |
| [CFPB Section 1071 resources](https://www.consumerfinance.gov/1071-rule/) | Binding regulation when applicable | Conditional small-business lending-data, firewall, and retention controls. |
| [FCRA Regulation V](https://www.consumerfinance.gov/rules-policy/regulations/1022/) and [NCUA E-SIGN Act guide](https://ncua.gov/regulation-supervision/manuals-guides/federal-consumer-financial-protection-guide/compliance-management/deposit-regulations/electronic-signatures-global-and-national-commerce-act-e-sign-act) | Binding law/regulation when applicable | Consumer-report and electronic-disclosure flags within a notice-control record. |
| [12 CFR 748.0](https://www.ecfr.gov/current/title-12/chapter-VII/subchapter-A/part-748/section-748.0) and [NCUA cyber-incident notification guidance](https://ncua.gov/regulation-supervision/letters-credit-unions-other-guidance/cyber-incident-notification-requirements) | Binding regulation and NCUA guidance when applicable | Security controls, contractual event notice, and institution-led escalation assessment. |
| [NCUA CUSO guidance](https://ncua.gov/regulation-supervision/letters-credit-unions-other-guidance/expansion-permissible-cuso-activities-and-associated-risks/guidance-statement) | NCUA guidance | CUSO/fintech relationship inventory and third-party lending-risk prompts; historical fair-lending language requires current-status qualification. |
| [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) and [SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm) | Voluntary or analogous reference | Optional risk-management vocabulary and model-risk design benchmark; neither is an NCUA mandate for this run kit. |

Recheck source assertions before every release that changes regulatory-language
claims. The source map is a navigation aid, not a substitute for
institution-specific counsel or compliance review.

## v0.9.2 Documentation And Reviewability Patch

v0.9.2 changes documentation, release notes, and package/release metadata. It
does not claim to implement the Phase 6 workflow.

| File | Required change |
| --- | --- |
| docs/credit-union-ai-vendor-risk-run-kit/README.md | Add applicability framing, link this plan, and state that the run kit is pre-implementation until the executable workflow is released. |
| SOURCE_MAP.md | Add source class, applicability, and checked-on fields; add Part 723, business-credit notice/retention, security/cyber, FCRA, E-SIGN, and conditional Section 1071 coverage; qualify voluntary sources and historical fair-lending language. |
| DUE_DILIGENCE.md | Replace the combined breach/incident/suspicious-activity prompt with contract-notice and institution-escalation prompts; add decision-authority, material-subcontractor, and evidence-retention questions. |
| MONITORING_PROTOCOL.md | Replace "minimum monitoring action" with illustrative risk-based cadence; require cadence rationale, heightened-monitoring triggers, and event-escalation records. |
| ADVERSE_ACTION_REVIEW.md | Add conditional business-credit notice-path, timing, specific-reason, retention, FCRA, E-SIGN, and Section 1071 review prompts. |
| LIMITATIONS.md | Explicitly state charter, asset-size, product, state-law, contract, and internal-policy dependencies; say that an event record is not a reportability determination. |
| docs/ai-rmf-alignment.md | Reconfirm that NIST AI RMF is voluntary and does not establish an NCUA requirement. |
| docs/system-implementation-roadmap.md and docs/repository-roadmap.md | Link the Phase 6 work to this plan and preserve the documentation-versus-implementation distinction. |
| README.md, docs/release-strategy.md, docs/releases/v0.9.2.md, and pyproject.toml | Update stable-release references and version metadata consistently for v0.9.2. |

### v0.9.2 Acceptance Criteria

- No text says or implies that the run kit itself meets NCUA, Part 723,
  Regulation B, FCRA, E-SIGN, or Section 1071 requirements.
- Every regulatory statement has a source class and applicability qualifier.
- The vendor is asked for contractual event notification, not for a
  suspicious-activity-reporting commitment.
- Monitoring timing is a risk-based configuration, not a universal legal or
  supervisory cadence.
- No public content includes personal data, vendor claims, institutional
  representations, or confidential information.
- Existing repository validation and tests pass.

## Executable Vendor-Oversight Build

Version 0.11.0 adds a separate vendor-risk layer. It does not silently extend
generic model records where linked vendor records preserve scope and backward
compatibility.

### Data Contracts

Add these JSON Schemas under schemas/, mirror them under
src/credit_gov/schemas/json/, and add typed models and validators under
src/credit_gov/schemas/.

| Contract | Purpose | Required concepts |
| --- | --- | --- |
| vendor-risk-review-record.schema.json | Master review record for a vendor product and covered use case. | Review ID, vendor/product identifiers, scope, decision impact/authority, applicability fields, document/contract versions, risk tier/rationale, source mappings, evidence references, owners, findings, remediation dates, review status, signoff. |
| vendor-model-component.schema.json | Records a vendor-hosted model, rules engine, score, explanation service, or material subcomponent. | Component ID, linked review, model/version IDs where available, function, data categories, output type, model-change notice method, subcontractor status, transparency state, limitation links. |
| vendor-model-limitation.schema.json | Separates an inherent/vendor-disclosed limitation from a validation gap. | Limitation ID, category, description, transparency state, evidence available, validation status, compensating control, residual-risk decision, owner, review date. |
| vendor-oversight-config.schema.json | Defines risk-based monitoring, heightened monitoring, and escalation configuration. | Linked review, cadence/rationale, metric/threshold references, event triggers, heightened-monitoring entry/exit criteria, evidence due dates, owners, reporting audience. |
| vendor-event-record.schema.json | Captures material model, data, service, or security events for institution review. | Event ID/type, detection/vendor-notice times, affected component/version, impact, contract-notice status, institution-assessment-required flag, escalation owner, remediation status, evidence links. |
| business-credit-notice-control.schema.json | Links a covered decision/workflow to its configured notice-control path. | Linked decision/component, credit/product classification, path determination, action/request dates, reason-source/mapping references, specific-reason review, retention basis, FCRA/E-SIGN flags, conditional Section 1071 flag, reviewer disposition. |

All contracts must:

- use deterministic IDs and relationships compatible with existing model,
  version, decision, threshold, reason-mapping, breach, and evidence-pack
  records;
- reject undeclared fields and invalid IDs;
- allow documented unknown or not_available states when a vendor is opaque;
- prohibit member, applicant, borrower, employee, and live vendor-confidential
  data in repository fixtures; and
- record evidence references and limitations separately from conclusions.

### Cross-Record Validation

Add vendor-risk relationship checks to the repository validation layer.
Validation must fail when:

1. A vendor review lacks covered use case, decision authority, risk rationale,
   owner, status, or evidence reference.
2. A component references an unknown review, model, version, or vendor event.
3. An opaque/partially transparent component lacks a limitation record and
   compensating-control or residual-risk decision.
4. A risk tier that requires heightened monitoring lacks configuration, evidence
   due date, or documented rationale.
5. A material model, data, subprocessor, threshold, reason-mapping, or service
   change lacks a linked event review and disposition.
6. A notice-control record lacks linked decision, configured path, reason-source
   reference, reviewer disposition, or retention basis.
7. An applicability assertion is made without its supporting evidence or
   reviewer determination.
8. A manifest references a missing vendor-risk record or mismatches model,
   version, vendor component, review period, or run ID.

Validation must report missing evidence and pending decisions as review gaps. It
must never label a record legally compliant or regulator approved.

### Modules, Scripts, And Commands

| Target | Responsibility |
| --- | --- |
| src/credit_gov/vendor_risk.py | Load, relate, and assess vendor review, component, limitation, configuration, event, and notice-control records. |
| src/credit_gov/vendor_reporting.py | Render deterministic vendor-oversight evidence-pack sections and reviewer-facing reports. |
| scripts/validate_vendor_risk_run_kit.py | Validate a vendor-risk dataset and return nonzero for invalid contracts or broken relationships. |
| scripts/build_vendor_risk_evidence_pack.py | Generate a synthetic vendor-oversight report, open-findings list, and manifest-linked evidence output. |
| src/credit_gov/commands.py and pyproject.toml | Expose package commands only after standalone scripts and tests are stable. |
| scripts/validate_repository.py | Include vendor-risk schemas, fixture checks, package-resource checks, and documentation-link checks. |

The generated report must show scope/applicability declarations; inventory;
decision authority; transparency/limitations; reviewed evidence; monitoring and
heightened-monitoring status; events/change review; adverse-action control
coverage; open findings/remediation; and signoff status. It must surface missing
evidence and pending review prominently. It must not produce a compliance score,
approval label, or legal conclusion.

### Synthetic Fixtures And Examples

Add fixtures under data/synthetic/credit-union-vendor-risk/ and generated
examples under examples/evidence-packs/credit-union-vendor-risk/.

| Fixture | Purpose |
| --- | --- |
| baseline-complete | Complete synthetic review with traceable model, reason, monitoring, and signoff records. |
| opaque-component | Unavailable model detail with documented limitation, compensating controls, and elevated monitoring. |
| material-change | Vendor model/data/reason-mapping change requiring review before continued reliance. |
| incident-escalation | Service/security event requiring institution assessment and tracked remediation, without claiming reportability. |
| invalid-missing-evidence | Deliberately incomplete review rejected by the validator. |
| invalid-broken-link | Deliberately mismatched relationship rejected by the validator. |
| notice-control-gap | Missing required notice-control evidence reported as a gap. |

Fixtures must use clearly fictional names and synthetic dates/identifiers. They
must not portray a real credit union, regulator, CUSO, vendor, product, or event.

### Tests

Add tests/test_vendor_risk_run_kit.py and extend existing package-resource,
repository-validation, monitoring, and change-validation tests where needed.

Tests must cover:

- valid and invalid forms for each new schema;
- ID, version, run, review-period, and manifest integrity;
- opaque-component limitations and compensating controls;
- risk-tier and heightened-monitoring configuration;
- material-change and incident-escalation records;
- notice-control links, reason sources, retention, and conditional flags;
- deterministic report generation and stable output ordering;
- absence of compliance/approval language in generated output;
- CLI success for valid fixtures and nonzero failure for invalid fixtures; and
- package inclusion of schemas and reference resources.

## Implementation Order

1. Complete the v0.9.2 documentation patch and validate all public claims.
2. Define schemas, typed models, ID patterns, and fixture layout.
3. Implement standalone vendor-risk loading and relationship validation.
4. Add valid and invalid fixtures; write schema and relationship tests.
5. Implement the deterministic evidence-pack report and its tests.
6. Integrate with existing monitoring, change-review, reason-mapping, and
   evidence-pack-manifest workflows.
7. Add package commands and package-resource tests.
8. Assign a release version, then update public documentation, examples, release
   notes, and version metadata consistently.
9. Run repository validation, focused/full tests, package build, and command
   smoke tests through the pull-request workflow.
10. Tag and publish the assigned vendor-oversight release only after all release
    gates pass.

External practitioner feedback may improve this plan, but it does not substitute
for these implementation/verification gates. Completing the code likewise does
not establish adoption or external validation.

## Definition Of Done

### v0.9.2 Documentation Baseline

- [x] Documentation changes in this plan's v0.9.2 scope are complete.
- [x] Source mappings distinguish binding, guidance, voluntary, and
  institution-specific material.
- [x] New public regulatory claims were rechecked and scoped for that release.
- [x] Documentation links and repository validation/tests passed for that release.
- [x] Pull request, merge, tag, and release note identify documentation and
  reviewability work only.

### v0.11.0 Vendor-Oversight Build

- [x] All six vendor-risk schemas, typed models, and relationship validators are
  implemented and packaged.
- [x] Valid and intentionally invalid synthetic fixtures are present.
- [x] Validation and evidence-pack commands are documented and tested.
- [x] Generated reports surface limitations, missing evidence, and pending
  decisions without a compliance/approval conclusion.
- [x] Existing workflows remain backward compatible and their tests pass.
- [x] Full repository validation, test suite, package build, and command smoke
  tests pass in CI for pull request #28.
- [x] A separately approved tag and release note accurately identify a
  synthetic technical demonstration and preserve every non-claim.

## Change Control

Update this plan when authoritative sources, external practitioner feedback, or
implementation findings change the work. Each change must name the affected
release and preserve the scope boundaries above. A completed checklist item
means the repository artifact exists and has passed its stated verification. It
does not mean that a regulator, credit union, vendor, or other external party
has endorsed it.
