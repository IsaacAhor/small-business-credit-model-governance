# AI Vendor Due Diligence

Use this questionnaire before a credit union adopts or materially changes an
AI-enabled third-party underwriting tool. It is written for small-business or
member-business credit workflows, but many questions also apply to consumer
credit when reviewed by appropriate counsel and compliance staff.

The goal is to make the vendor relationship reviewable. A "yes" answer should
be supported by evidence, not by a sales statement alone.

## 1. Use Case and Decision Role

| Review question | Evidence to request |
| --- | --- |
| What lending product or portfolio does the tool support? | Product description, credit policy mapping, covered portfolio list |
| Is the product used for small-business, member-business, consumer, or mixed-purpose credit? | Product taxonomy, policy owner confirmation |
| What stage does the tool affect: marketing, application intake, underwriting, pricing, fraud/KYC, manual review, adverse action, servicing, or collections? | Process map, workflow diagram, API documentation |
| Does the tool recommend, score, rank, route, approve, decline, price, or generate reasons? | Output specification, decision-role description |
| Who has final decision authority, and which vendor output may staff override, reject, or rely on? | Decision-authority matrix, credit policy, approval limits, override workflow |
| Can credit-union staff override the output? | Override policy, user permissions, override-event logs |
| Does the vendor use material subcontractors, affiliates, data brokers, model providers, cloud providers, or CUSO relationships? | Current subprocessor list, materiality criteria, affiliate list, data-flow map, change-notice terms |

## 2. Business Fit and Risk Tolerance

| Review question | Evidence to request |
| --- | --- |
| What business problem is the credit union trying to solve? | Business case, member-impact summary |
| How does the product fit the credit union's strategy, field of membership, and risk tolerance? | Board or management memo, risk appetite mapping |
| What member or applicant population will be affected? | Portfolio segmentation, expected volume |
| What are the expected benefits and the plausible adverse member impacts? | Benefits analysis, risk assessment |
| What staffing, monitoring, and technical skills are required to oversee the vendor? | Staffing plan, training plan, owner list |
| What is the exit strategy if the vendor fails, changes the model, or stops service? | Exit plan, manual fallback, transition assistance clause |

## 3. Vendor Background and Financial/Operational Review

| Review question | Evidence to request |
| --- | --- |
| What is the vendor's experience with credit underwriting or member-business lending? | Client references, implementation history |
| Has the vendor supported credit unions, CUSOs, banks, CDFIs, or fintech lenders with similar use cases? | Reference calls, case studies, deployment descriptions |
| Are there legal, regulatory, enforcement, complaint, or public controversy issues involving the vendor or key principals? | Legal search results, vendor disclosures |
| Does the vendor have adequate financial capacity and continuity planning? | Financial statements, insurance, continuity plan |
| What independent control reports are available? | SOC reports, penetration tests, security assessments, audit summaries |
| Are there concentration risks or dependency on a small number of upstream AI providers? | Subprocessor map, concentration-risk summary |

## 4. Model Function, Transparency, and Limitations

| Review question | Evidence to request |
| --- | --- |
| What model type or decision logic is used? | Model documentation, technical overview |
| What inputs, features, or data categories affect the output? | Feature list, data dictionary, prohibited-input review |
| Which inputs are supplied by the credit union, vendor, applicant, bureau, data broker, or upstream model provider? | Data lineage map |
| Can the vendor explain the reason for a score, rank, recommendation, or decline? | Explainability method note, sample explanations |
| What does the vendor refuse or is unable to disclose? | Black-box limitation statement |
| What model assumptions, exclusions, and known failure modes are documented? | Model card, validation report, limitation note |
| Has independent model validation, challenge, or technical review occurred? | Validation report, reviewer identity and scope |
| How are model updates, retraining, feature changes, threshold changes, and mapping changes governed? | Change-management policy, notification terms |

## 5. Data Governance and AI Data Security

| Review question | Evidence to request |
| --- | --- |
| What member, applicant, business, owner, guarantor, or transaction data is processed? | Data inventory, data-flow diagram |
| Is data used for training, tuning, monitoring, support, product improvement, or only inference? | Permitted-use statement, contract terms |
| How are data provenance, data quality, and data integrity verified? | Data quality reports, lineage logs, hash/checksum process |
| How are data at rest, in transit, and in APIs protected? | Encryption and API security documentation |
| Who has access to data and model outputs? | Access-control matrix, role list |
| What deidentification, masking, minimization, or retention controls apply? | Data retention schedule, deidentification method |
| How are data drift, input anomalies, and upstream data changes monitored? | Drift reports, alert thresholds |
| What contractual security-event, incident, outage, or data-compromise notice must the vendor provide, and who assesses the credit union's next steps? | Contractual notice clause, incident-response plan, internal ownership and escalation record |

## 6. Adverse-Action Reason Support

| Review question | Evidence to request |
| --- | --- |
| Can the system identify principal decision drivers for each declined or counteroffered application? | Reason output schema, ranked-driver examples |
| Are reason codes mapped to actual model, rule, or policy drivers rather than generic labels? | Reason-code mapping, mapping-version history |
| Are reasons specific enough for review under applicable Regulation B requirements? | Notice samples, legal/compliance review |
| Does the vendor support different business-credit notice pathways where applicable? | Business-credit workflow documentation |
| Are reason outputs retained with decision, model version, mapping version, and input fingerprints? | Retention record, audit log |
| How does the credit union test reason accuracy after model or threshold changes? | QA test plan, change-review evidence |

Use [ADVERSE_ACTION_REVIEW.md](ADVERSE_ACTION_REVIEW.md) for the detailed
review protocol.

## 7. Fair-Lending and Bias Risk Screening

Fair-lending review is a supporting risk-control component in this run kit. It
should not be treated as an automatic legal conclusion.

| Review question | Evidence to request |
| --- | --- |
| Has the vendor identified variables that may create protected-class proxy risk? | Feature risk review, counsel/compliance notes |
| What outcome, pricing, approval, override, and reason-code metrics can be monitored? | Monitoring metric list |
| What protected-class, proxy, geography, or segment data may be used lawfully for review? | Legal basis and data-use approval |
| Are disparity signals treated as review triggers rather than final legal findings? | Escalation policy, review workflow |
| Has a model-risk or fair-lending expert reviewed the model, data, or monitoring method? | Independent review report or written comments |
| Is any less-discriminatory-alternative analysis actually a candidate-model search rather than a label on one comparison? | Candidate-search documentation |

## 8. Operational Controls and Service Reliability

| Review question | Evidence to request |
| --- | --- |
| What uptime, latency, error-rate, and support commitments apply? | SLA, incident history |
| What happens if the API, model, or vendor service is unavailable? | Fallback procedure, manual-review path |
| What logging is available for decisions, user actions, overrides, errors, and model outputs? | Log schema, sample logs |
| Can the credit union verify vendor reports against internal records? | Reconciliation procedure |
| What quality-control process reviews vendor performance periodically? | QC schedule, report template |
| What material events require contractual notice to the credit union, including model, data-source, subprocessor, security, or service changes? | Contract notice provisions, materiality criteria, event log |

## 9. Contract and Legal Review

| Review question | Evidence to request |
| --- | --- |
| Does the contract define the vendor's role, credit union responsibilities, and decision authority? | Contract, statement of work |
| Does the credit union retain rights to audit, inspect records, or receive independent control reports? | Audit-rights clause |
| Are model changes, data-source changes, subcontractor changes, and threshold changes subject to notice? | Change-notification clause |
| Does the vendor support adverse-action, complaint, audit, and examiner-review requests? | Cooperation clause, report samples |
| Are data ownership, permitted use, retention, deletion, return, and accessible record preservation clearly defined? | Data terms, retention schedule, retrieval and transition procedures |
| Are security, privacy, incident response, business continuity, and insurance requirements defined? | Security schedule, insurance certificates |
| Are indemnity, limitation of liability, termination, transition assistance, and dispute provisions reviewed by counsel? | Legal review memo |

## 10. Oversight Record

Create a dated review record with:

- product and vendor name
- review date and review period
- credit-union owner and backup owner
- decision role and product scope
- documents reviewed
- unanswered questions
- accepted limitations
- required controls before launch
- applicability and records-retention basis confirmed by the appropriate owner
- ongoing monitoring cadence
- next review date
- reviewer signoff

The oversight record should be tied to a specific product version, model
version, mapping version, vendor documentation set, and contract version.
