"""Generate a synthetic CSV with the current SBA 7(a)/504 FOIA field names.

The fixture exists only to test the adapter. It is not real data or evidence.
"""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
except ImportError as exc:  # pragma: no cover - optional dependency guard
    np = None
    pd = None
    PUBLIC_DATA_IMPORT_ERROR = exc
else:
    PUBLIC_DATA_IMPORT_ERROR = None

STATES = ["CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI", "WA", "MA"]
DELIVERY = ["7A GEN", "PLP", "SBA EXPRESS", "504", "CLP"]
BIZTYPE = ["INDIVIDUAL", "PARTNERSHIP", "CORPORATION"]
NAICS2 = ["23", "44", "45", "54", "72", "62", "81", "31", "42", "56"]


def require_public_data_dependencies() -> None:
    if PUBLIC_DATA_IMPORT_ERROR is not None:
        raise SystemExit(
            "Missing optional public-data dependencies. Install with "
            "`python -m pip install -e .[public-data]` from a source checkout."
        ) from PUBLIC_DATA_IMPORT_ERROR


def main(argv: list[str] | None = None) -> int:
    require_public_data_dependencies()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=4000)
    parser.add_argument("--out", default="data/sba-7a-504-FIXTURE-synthetic.csv")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)
    if args.rows < 100:
        raise SystemExit("--rows must be at least 100 so both time periods are represented")

    rng = np.random.default_rng(args.seed)
    n = args.rows
    year = rng.choice(np.arange(2015, 2023), size=n)
    month = rng.integers(1, 13, size=n)
    day = rng.integers(1, 28, size=n)
    approval = pd.Series(pd.to_datetime({"year": year, "month": month, "day": day}))
    first_disbursement = approval + pd.to_timedelta(rng.integers(10, 91, size=n), unit="D")

    gross = np.clip(rng.lognormal(mean=11.6, sigma=0.9, size=n), 5_000, 5_000_000)
    term = rng.choice([84, 120, 180, 240, 300], size=n)
    jobs = rng.integers(0, 60, size=n)
    state = rng.choice(STATES, size=n)
    delivery = rng.choice(DELIVERY, size=n)
    biztype = rng.choice(BIZTYPE, size=n, p=[0.5, 0.15, 0.35])
    naics = rng.choice(NAICS2, size=n) + rng.integers(1000, 9999, size=n).astype(str)

    latent = (
        -3.2
        + 0.55 * (np.log(gross) - 11.6)
        - 0.010 * (term - 180)
        + 0.30 * np.isin([value[:2] for value in naics], ["72", "44", "45"])
        - 0.015 * jobs
        + rng.normal(0, 0.6, size=n)
    )
    defaulted = rng.random(n) < (1 / (1 + np.exp(-latent)))
    status = np.where(defaulted, "CHGOFF", np.where(rng.random(n) < 0.55, "P I F", "EXEMPT"))
    chargeoff_months = rng.integers(6, 31, size=n)
    chargeoff_dates = [
        date + pd.DateOffset(months=int(offset)) if is_default else pd.NaT
        for date, offset, is_default in zip(first_disbursement, chargeoff_months, defaulted)
    ]
    paid_dates = [
        date + pd.DateOffset(months=48) if value == "P I F" else pd.NaT
        for date, value in zip(first_disbursement, status)
    ]
    chargeoff_amount = np.where(
        defaulted, np.round(gross * rng.uniform(0.2, 0.9, size=n), 2), 0.0
    )

    frame = pd.DataFrame(
        {
            "AsOfDate": "2026-06-30",
            "Program": rng.choice(["7A", "504"], size=n, p=[0.82, 0.18]),
            "BorrState": state,
            "GrossApproval": np.round(gross, 2),
            "ApprovalDate": approval.dt.strftime("%Y-%m-%d"),
            "ApprovalFY": approval.dt.year,
            "FirstDisbursementDate": first_disbursement.dt.strftime("%Y-%m-%d"),
            "ProcessingMethod": delivery,
            "TermInMonths": term,
            "NaicsCode": naics,
            "BusinessType": biztype,
            "JobsSupported": jobs,
            "LoanStatus": status,
            "PaidInFullDate": pd.to_datetime(paid_dates).strftime("%Y-%m-%d"),
            "ChargeOffDate": pd.to_datetime(chargeoff_dates).strftime("%Y-%m-%d"),
            "GrossChargeOffAmount": chargeoff_amount,
        }
    )
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(f"WROTE SYNTHETIC FIXTURE (NOT REAL DATA): {output} rows={len(frame)}")
    print("fixed-horizon charge-off rate in fixture:", round(float(defaulted.mean()), 4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
