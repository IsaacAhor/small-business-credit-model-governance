# Private Data Requirements

The canonical field specification is:

```text
docs/adverse-action-reason-run-kit/PRIVATE_DATA_SPEC.md
```

This landing note summarizes the minimum dataset needed to move beyond a
synthetic benchmark.

## Required Dataset Unit

One record set should represent a small-business credit application and its
decision path. The application must be linkable, through deidentified IDs, to
the model output, decision drivers, adverse-action reason output, reason-code
mapping version, and reviewer label.

## Minimum Fields

| Group | Required fields |
| --- | --- |
| Application | deidentified application ID, product type, channel, application date, business revenue band, requested amount, geography at a safe aggregation level |
| Action | action taken, action date, declined/counteroffer/withdrawn/incomplete flag, business-credit notice path if applicable |
| Model output | model ID, model version, score, cutoff or policy threshold, decision band |
| Decision drivers | ranked driver names, driver values or bins, driver direction, driver contribution or reason-selection rank |
| Reason output | reason codes, reason text, reason order, notice or output timestamp, delivery channel if available |
| Mapping | mapping ID, mapping version, driver-to-code mapping, effective date, retirement date if any |
| Policy context | underwriting policy version, rule overrides, manual-review flags, exception reason |
| QA labels | reviewer label, reviewer rationale, defect category, remediation status, review date |
| Provenance | extract date, source systems, deidentification method, data owner, permitted-use note |

## Stronger Validation Fields

These fields are not always available, but they materially improve the evidence:

- adverse-action notice text or structured notice payload
- reason-selection algorithm version
- model feature snapshot or binned feature record
- manual override notes with sensitive text removed
- appeal, reconsideration, or second-look outcome
- reviewer identity role, deidentified
- policy exception approval chain, deidentified
- quality-control sampling frame

## Privacy And Scope Controls

Do not include names, full addresses, tax IDs, account numbers, emails,
telephone numbers, free-text customer narratives, or unredacted documents.

Protected-class fields should not be requested unless counsel and the data owner
approve the legal basis, permitted use, and deidentification controls. They are
not required for this adverse-action reason accuracy benchmark.

## Minimum Real-World Claim

With the required fields and independent review, the repo could support a claim
that the method was tested on a private deidentified small-business credit
decision dataset.

It still would not automatically prove legal compliance, broad adoption, or
field recognition without separate evidence.
