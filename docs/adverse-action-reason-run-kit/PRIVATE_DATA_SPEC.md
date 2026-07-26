# Private Data Specification For Adverse-Action Reason Accuracy

## Purpose

This specification defines the deidentified private data needed to test
real-world adverse-action reason accuracy and transparency for small-business
credit decisions.

The public repository can demonstrate the method with synthetic data. A
real-world accuracy assessment requires a lender, CDFI, or fintech dataset that
connects application records, decision factors, model drivers, reason mappings,
notices, and reviewer labels.

## Required Application And Decision Fields

- deidentified application ID
- application date
- final action date
- product type
- requested amount
- approved amount or approved limit, if applicable
- action taken
- adverse-action type, if applicable
- counteroffer flag and counteroffer terms
- applicant revenue band or revenue-size flag
- time in business
- industry or NAICS category
- geography at the least sensitive useful level
- application channel
- business segment

## Required Model And Underwriting Fields

- model ID
- model version
- model effective date
- score or risk grade
- score band
- approval or decline cutoff
- policy rules triggered
- automatic-denial flags
- manual-review flag
- judgmental review component, if any
- override flag
- override reason
- reviewer stage or queue
- underwriting variables actually considered or scored, with values or bins

## Required Driver And Explanation Fields

- decision ID or stable deidentified join key
- driver or signal name
- driver value or value band
- adverse or favorable direction
- contribution magnitude or rank
- explanation method name
- explanation method version
- baseline or reference population, if a score-distance method is used
- whether the driver was actually scored, reviewed, or used as an automatic
  denial rule

## Required Reason-Mapping Fields

- mapping ID
- reason code
- reason text
- mapped driver or signal
- mapping version
- effective date
- retirement date, if applicable
- owner or approval function
- model versions or products covered by the mapping

## Required Notice Or Disclosure Fields

- adverse-action notice sent flag
- notice date
- notice channel
- whether reasons were provided directly or through right-to-request workflow
- disclosed reason codes
- disclosed reason text
- disclosed reason order
- ECOA/FCRA split indicator, if applicable
- credit-score key-factor fields, if used
- delivery status

## Required QA And Review Labels

- reviewer-labeled principal reasons
- whether disclosed reasons matched actual scored or reviewed factors
- whether any principal reason was omitted
- whether any disclosed reason was not actually scored or reviewed
- specificity rating
- mapping-version disposition
- legal or compliance reviewer disposition, if available
- remediation issue ID
- signoff date

## Required Privacy And Provenance Fields

- deidentification method
- sampling frame
- inclusion and exclusion rules
- source system names or source categories
- extraction date
- missingness flags
- stable hash keys for joining records without exposing applicant identity
- data dictionary
- sensitivity classification

## Optional Monitoring Fields

These fields may support model-risk monitoring, but they do not by themselves
prove adverse-action reason accuracy:

- performance outcome for approved accounts
- delinquency or default indicator
- repayment observation window
- population stability cohort
- monthly run ID
- drift indicators

## Minimum Useful Dataset

The minimum useful private dataset contains declined small-business credit
applications with the actual factors considered, driver-level explanations,
reason-code mappings, disclosed reasons or notice records, and reviewer labels.

Without those fields, the dataset can support workflow testing but not a
truthful claim that adverse-action reason accuracy was validated.
