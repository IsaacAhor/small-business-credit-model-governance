# Fair-Lending Statistical Methodology

This note documents the statistical methods added to the fair-lending
screening workflow: significance testing on group disparities and BISG
protected-class proxy estimation. It is written for model-risk, fair-lending,
and validation reviewers.

## Why These Methods

A raw approval-rate ratio between groups says nothing about whether the gap
could be explained by sampling noise, and a workflow with no demographic
information at all cannot screen along the dimensions fair-lending review
actually cares about. These two additions close both gaps while keeping the
workflow's discipline: every output is labeled as a screening signal, not a
legal conclusion.

## Significance Testing

Implemented in `src/credit_gov/stats.py` and applied by the monitoring run to
every configured comparison-group dimension.

Method selection:

- When expected cell counts under the pooled rate are at least 5 in every
  cell, a pooled two-proportion z-test is used and the z statistic is
  reported.
- Otherwise the workflow falls back to Fisher's exact test (two-sided,
  computed in log space for numerical stability) and says so in the caveats.

What is tested:

- the approval-rate gap between the lowest- and highest-rate groups (the pair
  behind the `approval_rate_ratio` screen)
- the override-rate gap between the extreme groups (the pair behind the
  `override_rate_difference` screen)

Every result reports the effect size (rate difference and rate ratio), the
test used, the p-value, the alpha level, and whether the sample supported the
normal approximation. Fair-lending screening findings that fire on these
metrics carry the significance block alongside the threshold comparison, so a
reviewer sees both "the screen fired" and "the underlying gap is (or is not)
statistically distinguishable from noise at this sample size."

Limitations:

- These are unadjusted two-group comparisons. They do not control for
  legitimate credit factors; a significant unadjusted gap is a trigger for
  deeper review (for example, regression with credit-factor controls), not a
  conclusion.
- Multiple screens are evaluated without multiplicity correction; findings
  are review triggers, so sensitivity is preferred over strict familywise
  error control, and this choice is disclosed here.

## BISG Proxy Estimation

Implemented in `src/credit_gov/bisg.py`. Bayesian Improved Surname Geocoding
(BISG) is the standard proxy method used in fair-lending analysis when
protected-class labels are unavailable, combining surname-conditional and
geography-conditional race/ethnicity distributions:

P(race | surname, geography) is proportional to
P(race | surname) x P(race | geography) / P(race)

where P(race) is the national marginal distribution. Posteriors are
normalized per applicant. Applicants matching only one reference table fall
back to that single prior, and the basis of every posterior is counted and
reported.

Group metrics use probability-weighted counts: an applicant with a 0.7
posterior for one category contributes 0.7 of a decision to that category's
totals. Proxy-weighted approval rates are compared against a configured
reference group using the significance machinery above, with rounded
effective counts and a minimum-effective-sample floor below which groups are
excluded from testing rather than silently tested.

Running it:

- as part of the monitoring run, when the dataset contains
  `bisg-config.json` and `applicant-demographic-inputs.json` (the
  portfolio dataset does); results land in `bisg_proxy_results.json` inside
  the evidence pack and in the monitoring report
- standalone via `python scripts/run_bisg_proxy.py data/synthetic/monthly-portfolio`

Reference tables ship under `data/reference/bisg/` as documented
demonstration extracts; the loader accepts full Census-derived tables in the
same format (see the README in that folder).

An honest demonstration note: on the current 320-decision portfolio dataset,
the proxied Hispanic-to-White approval-rate gap is directionally negative but
does not reach significance at alpha 0.05 at these effective sample sizes,
while the raw regional screens do fire with significance. That contrast is
the point of adding inference: screens should distinguish gaps the data can
support from gaps it cannot.

Limitations:

- BISG output is a probabilistic proxy, never an observed demographic, and
  proxy error is itself a studied source of bias in disparity estimates.
- The shipped surname table is a small approximate extract for demonstration;
  production use requires the full Census surname file and real geographic
  composition data.
- Proxy-weighted comparisons remain unadjusted screening signals and are
  labeled as such in every output.

## References

- Elliott, M. N., Morrison, P. A., Fremont, A., McCaffrey, D. F., Pantoja,
  P., and Lurie, N. (2009). Using the Census Bureau's surname list to improve
  estimates of race/ethnicity and associated disparities. Health Services and
  Outcomes Research Methodology, 9(2), 69-83.
- Consumer Financial Protection Bureau (2014). Using publicly available
  information to proxy for unidentified race and ethnicity.
  <https://www.consumerfinance.gov/data-research/research-reports/using-publicly-available-information-to-proxy-for-unidentified-race-and-ethnicity/>
- U.S. Census Bureau. Frequently Occurring Surnames from the 2010 Census.
  <https://www.census.gov/topics/population/genealogy/data/2010_surnames.html>
