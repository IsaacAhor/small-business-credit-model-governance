# Model-Risk Oversight Run Kit

SBA 7(a)/504 FOIA approved-loan public-data monitoring demonstration.

Runs the public repo's monitoring workflow on **real federal small-business
lending records** (SBA 7(a)/504 FOIA) instead of synthetic data. Built and
proven end-to-end 2026-07-26 against the repo's Phase 2 workflow. After you have
the real data file, the main run is one command.

**Before you cite anything this produces, read `LIMITATIONS.md`.** In short: the
default-risk model is a governed-model stand-in, not an underwriting model;
SBA data is approved-only, so fairness/adverse-action work is not done here;
the meaningful signals are charge-off rate, score drift, and portfolio-mix
drift across cohorts.

---

## 0. Prerequisites

1. **A local clone of the public repo**, and you must run everything **from the
   repo root** (the folder containing `src/credit_gov/`). The adapter imports
   `credit_gov` from there.

   ```bash
   git clone https://github.com/IsaacAhor/small-business-credit-model-governance.git
   cd small-business-credit-model-governance
   ```

2. **Python 3.10 or newer** (built on 3.11).

   ```bash
   python3 --version
   ```

3. **Python packages:**

   ```bash
   pip install pandas numpy scikit-learn
   ```

4. **Kit files:**

   - `scripts/sba_to_monitoring.py`
   - `scripts/make_sba_fixture.py`
   - `docs/model-risk-oversight-run-kit/README.md`
   - `docs/model-risk-oversight-run-kit/LIMITATIONS.md`

---

## 1. Get the real SBA data

1. Open [SBA 7(a) and 504 FOIA data](https://data.sba.gov/dataset/7-a-504-foia)
2. In "Data and Resources", download the loan-level FOIA CSV you want to
   monitor. The adapter supports a combined 7(a)/504 file or separate 7(a) or
   504 files. For the standard run, prefer the FY2010-present loan-level file
   and preserve the matching data dictionary for provenance.
3. Save it into the repo as:

   ```text
   data/sba-7a-504.csv
   ```

   If you use a more specific local filename, update the `--input` argument in
   the run command.
4. Optional sanity check: the adapter needs, at minimum, columns for loan
   amount, term in months, and loan status. It auto-detects the documented names
   (`GrossApproval`, `TermInMonths`, `LoanStatus`, plus `ApprovalDate`,
   `ApprovalFiscalYear`, `BorrState`, `ProcessingMethod` or `DeliveryMethod`,
   optional `Program`, `BusinessType`, `JobsSupported`, `NaicsCode`, and
   `GrossChargeOffAmount`). Verify against the SBA data dictionary before each
   real-data run.

---

## 2. Run it

```bash
python scripts/sba_to_monitoring.py \
    --input data/sba-7a-504.csv \
    --repo-root . \
    --out-root model_risk_oversight_sba_run \
    --program all \
    --cohort month --max-cohorts 6 --sample-per-cohort 500
```

That single command cleans the data (matured loans, FY2010+), trains the
demonstration model, builds one cohort dataset per month, runs `credit_gov`'s
monitoring workflow on each, and writes the drift summary. The optional fixture
check in section 4 is only for pipeline validation before downloading the public
file.

Program filter:

- `--program all` keeps every row and is the default.
- `--program 7a` keeps records whose `Program` field does not contain 504.
- `--program 504` keeps records whose `Program` field contains 504.

If the input file has no `Program` column, use `--program all` for a
single-program file. The adapter exits rather than guessing when a program
filter is requested without a program column.

---

## 3. What you get and how to read it

Everything lands under `model_risk_oversight_sba_run/`:

- `model_risk_oversight_sba_run/evidence/<cohort>/`: one reviewer-ready
  evidence pack per month (`metric_results.json`, `breach_register.json`,
  `fair_lending_screening_results.json`, `monitoring_report.md`,
  `manifest.json`, and more).
- `model_risk_oversight_sba_run/cross_cohort_drift_summary.csv` and `.json`:
  one row per cohort with `n_loans`, `default_rate`, `score_avg`, and
  `program_scope`.

The headline governance signals are charge-off rate, score drift, and
portfolio-mix drift across cohorts. Rising default rate with flat scores, for
example, is the kind of drift a monitoring program is meant to catch.

Ignore `approval_rate`, `decline_rate`, `override_rate`, and the fair-lending
screening numbers in the per-cohort packs. They are not meaningful on
approved-only data. See `LIMITATIONS.md`.

---

## 4. Prove the pipeline without the real file

If you want to confirm the pipeline runs before downloading anything:

```bash
python scripts/make_sba_fixture.py --rows 4000 --out data/sba-7a-504-FIXTURE-synthetic.csv
python scripts/sba_to_monitoring.py --input data/sba-7a-504-FIXTURE-synthetic.csv --repo-root . --out-root model_risk_oversight_sba_fixture --program all
```

The fixture is synthetic. Its outputs are for pipeline validation only and are
**not evidence**. Use a different `--out-root` so they never mix with the real
run.

---

## 5. Optional rigor upgrade: make default_rate thresholdable

The built-in thresholdable metrics are not meaningful on approved-only data. To
let the workflow raise a breach when the charge-off rate crosses a threshold,
make two small edits, then re-run section 2.

**a) In `src/credit_gov/monitoring.py`, inside `compute_metrics(...)`, add a
`default_rate` to the returned metrics dict** (it already loads `outcomes`):

```python
    # near the other rate calculations in compute_metrics
    defaulted = sum(
        1 for o in outcomes
        if o["repayment_or_default_indicator"] == "default"
    )
    # ...then add this key to the returned dict:
    #   "default_rate": safe_rate(defaulted, len(outcomes)),
```

**b) In the adapter's `threshold-set.json` block (in `write_cohort`), add a
threshold** so the workflow evaluates it:

```json
{"metric_name": "default_rate", "comparison_rule": "greater_than",
 "threshold_value": 0.08, "severity": "high", "escalation_owner": "Model Risk Governance"}
```

Ship this as its own commit/release and re-run section 2 so the change is dated
and reproducible.

---

## 6. Reproducibility And Provenance

The raw input (`data/*.csv`) and scratch output dirs such as
`model_risk_oversight_sba_run/` are git-ignored. Do not commit the large raw
file or working outputs. To make a run reproducible:

1. Commit the kit code and record the exact run command used.
2. Record the data source URL and the SBA file's as-of date.
3. Tag a versioned release marking the code version used.
4. Optional: to publish a provenance snapshot of outputs, copy a small curated
   subset into `examples/` and commit it deliberately.
