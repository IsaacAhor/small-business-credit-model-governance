# Fair-Lending Statistical Methodology

This note documents the statistical methods added to the fair-lending
screening workflow: significance testing on group disparities, BISG
protected-class proxy estimation, and BISG measurement-error sensitivity
bounds. It is written for model-risk, fair-lending, and validation reviewers.

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
- The tested pair on each dimension is chosen post hoc: the lowest- and
  highest-rate groups. Selecting the largest observed gap before testing it
  inflates the false-positive rate beyond the nominal per-test alpha.
  Combined with the absence of multiplicity correction, these p-values should
  be read as sensitivity-oriented screening signals, not confirmatory
  inference. A pre-registered comparison structure or simultaneous-inference
  procedure would be the confirmatory upgrade.

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

Group metrics use probability-weighted counts for point estimates: an
applicant with a 0.7 posterior for one category contributes 0.7 of a decision
to that category's expected totals. Reference-group comparisons no longer turn
those fractional totals into observed integer counts. Instead, BISG inference
uses a posterior-predictive applicant bootstrap:

1. resample matched applicants with replacement using a fixed seed;
2. draw one latent group membership from each resampled applicant's BISG
   posterior;
3. recompute group approval rates and reference-group gaps; and
4. report percentile confidence intervals and a two-sided bootstrap tail
   probability for the rate difference crossing zero.

Each group also reports Kish effective sample size, `(sum p_i)^2 / sum p_i^2`,
as a concentration diagnostic. The sample gate requires both enough expected
proxy-weighted group mass and enough effective sample size; groups failing the
gate are skipped rather than silently tested.

The measurement-error sensitivity layer addresses the next problem: proxy
posterior error can bias the disparity point estimate even when the sampling
interval is honestly estimated. The configuration supplies absolute posterior
probability error margins, such as 0.05 for plus or minus five probability
points per applicant and group. For each group-specific posterior `p_i`, the
sensitivity check allows true group probability to fall in
`[max(0, p_i - epsilon), min(1, p_i + epsilon)]`. The lower group approval
rate assigns the smallest allowed group mass to approved applicants and the
largest allowed mass to declined applicants; the upper rate does the reverse.
A rate-difference interval is then formed as:

- lower bound: lower approval rate for the proxy group minus upper approval
  rate for the reference group
- upper bound: upper approval rate for the proxy group minus lower approval
  rate for the reference group

The reported finding gate uses the configured sensitivity margin and widens
the bootstrap confidence interval by the sensitivity envelope. A BISG finding
fires only when that widened interval excludes zero in the adverse direction.
This is a bounded-error sensitivity analysis for noisy group probabilities,
not a corrected point estimate. It is also not a sharp Kallus-Mao-Zhou
partial-identification implementation, because it does not solve the joint
optimization problem or enforce a full cross-category probability simplex.

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
the proxied Hispanic-to-White approval-rate gap is directionally negative, but
the posterior-predictive bootstrap confidence interval crosses zero and does
not produce a significant proxy-screening finding, while the raw regional
screens do fire with significance. That contrast is the point of adding
inference: screens should distinguish gaps the data can support from gaps it
cannot.

Limitations:

- BISG output is a probabilistic proxy, never an observed demographic, and
  proxy error is itself a studied source of bias in disparity estimates.
- The posterior-predictive bootstrap propagates applicant sampling and BISG
  posterior membership uncertainty under the proxy model, but it does not
  identify true protected-class membership or remove measurement bias.
- The shipped surname table is a small approximate extract for demonstration;
  production use requires the full Census surname file and real geographic
  composition data.
- Proxy-weighted comparisons remain unadjusted screening signals and are
  labeled as such in every output.
- Measurement-error sensitivity margins are reviewer assumptions, not facts
  estimated from the synthetic data. The shipped default gate uses a 0.05
  absolute posterior-probability error margin only for demonstration.
- The sensitivity layer is conservative and transparent, but not sharp: it
  does not enforce joint probability constraints across every race/ethnicity
  category and should not be described as a full partial-identification bound.

## Metric Limitations in Related Workflow Steps

Two metrics used by the less-discriminatory-alternative assessment step
(`src/credit_gov/lda.py`) deserve the same candor:

- Predictive "separation" is the approval rate among good outcomes minus the
  approval rate among bad outcomes, computed on final decisions. This is a
  coarse, threshold-dependent proxy (a decision-level Youden's J), not a
  score-based measure such as AUC. It is adequate for demonstrating the
  assessment process; a score-based measure is the planned upgrade when the
  workflow runs against a reference model on public data.
- Group disparity uses the minimum-to-maximum approval-rate ratio across
  groups. With many groups or small groups, the extreme pair is unstable,
  and the disparity improvement reported for a candidate alternative
  currently carries no significance test. Treat qualifying-alternative
  findings as documentation triggers, not measured effects.

## References

- Elliott, M. N., Morrison, P. A., Fremont, A., McCaffrey, D. F., Pantoja,
  P., and Lurie, N. (2009). Using the Census Bureau's surname list to improve
  estimates of race/ethnicity and associated disparities. Health Services and
  Outcomes Research Methodology, 9(2), 69-83.
- Consumer Financial Protection Bureau (2014). Using publicly available
  information to proxy for unidentified race and ethnicity.
  <https://www.consumerfinance.gov/data-research/research-reports/using-publicly-available-information-to-proxy-for-unidentified-race-and-ethnicity/>
- Chen, J., Kallus, N., Mao, X., Svacha, G., and Udell, M. (2018). Fairness
  under unawareness: assessing disparity when protected class is unobserved.
  <https://arxiv.org/abs/1811.11154>
- Kallus, N., Mao, X., and Zhou, A. (2019). Assessing algorithmic fairness
  with unobserved protected class using data combination.
  <https://arxiv.org/abs/1906.00285>
- Wastvedt, S., Snoke, J., Agniel, D., Lai, R., Elliott, M. N., and Martino,
  S. C. (2024). De-Biasing the Bias: Methods for Improving Disparity
  Assessments with Noisy Group Measurements.
  <https://arxiv.org/abs/2402.13391>
- U.S. Census Bureau. Frequently Occurring Surnames from the 2010 Census.
  <https://www.census.gov/topics/population/genealogy/data/2010_surnames.html>
