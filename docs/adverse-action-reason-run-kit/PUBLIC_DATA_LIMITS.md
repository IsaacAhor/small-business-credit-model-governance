# Public-Data Limits For Adverse-Action Reason Accuracy

## Demonstrated Scope

This run kit demonstrates a synthetic small-business credit workflow. It does
not evaluate actual lender reasons or establish whether a suitable public dataset
exists. Public or private status alone does not determine data suitability.
An evaluation needs evidence appropriate to its specific accuracy claim,
decision process, population and reference standard.

## What Would Be Needed

For the linked-record assessment described by this run kit, relevant evidence
includes:

- small-business credit applications, including declined applications;
- final action taken;
- actual model or underwriting factors considered;
- driver-level explanation or contribution records;
- governed reason-code mappings and mapping versions;
- disclosed adverse-action reasons or notices;
- reviewer labels that assess whether disclosed reasons match the actual
  principal decision factors.

A proposed dataset should be assessed against those needs using its exact
version, available fields and provenance. The private-data specification
describes one prospective evaluation route; it is not a universal requirement
that evaluation data be private.

## SBA 7(a), PPP, And CRA

SBA 7(a) and 504 FOIA files are useful for approved-loan portfolio monitoring
and public-data reproducibility exercises. They do not contain the denied
application universe, adverse-action notices, disclosed reasons, or actual
underwriting driver files needed to test reason accuracy.

PPP public data describes disbursed program loans. It is not a normal
small-business underwriting denial dataset and does not provide the full
adverse-action reason chain.

CRA small-business data supports lending-volume and geography review, but it
does not provide application-level adverse-action notices, model drivers, or
reason-code mappings.

Relevant public sources:

- SBA 7(a) and 504 FOIA data:
  <https://data.sba.gov/dataset/7a-504-foia>
- SBA Office of Capital Access datasets:
  <https://data.sba.gov/oca-datasets>
- FFIEC CRA public data materials:
  <https://www.ffiec.gov/data/cra/findings-from-2024-data-fact-sheet>

## HMDA

Within this run kit's scope, HMDA is treated as an off-domain mortgage-denial
reason-code mechanics proxy.

Exact label for future work:

> HMDA denial-reason data is an off-domain mortgage-denial reason-code
> mechanics proxy used to test ingestion, action-taken filtering,
> denial-reason completeness checks, reproducible reporting, and QA workflow
> design. It is not evidence of small-business credit adverse-action accuracy,
> not evidence of lender model-explanation accuracy, and not proof of
> Regulation B compliance.

HMDA is more useful than SBA, PPP, or CRA for reason-code mechanics because
Regulation C section 1003.4(a)(16) includes principal denial reasons for denied
mortgage applications. But HMDA still does not provide enough information to
verify that the reported reasons match the actual model or underwriting drivers
behind each decision.

Primary source:

- CFPB Regulation C section 1003.4:
  <https://www.consumerfinance.gov/rules-policy/regulations/1003/4/>

## CFPB Section 1071

Current Regulation B Subpart B can provide future small-business application
and action-taken context after covered reporting begins. It should not be used
as current public proof of adverse-action reason accuracy.

As of the current CFPB Regulation B materials reviewed on July 26, 2026,
section 1002.107 includes action taken fields, while the CFPB's May 1, 2026
Regulation B update says pricing and denial-reason data were eliminated from
the revised Subpart B reporting requirements.

Primary sources:

- CFPB Regulation B section 1002.107:
  <https://www.consumerfinance.gov/rules-policy/regulations/1002/107/>
- CFPB Regulation B current amendments page:
  <https://www.consumerfinance.gov/rules-policy/regulations/1002/>

## Repository Discipline

Describe an evaluation by the property tested, exact data and source version,
reference method and limitations. A portfolio or reason-code mechanics result
does not by itself establish actual decision-reason accuracy. The demonstrated
claim for this run kit remains a reproducible synthetic workflow with explicit
coverage and limits.
