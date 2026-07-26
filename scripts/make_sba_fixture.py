"""Generate a SYNTHETIC fixture CSV that mirrors the SBA 7(a)/504 FOIA schema.

PURPOSE: prove the SBA->monitoring adapter and the governance workflow run
end-to-end BEFORE the real FOIA file is downloaded. The output of this script
is NOT real data and NOT evidence. It exists only so the pipeline can be
validated. When the real file is present, skip this script entirely.

Column names follow the documented SBA 7(a)/504 FOIA data dictionary
(data.sba.gov, dictionary as of 2025-09-30). Verify names against the current
dictionary before the real run; SBA occasionally renames columns.
"""
from __future__ import annotations

import argparse
import numpy as np
import pandas as pd

STATES = ["CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI", "WA", "MA"]
DELIVERY = ["7A GEN", "PLP", "SBA EXPRESS", "504", "CLP"]
BIZTYPE = ["INDIVIDUAL", "PARTNERSHIP", "CORPORATION"]
NAICS2 = ["23", "44", "45", "54", "72", "62", "81", "31", "42", "56"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=4000)
    ap.add_argument("--out", default="data/sba-7a-504-FIXTURE-synthetic.csv")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    n = args.rows

    fy = rng.choice([2019, 2020, 2021, 2022], size=n, p=[0.25, 0.25, 0.25, 0.25])
    month = rng.integers(1, 13, size=n)
    day = rng.integers(1, 28, size=n)
    approval_date = pd.to_datetime(
        {"year": fy, "month": month, "day": day}
    ).dt.strftime("%m/%d/%Y")

    gross = np.round(rng.lognormal(mean=11.6, sigma=0.9, size=n), 2)
    gross = np.clip(gross, 5000, 5_000_000)
    term = rng.choice([84, 120, 180, 240, 300], size=n)
    jobs = rng.integers(0, 60, size=n)
    state = rng.choice(STATES, size=n)
    delivery = rng.choice(DELIVERY, size=n)
    biztype = rng.choice(BIZTYPE, size=n, p=[0.5, 0.15, 0.35])
    naics = rng.choice(NAICS2, size=n) + rng.integers(1000, 9999, size=n).astype(str)

    # latent charge-off risk correlated to shorter term, larger amount, some sectors
    z = (
        -3.2
        + 0.55 * (np.log(gross) - 11.6)
        - 0.010 * (term - 180)
        + 0.30 * np.isin([s[:2] for s in naics], ["72", "44", "45"]).astype(float)
        - 0.015 * jobs
        + rng.normal(0, 0.6, size=n)
    )
    p_default = 1 / (1 + np.exp(-z))
    defaulted = rng.random(n) < p_default
    status = np.where(defaulted, "CHGOFF", "PIF")
    chargeoff_amt = np.where(defaulted, np.round(gross * rng.uniform(0.2, 0.9, size=n), 2), 0.0)

    df = pd.DataFrame(
        {
            "AsOfDate": "20250930",
            "BorrName": [f"FIXTURE BORROWER {i}" for i in range(n)],
            "BorrState": state,
            "GrossApproval": gross,
            "SBAGuaranteedApproval": np.round(gross * 0.75, 2),
            "ApprovalDate": approval_date,
            "ApprovalFiscalYear": fy,
            "ProcessingMethod": delivery,
            "Program": rng.choice(["7A", "504"], size=n, p=[0.82, 0.18]),
            "TermInMonths": term,
            "NaicsCode": naics,
            "BusinessType": biztype,
            "JobsSupported": jobs,
            "LoanStatus": status,
            "GrossChargeOffAmount": chargeoff_amt,
        }
    )
    df.to_csv(args.out, index=False)
    print(f"WROTE SYNTHETIC FIXTURE (NOT REAL DATA): {args.out}  rows={len(df)}")
    print("charge-off rate in fixture:", round(defaulted.mean(), 4))


if __name__ == "__main__":
    main()
