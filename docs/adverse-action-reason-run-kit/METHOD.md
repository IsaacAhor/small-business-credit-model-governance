# Adverse-Action Reason Accuracy and Transparency Method

## Purpose

This method note defines the repository workstream for adverse-action reason
accuracy and transparency under Regulation B 12 CFR 1002.9.

The repository demonstrates a governance workflow for generating,
mapping, reviewing, and packaging adverse-action reason outputs for synthetic
small-business credit decisions. It does not provide legal advice, production
underwriting, lender adoption evidence, regulatory approval, or an automatic
compliance conclusion.

## Plain-English Definition

Adverse-action reason accuracy and transparency means that a declined or
otherwise adverse credit decision can be traced from:

1. the actual model or underwriting factors considered,
2. to the principal adverse drivers for that applicant,
3. to governed reason codes and specific reason text,
4. to reason QA checks for missing, generic, unmapped, stale, or mismatched
   reasons,
5. to a versioned rendered-text/template record and reason-selection method,
6. to source-to-notice reconciliation and a reviewer-ready evidence pack.

For this repository, the public demonstration uses synthetic small-business
credit data because no current public small-business dataset contains the full
chain needed to test real adverse-action reason accuracy.

## Regulatory Anchor

As of August 12, 2026, Regulation B 12 CFR 1002.9 remains the anchor for
adverse-action notification and specific-reason review. Current CFPB text states
that an adverse-action notification must include either specific reasons for the
action taken or disclosure of the applicant's right to receive the reasons.
For business credit, the notification path depends on the size and type of the
business credit applicant.

The current official interpretation provides the key design standard for this
run kit:

- reasons must be specific and identify the principal reasons for adverse
  action;
- generic statements such as failing internal standards or failing to achieve a
  qualifying score are insufficient;
- reasons must relate to and accurately describe the factors actually
  considered or scored by the creditor;
- for scoring systems, disclosed reasons must relate only to factors actually
  scored, and no principal reason may be excluded;
- for judgmental systems, reasons must relate to factors actually reviewed by
  the decision-maker;
- for combined scoring and judgmental systems, reasons should come from the
  component that the applicant failed.

Primary sources:

- CFPB current Regulation B section 1002.9:
  <https://www.consumerfinance.gov/rules-policy/regulations/1002/9/>
- CFPB Regulation B current amendments page:
  <https://www.consumerfinance.gov/rules-policy/regulations/1002/>
- Current eCFR text for 12 CFR 1002.9:
  <https://www.ecfr.gov/current/title-12/chapter-X/part-1002/subpart-A/section-1002.9>

## What The Run Kit Tests

The synthetic run kit tests the operational controls that support reason
accuracy and transparency:

- whether declined decisions have generated reason outputs;
- whether each reason output references a governed reason-code mapping;
- whether the output driver matches the mapping driver;
- whether the output mapping version matches the governed mapping version;
- whether reason text is too generic for governance review;
- whether reason outputs are attached to non-declined decisions;
- whether too many reasons are generated for one declined decision;
- whether a declined decision has no mapped adverse driver;
- whether a credit-report-only placeholder is being used where a specific
  principal reason should be reviewed.

These checks are review triggers. They do not determine legal sufficiency.

## Source-To-Notice Fidelity Controls

Where the required synthetic provenance inputs are present, the run kit also
checks the exact governed chain from the recorded final decision component to
the text record:

- the reason driver is an adverse contributor in the recorded final component;
- the recorded source-driver rank matches deterministic source ranking;
- governed principal mapped drivers within the configured review limit are not
  absent from recorded outputs;
- the reason output pins the mapping ID, mapping version, mapping effective
  date, and underwriting policy version used for the decision;
- the recorded reason text matches the controlled mapped reason text and pins
  a versioned notice template; and
- the output identifies the governed method and version configured for the
  recorded decision component.

The synthetic ranking is a reproducibility control. It does not establish that
the method would produce results substantially similar to a creditor's
production score-distance or other selection method, and it does not make a
legal-sufficiency finding. That determination requires a creditor's actual
system, data, and appropriate legal review.

## Public Demonstration Boundary

The public proof path is synthetic small-business credit data. That is the only
on-domain public method available for this workstream because the accuracy
question requires more than a denial outcome or a reason label. It requires
the actual decision factors, generated or disclosed reasons, mapping versions,
and reviewer labels.

HMDA denial-reason data may be used later only as an off-domain mortgage
reason-code mechanics proxy. HMDA can help test ingestion and reporting
mechanics, but it cannot prove small-business credit adverse-action reason
accuracy.

## Reviewer Interpretation

A reviewer may truthfully read the run kit as evidence that the repository has
a reproducible method for organizing and testing adverse-action reason controls.

A reviewer should not read it as evidence that a lender has used the method, a
notice was legally compliant, the method has been independently validated, or
any institution has adopted the repository.
