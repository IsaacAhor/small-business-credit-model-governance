# Ongoing Monitoring Protocol

This protocol defines how a credit union could monitor an AI-enabled
third-party underwriting tool after due diligence and launch. It is a
reviewer-facing control pattern, not a production monitoring system by itself.

## Monitoring Owners

Assign named owners before launch:

| Role | Responsibility |
| --- | --- |
| Business owner | Confirms product fit, volume limits, member impact, and business actions. |
| Vendor-management owner | Maintains vendor documentation, contract obligations, service reports, and issue follow-up. |
| Credit-policy owner | Reviews underwriting policy, thresholds, overrides, and exception handling. |
| Compliance owner | Reviews Regulation B, fair-lending, UDAAP, privacy, complaints, and record-retention implications. |
| Model-risk or validation reviewer | Reviews model performance, limitations, explainability, drift, and change impact. |
| Information-security owner | Reviews access controls, API security, incident response, data protection, and vendor security reports. |
| Board or senior-management reporting owner | Packages periodic reports and escalations. |

For smaller credit unions, one person may cover multiple roles, but the review
record should still state who performed each review function.

## Cadence

| Event | Minimum monitoring action |
| --- | --- |
| Pre-launch | Complete due diligence, legal review, control setup, adverse-action review, and monitoring thresholds. |
| First 30 to 90 days | Run heightened monitoring for volume, overrides, errors, reason mix, complaints, and vendor service issues. |
| Monthly or quarterly | Review metrics, threshold breaches, vendor reports, adverse-action reason QA, and issue register. |
| Material model or rule change | Run model-change review before promotion or renewed reliance. |
| Incident or complaint spike | Escalate outside normal cadence and document corrective action. |
| Annual review | Reassess business fit, vendor financial/operational condition, controls, validation, contract terms, and exit plan. |

## Metrics

Define thresholds before reviewing outputs.

### Business and Operational Metrics

- application volume
- approval, decline, counteroffer, and withdrawal rates
- manual-review and override rates
- processing time
- API uptime, latency, and error rates
- unresolved vendor tickets
- complaint volume and complaint themes
- exception volume and aging

### Model and Decision Metrics

- score distribution or risk-band distribution
- approval-rate shift by product, geography, channel, or segment
- override rate by policy reason
- threshold breach count
- drift in key input distributions
- outcome or performance metrics available for the product
- model-change impact summary
- reason-code mix and reason-code concentration
- reason-output completeness and mapping failures

### Vendor Oversight Metrics

- service-level results
- incident count and severity
- unresolved audit or security findings
- documentation updates received on time
- model-change notices received on time
- subcontractor or data-source changes
- business-continuity test results
- open contract or legal issues

## Evidence Pack

A monitoring run should create or update:

- monitoring report
- metric results
- breach register
- adverse-action reason QA results
- reason-code stability report
- vendor service report
- model-change validation report if model, threshold, or mapping records changed
- issue register
- reviewer notes
- reviewer signoff
- management or board summary

The repository's existing synthetic evidence packs show this structure under
`examples/evidence-packs/monthly-portfolio/`.

## Breach Handling

For each breach or material finding, record:

- finding ID
- source metric or report
- review period
- severity
- owner
- due date
- remediation action
- accepted-risk rationale, if applicable
- evidence link
- status
- follow-up date

Do not close a finding only because a metric returned to normal. Close it when
the owner has documented cause, action taken or accepted risk, and reviewer
signoff.

## Model-Change Review

Require vendor notice and internal review for:

- new model version
- retraining or recalibration
- material feature change
- data-source change
- threshold change
- reason-code or explanation mapping change
- change to fallback or override logic
- material change in vendor subcontractors or upstream AI providers

Before relying on a changed model or decision service, the review should answer:

- What changed?
- Why did it change?
- What evidence supports the change?
- Which monitoring thresholds need to be reset?
- Did adverse-action reason mappings change?
- Did fair-lending or bias-risk screens change materially?
- Did the credit union receive enough information to understand and monitor the
  change?
- Is independent validation or challenge needed before promotion?

The repository's `scripts/run_change_validation.py` demonstrates this pattern
with synthetic model-version, threshold, and reason-code mapping records.

## Management or Board Reporting

Periodic reporting should be concise and decision useful:

- product and vendor covered
- review period
- current use and volume
- significant threshold breaches
- adverse-action reason QA issues
- fair-lending or bias-risk review triggers
- operational incidents and SLA exceptions
- unresolved vendor documentation gaps
- complaints and member-impact signals
- material model or service changes
- open issues by severity and age
- management decision: continue, continue with conditions, pause, remediate, or
  exit

## Reviewer Signoff

A signoff should state:

- records reviewed
- unresolved limitations
- issues requiring action
- whether the monitoring evidence is sufficient for the review period
- whether continued use is accepted, conditional, paused, or escalated
- next review date

Signoff is not a compliance certification. It is evidence that a qualified
reviewer inspected the record and made a documented governance decision.
