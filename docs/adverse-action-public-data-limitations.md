# Public-Data Limits For Adverse-Action Reason Accuracy

## Bottom Line

Adverse-action reason accuracy and transparency under Regulation B 12 CFR
1002.9 cannot be proven today with public small-business lending data.

The public repo can demonstrate an on-domain synthetic workflow. Public datasets
can support context, mechanics, or model-risk monitoring only. Real-world
accuracy requires private, deidentified application-level data from a lender,
CDFI, or fintech.

## What Would Be Needed

To prove actual adverse-action reason accuracy, a dataset would need the full
decision chain:

- small-business credit applications, including declined applications;
- final action taken;
- actual model or underwriting factors considered;
- driver-level explanation or contribution records;
- governed reason-code mappings and mapping versions;
- disclosed adverse-action reasons or notices;
- reviewer labels that assess whether disclosed reasons match the actual
  principal decision factors.

No current public small-business dataset provides that full chain.

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

HMDA is useful only as an off-domain mortgage-denial reason-code mechanics
proxy.

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

Public data should not be described as proof of live adverse-action reason
accuracy unless it contains the complete decision chain. Until then, the
strongest truthful public claim is that this repository provides a reproducible
synthetic governance method and clearly labeled public-data boundary.
