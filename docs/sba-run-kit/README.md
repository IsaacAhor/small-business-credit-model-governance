# SBA 7(a) Public-Data Monitoring Run Kit

Runs the public repo's monitoring workflow on **real federal small-business
lending records** (SBA 7(a)/504 FOIA) instead of synthetic data. Built and
proven end-to-end 2026-07-26 against the repo's Phase 2 workflow. After you have
the real data file, the run is two commands.

**Before you cite anything this produces, read `LIMITATIONS.md`.** In short: the
default-risk model is a governed-model stand-in, not an underwriting model; SBA
data is approved-only, so fairness/adverse-action work is NOT done here (that is
the HMDA track); the meaningful signals are charge-off rate, score drift, and
portfolio-mix drift across cohorts.

---

## 0. Prerequisites (do these once)

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

4. **Place the kit files into the repo:**
   - copy `scripts/sba_to_monitoring.py` and `scripts/make_sba_fixture.py` into the repo's `scripts/`
   - copy `README.md` and `LIMITATIONS.md` into `docs/sba-run-kit/`

---

## 1. Get the real SBA data

1. Open [SBA 7(a) and 504 FOIA data](https://data.sba.gov/dataset/7-a-504-foia)
2. In "Data and Resources", download the **7(a) loan-level FOIA file covering
   FY2010–present** (CSV). If it is offered as separate era files, take the
   FY2010–present one; ignore the FY1991–2009 file and the 504 file for this run.
3. Save it into the repo as:

   ```text
   data/sba-7a.csv
   ```

   (create the `data/` folder if it does not exist)
4. Optional sanity check — the adapter needs, at minimum, columns for loan
   amount, term in months, and loan status. It auto-detects the documented names
   (`GrossApproval`, `TermInMonths`, `LoanStatus`, plus `ApprovalDate`/
   `ApprovalFiscalYear`, `BorrState`, `DeliveryMethod`, `BusinessType`,
   `JobsSupported`, `NaicsCode`, `GrossChargeOffAmount`). Verify against the SBA
   data dictionary (as of 2025-09-30). **If the adapter later exits with
   "Required columns not found", open `scripts/sba_to_monitoring.py`, find the
   `pick(...)` calls in `load_and_prepare`, and add the actual column name from
   your file as a new candidate.**

---

## 2. Run it (the two commands)

```bash
# a) build the monitoring datasets from the real file AND run the workflow
python scripts/sba_to_monitoring.py \
    --input data/sba-7a.csv \
    --repo-root . \
    --out-root sba_run \
    --cohort month --max-cohorts 6 --sample-per-cohort 500
```

That single command does everything: cleans the data (matured loans, FY2010+),
trains the demonstration model, builds one cohort dataset per month, runs
`credit_gov`'s monitoring workflow on each, and writes the drift summary. There
is no separate second command needed for the basic run — the "two commands" are
this run command plus the optional fixture check in section 4.

---

## 3. What you get and how to read it

Everything lands under `sba_run/`:

- `sba_run/evidence/<cohort>/` — one reviewer-ready evidence pack per month
  (metric_results.json, breach_register.json, fair_lending_screening_results.json,
  monitoring_report.md, manifest.json, and more).
- `sba_run/cross_cohort_drift_summary.csv` (and `.json`) — one row per cohort
  with `n_loans`, `default_rate` (charge-off rate), and `score_avg`. **This is
  the headline governance signal: watch how default_rate and score_avg move
  across cohorts.** Rising default_rate with flat scores, for example, is the
  kind of drift a monitoring program is meant to catch.

Ignore `approval_rate`, `decline_rate`, `override_rate`, and the fair-lending
screening numbers in the per-cohort packs — they are not meaningful on
approved-only data (see `LIMITATIONS.md`).

---

## 4. Prove the pipeline without the real file (optional)

If you want to confirm the pipeline runs before downloading anything:

```bash
python scripts/make_sba_fixture.py --rows 4000 --out data/sba-7a-FIXTURE-synthetic.csv
python scripts/sba_to_monitoring.py --input data/sba-7a-FIXTURE-synthetic.csv --repo-root . --out-root sba_run_fixture
```

The fixture is SYNTHETIC. Its outputs are for pipeline validation only and are
**not evidence** — do not cite them. Use a different `--out-root` so they never
mix with the real run.

---

## 5. Optional rigor upgrade — make default_rate thresholdable

The built-in thresholdable metrics aren't meaningful on approved-only data. To
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

## 6. Reproducibility & provenance (after the real run)

The raw input (`data/*.csv`) and the scratch output dir (`sba_run/`) are
git-ignored — don't commit the large raw file or working outputs. To make a
run reproducible:

1. Commit the kit code and record the exact run command used.
2. Record the data source URL and the SBA file's as-of date.
3. Tag a versioned release marking the code version used.
4. Optional: to publish a provenance snapshot of outputs, copy a small curated
   subset into `examples/` (matching the repo's existing example-pack pattern)
   and commit it deliberately.
