# Model-Risk Oversight Public-Data Run Kit

This kit converts official SBA 7(a)/504 FOIA approved-loan CSVs into a
reproducible demonstration of fixed-horizon outcome monitoring, out-of-time
model performance review, and portfolio drift.

The source is approved-loan data. It cannot measure application approval or
decline rates, manual review, overrides, adverse-action reasons, or protected-
class disparities. The generated evidence packs record those modules as
`not_applicable`; they do not manufacture zeros or placeholder events.

Read [LIMITATIONS.md](LIMITATIONS.md) before interpreting an output.

## Install

From the repository root, use Python 3.10 or newer and install the optional
public-data dependencies:

```bash
python -m pip install -e ".[public-data]"
```

## Obtain and preserve the source files

Use the official [SBA 7(a)/504 FOIA distribution page](https://data.sba.gov/dataset/7a-504-foia).
The page can publish the historical 7(a), current 7(a), and 504 periods as
separate CSVs. Preserve the matching data dictionary and record the direct
download URL for each CSV used.

The adapter requires the current fields `GrossApproval`, `TermInMonths`,
`FirstDisbursementDate`, `AsOfDate`, and `LoanStatus`. It also reads
`ApprovalDate`, `ApprovalFY`, `Program`, `BorrState` or `ProjectState`,
`ProcessingMethod` or `DeliveryMethod`, `BusinessType`, `JobsSupported`,
`NaicsCode`, `PaidInFullDate`, `ChargeOffDate`, and
`GrossChargeOffAmount` when present.

Large raw files and run directories are ignored by Git. Do not commit them by
accident.

## Run

Supply one or more CSV paths after `--input`. Repeat `--source-url` once for
each input, in the same order, to make the provenance record self-contained.

```bash
python scripts/sba_to_monitoring.py \
  --input data/FOIA_7a_FY2010_FY2019.csv data/FOIA_7a_FY2020_Present.csv data/FOIA_504_FY2010_Present.csv \
  --source-url https://data.sba.gov/path/to/historical-7a.csv \
  --source-url https://data.sba.gov/path/to/current-7a.csv \
  --source-url https://data.sba.gov/path/to/current-504.csv \
  --out-root model_risk_oversight_sba_run \
  --program all \
  --horizon-months 36 \
  --monitoring-start 2020-01-01 \
  --cohort year \
  --max-cohorts 6 \
  --sample-per-cohort 500
```

The default outcome definition is a recorded charge-off date on or before 36
months after `FirstDisbursementDate`. A nondefault observation is admitted only
when `AsOfDate` reaches the same horizon. A charge-off recorded after the
horizon is a nondefault at the horizon. `P I F` is normalized to `PIF`, and a
seasoned `EXEMPT` active loan is a nondefault at the horizon. Canceled,
unseasoned, unsupported, and date-incomplete records are separately counted.

The model is fit only on first-disbursement dates before `--monitoring-start`.
Later rows are scored out of time. The development population is the baseline
for numeric and categorical population-stability indexes (PSI). The PSI bands
are transparent demonstration review bands, not universal policy limits.

## Outputs

The output root contains:

- `source_provenance.json`: source paths, supplied URLs, byte sizes, SHA-256
  hashes, row counts, and observed as-of dates.
- `row_disposition.json`: mutually exclusive inclusion and exclusion counts.
- `methodology.json`: label, censoring, split, feature, drift, and nonclaim
  definitions.
- `model_performance.json`: in-sample development and out-of-time monitoring
  AUC, Brier score, mean probability, default rate, and calibration gap.
- `run_environment.json`: exact invocation, platform and dependency versions,
  repository commit and dirty state, and hashes of the implementation files.
- `cross_cohort_drift_summary.csv` and `.json`: full-cohort outcome,
  performance, and drift measurements.
- `datasets/<cohort>/`: a bounded sample used as the input to the repository's
  evidence-pack workflow.
- `evidence/<cohort>/`: generated monitoring evidence packs.
- `run_summary.md`: concise run and interpretation summary.
- `output_hashes.json`: SHA-256 hashes for every generated file.

Full cohort statistics are computed before bounded evidence-pack sampling.
Sampling therefore controls artifact size without changing the full-cohort
summary. The per-pack threshold register operates on that pack's bounded sample;
use the cross-cohort summary, not the sampled breach register, for full-cohort
rate and score conclusions. Set `--sample-per-cohort` at or above the cohort
size when a full-population evidence pack is required.

## Synthetic pipeline check

The fixture mirrors the current field names and includes both development and
monitoring periods:

```bash
python scripts/make_sba_fixture.py \
  --rows 4000 \
  --out data/sba-7a-504-FIXTURE-synthetic.csv

python scripts/sba_to_monitoring.py \
  --input data/sba-7a-504-FIXTURE-synthetic.csv \
  --out-root model_risk_oversight_sba_fixture \
  --cohort year
```

The fixture and its outputs are synthetic test artifacts, not public-data
results.

## Review gate

Before sharing or relying on a run:

1. Confirm every source hash and direct URL in `source_provenance.json`.
2. Confirm the file as-of date and data dictionary version.
3. Review every row-disposition count, especially missing charge-off event
   dates and unseasoned records.
4. Confirm the development/monitoring split and both performance sections.
5. Treat decision-rate, override, reason, and fair-lending outputs as not
   applicable.
6. Preserve the exact command and code revision used.
