# BISG Demonstration Reference Tables

These tables support the BISG (Bayesian Improved Surname Geocoding) proxy
estimation module in `src/credit_gov/bisg.py`.

## Files

- `demo-surname-probabilities.json`
  Surname to race/ethnicity probability rows. The values are rounded
  approximations of entries in the public U.S. Census Bureau 2010 surname
  file, included for demonstration only. They are close enough to exercise
  the method credibly but should not be used for production analysis.
- `demo-geography-probabilities.json`
  Synthetic geography identifiers mapped to race/ethnicity composition rows.
  These identifiers correspond to the synthetic regions used in
  `data/synthetic/` and do not represent real places.
- `national-marginals.json`
  Approximate national race/ethnicity marginal distribution used as the
  denominator prior in the BISG posterior.

## Using Real Reference Data

For production-grade analysis, replace these files with tables derived from:

- the U.S. Census Bureau "Frequently Occurring Surnames from the 2010 Census"
  file (surname race/ethnicity percentages), and
- Census tract- or block-group-level race/ethnicity composition from the
  decennial census or ACS.

The loader (`credit_gov.bisg.load_reference_table`) accepts any JSON object
whose keys are uppercase surnames or geography identifiers and whose values
are probability rows over the categories: `white`, `black`, `hispanic`,
`api`, `aian`, `multiracial`. Rows are normalized on load.

## Honest Limitations

- BISG output is a probabilistic proxy, never an observed demographic.
- Demonstration tables cover a small surname list; unmatched surnames fall
  back to geography-only priors, and vice versa.
- All downstream comparisons are screening signals, not legal conclusions.
