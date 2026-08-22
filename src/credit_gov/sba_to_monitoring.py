"""Convert current SBA 7(a)/504 FOIA CSVs into reproducible monitoring runs.

The public data contain approved loans, not applications or underwriting
decisions. This adapter therefore limits itself to fixed-horizon charge-off
outcomes, an out-of-time demonstration model, portfolio composition, and drift.
Decision-rate, manual-review, override, adverse-action-reason, and fair-lending
modules are explicitly marked not applicable rather than filled with stand-ins.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any, Iterable

try:
    import numpy as np
    import pandas as pd
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import brier_score_loss, roc_auc_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
except ImportError as exc:  # pragma: no cover - optional dependency guard
    np = None
    pd = None
    PUBLIC_DATA_IMPORT_ERROR = exc
else:
    PUBLIC_DATA_IMPORT_ERROR = None

MODEL_ID = "mdl-sba-public-monitoring-demo"
VERSION_ID = "ver-sba-public-monitoring-2"
DEFAULT_DISTRIBUTION_PAGE = "https://data.sba.gov/dataset/7a-504-foia"
DEFAULT_DICTIONARY_URL = (
    "https://data.sba.gov/sites/default/files/uploaded_resources/"
    "7a_504_foia_data_dictionary.xlsx"
)

CENSUS_REGION = {
    **{s: "west" for s in ("CA", "WA", "OR", "NV", "AZ", "CO", "UT", "ID", "MT", "WY", "NM", "AK", "HI")},
    **{s: "midwest" for s in ("IL", "OH", "MI", "IN", "WI", "MN", "IA", "MO", "KS", "NE", "SD", "ND")},
    **{s: "south" for s in ("TX", "FL", "GA", "NC", "SC", "VA", "TN", "AL", "MS", "LA", "AR", "OK", "KY", "WV", "MD", "DE", "DC")},
    **{s: "northeast" for s in ("NY", "PA", "MA", "NJ", "CT", "RI", "NH", "VT", "ME")},
}

COLUMN_CANDIDATES = {
    "amount": ("GrossApproval", "GrossApproval$", "gross_approval"),
    "term": ("TermInMonths", "TermMonths", "term"),
    "approval_date": ("ApprovalDate", "approval_date"),
    "approval_fy": ("ApprovalFY", "ApprovalFiscalYear", "FiscalYear"),
    "first_disbursement_date": ("FirstDisbursementDate", "FirstDisbursementDt"),
    "as_of_date": ("AsOfDate", "as_of_date"),
    "state": ("BorrState", "ProjectState", "state"),
    "delivery": ("ProcessingMethod", "DeliveryMethod", "delivery"),
    "program": ("Program",),
    "biztype": ("BusinessType", "business_type"),
    "jobs": ("JobsSupported", "jobs"),
    "naics": ("NaicsCode", "NAICSCode", "naics"),
    "status": ("LoanStatus", "status"),
    "paid_in_full_date": ("PaidInFullDate", "PaidInFullDt"),
    "chargeoff_date": ("ChargeOffDate", "ChargeOffDt"),
    "chargeoff_amount": ("GrossChargeOffAmount", "ChargeOffAmount"),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def require_public_data_dependencies() -> None:
    if PUBLIC_DATA_IMPORT_ERROR is not None:
        raise SystemExit(
            "Missing optional public-data dependencies. Install with "
            "`python -m pip install -e .[public-data]` from a source checkout."
        ) from PUBLIC_DATA_IMPORT_ERROR


def canonical_column_map(columns: Iterable[str]) -> dict[str, str | None]:
    by_lower = {column.lower(): column for column in columns}
    return {
        field: next(
            (by_lower[candidate.lower()] for candidate in candidates if candidate.lower() in by_lower),
            None,
        )
        for field, candidates in COLUMN_CANDIDATES.items()
    }


def normalized_status(values: pd.Series) -> pd.Series:
    """Normalize whitespace and punctuation (for example, ``P I F`` -> ``PIF``)."""
    return (
        values.fillna("")
        .astype(str)
        .str.upper()
        .str.replace(r"[^A-Z0-9]+", "", regex=True)
    )


def add_months_preserving_day(values: pd.Series, months: int) -> pd.Series:
    periods = values.dt.to_period("M") + months
    first_days = periods.dt.to_timestamp()
    days = np.minimum(values.dt.day.to_numpy(), periods.dt.days_in_month.to_numpy())
    return first_days + pd.to_timedelta(days - 1, unit="D")


def program_category(values: pd.Series) -> pd.Series:
    normalized = values.fillna("").astype(str).str.upper().str.strip()
    return pd.Series(
        np.where(normalized.str.contains("504"), "504", "7a"), index=values.index
    )


def _as_text(raw: pd.DataFrame, column: str | None, default: str) -> pd.Series:
    if column is None:
        return pd.Series(default, index=raw.index, dtype="object")
    return raw[column].fillna(default).astype(str).str.strip()


def prepare_chunk(
    raw: pd.DataFrame,
    columns: dict[str, str | None],
    horizon_months: int,
    selected_program: str = "all",
) -> tuple[pd.DataFrame, Counter[str]]:
    """Apply mutually exclusive disposition rules and construct fixed-horizon labels."""
    counts: Counter[str] = Counter(rows_read=len(raw))
    frame = pd.DataFrame(index=raw.index)
    frame["amount"] = pd.to_numeric(raw[columns["amount"]], errors="coerce")
    frame["term"] = pd.to_numeric(raw[columns["term"]], errors="coerce")
    frame["origin_date"] = pd.to_datetime(
        raw[columns["first_disbursement_date"]], errors="coerce"
    )
    frame["as_of_date"] = pd.to_datetime(raw[columns["as_of_date"]], errors="coerce")
    frame["approval_date"] = (
        pd.to_datetime(raw[columns["approval_date"]], errors="coerce")
        if columns["approval_date"]
        else frame["origin_date"]
    )
    frame["chargeoff_date"] = (
        pd.to_datetime(raw[columns["chargeoff_date"]], errors="coerce")
        if columns["chargeoff_date"]
        else pd.NaT
    )
    frame["chargeoff_amount"] = (
        pd.to_numeric(raw[columns["chargeoff_amount"]], errors="coerce").fillna(0.0)
        if columns["chargeoff_amount"]
        else 0.0
    )
    frame["status"] = normalized_status(raw[columns["status"]])
    frame["program"] = program_category(_as_text(raw, columns["program"], "7a"))
    frame["state"] = _as_text(raw, columns["state"], "NA").str.upper()
    frame["delivery"] = _as_text(raw, columns["delivery"], "unknown")
    frame["biztype"] = _as_text(raw, columns["biztype"], "unknown").str.upper()
    frame["jobs"] = (
        pd.to_numeric(raw[columns["jobs"]], errors="coerce").fillna(0.0)
        if columns["jobs"]
        else 0.0
    )
    frame["naics2"] = (
        _as_text(raw, columns["naics"], "00")
        .str.replace(r"\.0$", "", regex=True)
        .str[:2]
    )

    disposition = pd.Series("candidate", index=frame.index, dtype="object")

    def exclude(mask: pd.Series, reason: str) -> None:
        effective = mask.fillna(False) & disposition.eq("candidate")
        disposition.loc[effective] = reason

    exclude(frame["status"].str.contains("CANCL|CANCEL"), "excluded_cancelled")
    exclude(
        frame[["amount", "term", "origin_date", "as_of_date"]].isna().any(axis=1)
        | frame["amount"].le(0)
        | frame["term"].le(0),
        "excluded_missing_or_invalid_core_field",
    )
    exclude(frame["origin_date"].dt.year.lt(2010), "excluded_pre_fy2010")
    if selected_program != "all":
        exclude(frame["program"].ne(selected_program), "excluded_program_filter")

    chargeoff_signal = (
        frame["status"].str.contains("CHGOFF|CHARGEOFF")
        | frame["chargeoff_amount"].gt(0)
        | frame["chargeoff_date"].notna()
    )
    supported_status = frame["status"].str.contains(
        "PIF|PAIDINFULL|EXEMPT|CHGOFF|CHARGEOFF"
    )
    exclude(~supported_status & ~chargeoff_signal, "excluded_unsupported_status")
    exclude(
        chargeoff_signal & frame["chargeoff_date"].isna(),
        "excluded_chargeoff_missing_event_date",
    )

    frame["horizon_end"] = add_months_preserving_day(
        frame["origin_date"], horizon_months
    )
    exclude(
        frame["as_of_date"].lt(frame["horizon_end"]),
        "excluded_unseasoned_at_as_of_date",
    )

    eligible = disposition.eq("candidate")
    frame["default"] = (
        chargeoff_signal & frame["chargeoff_date"].le(frame["horizon_end"])
    ).astype(int)
    disposition.loc[eligible & frame["default"].eq(1)] = (
        "eligible_default_within_horizon"
    )
    disposition.loc[eligible & frame["default"].eq(0)] = (
        "eligible_nondefault_at_horizon"
    )
    counts.update(disposition.value_counts().to_dict())

    keep = disposition.str.startswith("eligible_")
    output = frame.loc[keep].copy()
    output["disposition"] = disposition.loc[keep]
    return output.reset_index(drop=True), counts


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_and_prepare(
    paths: list[Path] | Path,
    horizon_months: int = 36,
    selected_program: str = "all",
    chunksize: int = 100_000,
    source_urls: list[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read one or more official-layout CSVs in chunks and retain eligible rows."""
    require_public_data_dependencies()
    if isinstance(paths, Path):
        paths = [paths]
    source_urls = source_urls or []
    if source_urls and len(source_urls) != len(paths):
        raise ValueError("--source-url must be supplied once per --input file")

    prepared: list[pd.DataFrame] = []
    overall_counts: Counter[str] = Counter()
    sources: list[dict[str, Any]] = []
    for path_index, path in enumerate(paths):
        path = path.resolve()
        header = pd.read_csv(path, nrows=0)
        columns = canonical_column_map(header.columns)
        required = ("amount", "term", "first_disbursement_date", "as_of_date", "status")
        missing = [name for name in required if columns[name] is None]
        if missing:
            raise ValueError(f"{path.name}: required columns not found: {missing}")
        if selected_program != "all" and columns["program"] is None:
            raise ValueError(
                f"{path.name}: --program filtering requires the Program column"
            )
        usecols = sorted({column for column in columns.values() if column is not None})
        file_counts: Counter[str] = Counter()
        as_of_min: pd.Timestamp | None = None
        as_of_max: pd.Timestamp | None = None
        for raw in pd.read_csv(
            path, usecols=usecols, chunksize=chunksize, low_memory=False
        ):
            output, counts = prepare_chunk(
                raw, columns, horizon_months, selected_program
            )
            file_counts.update(counts)
            overall_counts.update(counts)
            if not output.empty:
                prepared.append(output)
                current_min = output["as_of_date"].min()
                current_max = output["as_of_date"].max()
                as_of_min = current_min if as_of_min is None else min(as_of_min, current_min)
                as_of_max = current_max if as_of_max is None else max(as_of_max, current_max)
        sources.append(
            {
                "path": str(path),
                "filename": path.name,
                "source_url": source_urls[path_index] if source_urls else None,
                "byte_size": path.stat().st_size,
                "sha256": sha256_file(path),
                "rows_read": file_counts["rows_read"],
                "eligible_rows": file_counts["eligible_default_within_horizon"]
                + file_counts["eligible_nondefault_at_horizon"],
                "eligible_as_of_date_min": as_of_min.strftime("%Y-%m-%d") if as_of_min is not None else None,
                "eligible_as_of_date_max": as_of_max.strftime("%Y-%m-%d") if as_of_max is not None else None,
                "row_disposition": dict(sorted(file_counts.items())),
            }
        )
    if not prepared:
        raise ValueError(
            "No eligible fixed-horizon rows remained after the documented exclusions"
        )
    frame = pd.concat(prepared, ignore_index=True)
    provenance = {
        "record_type": "source_provenance",
        "created_at": now_iso(),
        "official_distribution_page": DEFAULT_DISTRIBUTION_PAGE,
        "official_data_dictionary": DEFAULT_DICTIONARY_URL,
        "sources": sources,
        "combined_row_disposition": dict(sorted(overall_counts.items())),
        "eligible_rows": len(frame),
    }
    return frame, provenance


def model_features(frame: pd.DataFrame) -> pd.DataFrame:
    features = pd.DataFrame(index=frame.index)
    features["log_amount"] = np.log1p(frame["amount"].clip(lower=0))
    features["term"] = frame["term"]
    features["log_jobs"] = np.log1p(frame["jobs"].clip(lower=0))
    features["naics2"] = frame["naics2"].fillna("00").astype(str)
    features["biztype"] = frame["biztype"].fillna("unknown").astype(str)
    features["region"] = frame["state"].map(CENSUS_REGION).fillna("other")
    features["delivery"] = frame["delivery"].fillna("unknown").astype(str)
    features["program"] = frame["program"].fillna("unknown").astype(str)
    return features


def performance_metrics(
    y_true: pd.Series | np.ndarray, probabilities: np.ndarray
) -> dict[str, Any]:
    y = np.asarray(y_true, dtype=int)
    result: dict[str, Any] = {
        "n": int(len(y)),
        "default_rate": round(float(y.mean()), 6) if len(y) else None,
        "mean_predicted_default_probability": round(float(probabilities.mean()), 6)
        if len(y)
        else None,
        "brier_score": round(float(brier_score_loss(y, probabilities)), 6)
        if len(y)
        else None,
        "calibration_gap": round(float(probabilities.mean() - y.mean()), 6)
        if len(y)
        else None,
        "roc_auc": None,
    }
    if len(np.unique(y)) == 2:
        result["roc_auc"] = round(float(roc_auc_score(y, probabilities)), 6)
    return result


def train_out_of_time_model(
    frame: pd.DataFrame,
    monitoring_start: pd.Timestamp,
    max_training_rows: int,
    seed: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Fit only on pre-monitoring origins, then score every eligible row."""
    development = frame["origin_date"].lt(monitoring_start)
    if development.sum() == 0:
        raise ValueError("No development rows precede --monitoring-start")
    train_index = frame.index[development]
    if len(train_index) > max_training_rows:
        train_index = frame.loc[train_index].sample(
            max_training_rows, random_state=seed
        ).index
    features = model_features(frame)
    numeric = ["log_amount", "term", "log_jobs"]
    categorical = ["naics2", "biztype", "region", "delivery", "program"]
    y_train = frame.loc[train_index, "default"].astype(int)
    if y_train.nunique() < 2:
        probabilities = np.full(len(frame), float(y_train.mean()))
        model_type = "constant development-period base rate (single-class fallback)"
    else:
        transformer = ColumnTransformer(
            [
                (
                    "numeric",
                    Pipeline(
                        [
                            ("imputer", SimpleImputer(strategy="median")),
                            ("scale", StandardScaler()),
                        ]
                    ),
                    numeric,
                ),
                (
                    "categorical",
                    Pipeline(
                        [
                            ("imputer", SimpleImputer(strategy="most_frequent")),
                            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
                        ]
                    ),
                    categorical,
                ),
            ]
        )
        model = Pipeline(
            [
                ("features", transformer),
                (
                    "logistic_regression",
                    LogisticRegression(max_iter=1000, C=1.0, random_state=seed),
                ),
            ]
        )
        model.fit(features.loc[train_index], y_train)
        probabilities = model.predict_proba(features)[:, 1]
        model_type = "regularized logistic regression"
    monitoring = ~development
    metadata = {
        "model_type": model_type,
        "development_period": {
            "origin_date_start": frame.loc[development, "origin_date"].min().strftime("%Y-%m-%d"),
            "origin_date_end": frame.loc[development, "origin_date"].max().strftime("%Y-%m-%d"),
            "eligible_rows": int(development.sum()),
            "training_rows_used": int(len(train_index)),
            "performance_in_sample": performance_metrics(
                frame.loc[development, "default"], probabilities[development.to_numpy()]
            ),
        },
        "monitoring_period": {
            "origin_date_start": frame.loc[monitoring, "origin_date"].min().strftime("%Y-%m-%d")
            if monitoring.any()
            else None,
            "origin_date_end": frame.loc[monitoring, "origin_date"].max().strftime("%Y-%m-%d")
            if monitoring.any()
            else None,
            "eligible_rows": int(monitoring.sum()),
            "performance_out_of_time": performance_metrics(
                frame.loc[monitoring, "default"], probabilities[monitoring.to_numpy()]
            )
            if monitoring.any()
            else None,
        },
        "features": numeric + categorical,
        "fit_boundary": (
            "Rows with first-disbursement dates before monitoring_start only; "
            "no monitoring-period row was used to fit the model."
        ),
    }
    return probabilities, metadata


def probability_to_score(probabilities: np.ndarray) -> np.ndarray:
    return np.round(300.0 + (1.0 - probabilities) * 550.0, 1)


def _psi_from_shares(reference: np.ndarray, current: np.ndarray) -> float:
    epsilon = 1e-6
    ref = np.clip(reference.astype(float), epsilon, None)
    cur = np.clip(current.astype(float), epsilon, None)
    return round(float(np.sum((cur - ref) * np.log(cur / ref))), 6)


def numeric_psi(
    reference: pd.Series, current: pd.Series, bins: int = 10
) -> float | None:
    reference = pd.to_numeric(reference, errors="coerce").dropna()
    current = pd.to_numeric(current, errors="coerce").dropna()
    if reference.empty or current.empty:
        return None
    quantiles = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(quantiles) < 3:
        return 0.0
    edges = np.concatenate(([-np.inf], quantiles[1:-1], [np.inf]))
    ref_counts, _ = np.histogram(reference, bins=edges)
    cur_counts, _ = np.histogram(current, bins=edges)
    return _psi_from_shares(
        ref_counts / ref_counts.sum(), cur_counts / cur_counts.sum()
    )


def categorical_psi(reference: pd.Series, current: pd.Series) -> float | None:
    ref = reference.fillna("missing").astype(str).value_counts(normalize=True)
    cur = current.fillna("missing").astype(str).value_counts(normalize=True)
    if ref.empty or cur.empty:
        return None
    categories = sorted(set(ref.index) | set(cur.index))
    return _psi_from_shares(
        np.array([ref.get(category, 0.0) for category in categories]),
        np.array([cur.get(category, 0.0) for category in categories]),
    )


def psi_band(value: float | None) -> str:
    if value is None:
        return "not_computable"
    if value < 0.10:
        return "stable_demo_band"
    if value < 0.25:
        return "moderate_shift_demo_band"
    return "high_shift_demo_band"


def cohort_drift(reference: pd.DataFrame, current: pd.DataFrame) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for field in ("score", "amount", "term"):
        value = numeric_psi(reference[field], current[field])
        values[field] = {"psi": value, "band": psi_band(value)}
    for field in ("program", "naics2", "biztype", "region", "delivery"):
        value = categorical_psi(reference[field], current[field])
        values[field] = {"psi": value, "band": psi_band(value)}
    return values


def size_segment(amount: float) -> str:
    if amount < 50_000:
        return "micro"
    if amount < 350_000:
        return "small"
    return "mid"


def score_band(score: float) -> str:
    if score >= 760:
        return "A"
    if score >= 700:
        return "B"
    if score >= 640:
        return "C"
    if score >= 580:
        return "D"
    return "E"


def safe_token(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")


def dump_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def repository_state(repo_root: Path) -> dict[str, Any]:
    def git(*arguments: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    try:
        commit = git("rev-parse", "HEAD")
        status = git("status", "--short")
    except (OSError, subprocess.CalledProcessError) as exc:
        return {"available": False, "error": str(exc)}
    return {
        "available": True,
        "commit": commit,
        "clean": not bool(status),
        "working_tree_status": status.splitlines(),
    }


def run_environment(repo_root: Path, invocation: list[str]) -> dict[str, Any]:
    implementation_paths = [
        repo_root / "src" / "credit_gov" / "sba_to_monitoring.py",
        repo_root / "src" / "credit_gov" / "monitoring.py",
        repo_root / "src" / "credit_gov" / "schemas" / "validators.py",
        repo_root / "src" / "credit_gov" / "schemas" / "models.py",
        repo_root / "schemas" / "monitoring-applicability.schema.json",
        repo_root / "schemas" / "fair-lending-screening-config.schema.json",
    ]
    return {
        "record_type": "run_environment",
        "created_at": now_iso(),
        "invocation": invocation,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "dependencies": {
            name: package_version(name)
            for name in ("numpy", "pandas", "scikit-learn")
        },
        "repository": repository_state(repo_root),
        "implementation_file_hashes": {
            str(path.relative_to(repo_root)).replace("\\", "/"): sha256_file(path)
            for path in implementation_paths
            if path.is_file()
        },
    }


def write_cohort(
    cohort_id: str,
    frame: pd.DataFrame,
    out_dir: Path,
    program_label: str,
    horizon_months: int,
    baseline_default_rate: float,
    baseline_score_average: float,
    effective_date: str = "2020-01-01",
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    token = safe_token(cohort_id.removeprefix("sba-"))
    run_id = f"run-{token}"
    decisions: list[dict[str, Any]] = []
    score_outputs: list[dict[str, Any]] = []
    outcomes: list[dict[str, Any]] = []
    for index, row in frame.reset_index(drop=True).iterrows():
        decision_id = f"dec-{token}-{index:05d}"
        score = float(row["score"])
        origin = row["origin_date"]
        decisions.append(
            {
                "record_type": "application_decision_record",
                "decision_id": decision_id,
                "application_date": origin.strftime("%Y-%m-%d"),
                "segment": size_segment(float(row["amount"])),
                "decision_outcome": "approved",
                "manual_review_flag": False,
                "override_flag": False,
                "underwriting": {
                    "score": score,
                    "requested_amount": round(float(row["amount"]), 2),
                    "decision_timestamp": origin.strftime("%Y-%m-%dT12:00:00Z"),
                },
                "monitoring": {
                    "region": str(row["region"]),
                    "channel": safe_token(str(row["delivery"])) or "unknown",
                    "review_batch_id": run_id,
                },
            }
        )
        score_outputs.append(
            {
                "record_type": "score_output",
                "decision_id": decision_id,
                "score_value": score,
                "score_band": score_band(score),
                "score_version": VERSION_ID,
            }
        )
        outcomes.append(
            {
                "record_type": "outcome_record",
                "outcome_id": f"out-{token}-{index:05d}",
                "decision_id": decision_id,
                "observation_period": f"{horizon_months}m",
                "repayment_or_default_indicator": "default"
                if int(row["default"])
                else "performing",
                "realized_outcome_value": 0.0 if int(row["default"]) else 1.0,
            }
        )

    reasons = {
        "decision_outcome_rates": (
            "The SBA FOIA files contain approved loans only, not the full application decision population."
        ),
        "manual_review": (
            "The SBA FOIA files do not identify underwriting manual-review events."
        ),
        "override_monitoring": (
            "The SBA FOIA files do not identify policy or model override events."
        ),
        "adverse_action_reason_qa": (
            "Approved-loan SBA FOIA records do not contain declined decisions, reason drivers, or notices."
        ),
        "fair_lending_screening": (
            "The approved-loan files lack the applicant decision denominator and protected-class data needed for this screen."
        ),
    }
    dump_json(
        out_dir / "monitoring-applicability.json",
        {
            "record_type": "monitoring_applicability",
            "data_context": "public_data",
            "dataset_name": "SBA 7(a)/504 FOIA approved-loan extract",
            "modules": {
                name: {"applicable": False, "reason": reason}
                for name, reason in reasons.items()
            },
        },
    )
    dump_json(
        out_dir / "model-registry-record.json",
        {
            "record_type": "model_registry_record",
            "model_id": MODEL_ID,
            "model_name": f"{program_label} fixed-horizon public-data demonstration model",
            "business_owner": "Small Business Credit Risk (demonstration)",
            "technical_owner": "Model Risk Governance (demonstration)",
            "intended_use": (
                "Demonstrate fixed-horizon outcome monitoring and out-of-time drift controls; "
                "not an underwriting model or lending recommendation."
            ),
            "target_population": f"Seasoned approved {program_label} loans in the public FOIA files",
            "status": "active",
            "monitoring_only_fields": ["region", "channel", "review_batch_id"],
            "underwriting_fields": ["score", "requested_amount", "decision_timestamp"],
        },
    )
    dump_json(
        out_dir / "model-version-record.json",
        {
            "record_type": "model_version_record",
            "model_id": MODEL_ID,
            "version_id": VERSION_ID,
            "effective_date": effective_date,
            "change_summary": (
                "Fixed-horizon charge-off labeling with a pre-monitoring development split "
                "and explicit applicability controls."
            ),
            "assumptions": [
                f"Default means a recorded charge-off date on or before {horizon_months} months after first disbursement.",
                "A nondefault observation is included only when the file as-of date reaches the same horizon.",
            ],
            "limitations": [
                "Approved-loan public data cannot measure approval, decline, manual-review, or override rates.",
                "No applicant protected-class fields, adverse-action reasons, notices, or model drivers are present.",
                "The schema field requested_amount stores GrossApproval because this is a booked-loan file.",
                "The model is a monitoring demonstration, not evidence of production use, adoption, or regulatory compliance.",
            ],
            "linked_validation_record": "val-sba-public-demo-v2",
        },
    )
    dump_json(
        out_dir / "threshold-set.json",
        {
            "record_type": "threshold_set",
            "threshold_set_id": f"thr-{token}",
            "model_id": MODEL_ID,
            "version_id": VERSION_ID,
            "review_cadence": "monthly",
            "thresholds": [
                {
                    "metric_name": "default_rate",
                    "comparison_rule": "greater_than",
                    "threshold_value": round(min(1.0, baseline_default_rate + 0.05), 6),
                    "severity": "high",
                    "escalation_owner": "Model Risk Governance",
                },
                {
                    "metric_name": "score_average",
                    "comparison_rule": "less_than",
                    "threshold_value": round(max(0.0, baseline_score_average - 25.0), 4),
                    "severity": "medium",
                    "escalation_owner": "Model Risk Governance",
                },
            ],
        },
    )
    dump_json(
        out_dir / "fair-lending-screening-config.json",
        {
            "record_type": "fair_lending_screening_config",
            "screening_config_id": f"fls-{token}",
            "model_id": MODEL_ID,
            "version_id": VERSION_ID,
            "minimum_group_size": 30,
            "alpha": 0.05,
            "applicable": False,
            "not_applicable_reason": reasons["fair_lending_screening"],
            "comparison_groups": [],
            "screens": [],
        },
    )
    dump_json(out_dir / "application-decision-records.json", decisions)
    dump_json(out_dir / "score-outputs.json", score_outputs)
    dump_json(out_dir / "outcome-records.json", outcomes)
    dump_json(out_dir / "reason-code-mappings.json", [])
    dump_json(out_dir / "adverse-action-reason-outputs.json", [])
    dump_json(out_dir / "override-events.json", [])
    dump_json(out_dir / "breach-records.json", [])
    inputs = [
        "monitoring-applicability.json",
        "model-registry-record.json",
        "model-version-record.json",
        "threshold-set.json",
        "fair-lending-screening-config.json",
        "application-decision-records.json",
        "score-outputs.json",
        "outcome-records.json",
        "reason-code-mappings.json",
        "adverse-action-reason-outputs.json",
        "override-events.json",
        "breach-records.json",
    ]
    dump_json(
        out_dir / "evidence-pack-manifest.json",
        {
            "record_type": "evidence_pack_manifest",
            "run_id": run_id,
            "created_at": now_iso(),
            "model_id": MODEL_ID,
            "version_id": VERSION_ID,
            "input_references": inputs,
            "output_files": [
                "metric_results.json",
                "breach_register.json",
                "reason_qa_results.json",
                "reason_stability_report.json",
                "fair_lending_screening_results.json",
                "fair_lending_escalation_register.json",
                "reviewer_notes.md",
                "monitoring_report.md",
            ],
            "reviewer_status": "pending_review",
        },
    )
    return {
        "cohort": cohort_id,
        "evidence_sample_rows": len(frame),
        "sample_default_rate": round(float(frame["default"].mean()), 6),
        "sample_score_average": round(float(frame["score"].mean()), 4),
        "program_scope": program_label,
    }


def program_scope_label(program: str) -> str:
    return {"7a": "SBA 7(a)", "504": "SBA 504"}.get(
        program, "SBA 7(a)/504"
    )


def write_run_summary(
    out_root: Path, metadata: dict[str, Any], rows: list[dict[str, Any]]
) -> None:
    lines = [
        "# SBA Public-Data Monitoring Run Summary",
        "",
        "This run uses approved-loan public data and a demonstration model. It is not an underwriting, adoption, or compliance claim.",
        "",
        f"- Created: {metadata['created_at']}",
        f"- Fixed outcome horizon: {metadata['horizon_months']} months after first disbursement",
        f"- Monitoring start: {metadata['monitoring_start']}",
        f"- Eligible labeled rows: {metadata['eligible_rows']}",
        f"- Development rows: {metadata['development_rows']}",
        f"- Monitoring rows: {metadata['monitoring_rows']}",
        "",
        "## Cohorts",
        "",
        "| Cohort | Full rows | Default rate | Score average | Workflow |",
        "|---|---:|---:|---:|---|",
    ]
    for row in rows:
        workflow = "passed" if row["workflow_ok"] else "failed"
        lines.append(
            f"| {row['cohort']} | {row['full_cohort_rows']} | {row['default_rate']} | "
            f"{row['score_average']} | {workflow} |"
        )
    lines += [
        "",
        "## Interpretation Boundary",
        "",
        "The meaningful outputs are fixed-horizon default performance, score behavior, and portfolio-composition drift. Approval, decline, manual-review, override, adverse-action-reason, and fair-lending modules are recorded as not applicable because the source fields are absent.",
        "",
    ]
    (out_root / "run_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_output_hashes(out_root: Path) -> None:
    hashes = {
        str(path.relative_to(out_root)).replace("\\", "/"): sha256_file(path)
        for path in sorted(out_root.rglob("*"))
        if path.is_file() and path.name != "output_hashes.json"
    }
    dump_json(out_root / "output_hashes.json", {"algorithm": "sha256", "files": hashes})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", nargs="+", required=True, help="One or more official-layout SBA CSV files."
    )
    parser.add_argument(
        "--source-url",
        action="append",
        default=[],
        help="Repeat once per input to record its download URL.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Accepted for compatibility; the installed package is canonical.",
    )
    parser.add_argument("--out-root", default="model_risk_oversight_sba_run")
    parser.add_argument("--program", choices=["all", "7a", "504"], default="all")
    parser.add_argument("--horizon-months", type=int, default=36)
    parser.add_argument("--monitoring-start", default="2020-01-01")
    parser.add_argument("--cohort", choices=["month", "year"], default="year")
    parser.add_argument("--max-cohorts", type=int, default=6)
    parser.add_argument("--sample-per-cohort", type=int, default=500)
    parser.add_argument("--max-training-rows", type=int, default=250_000)
    parser.add_argument("--chunksize", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=7)
    return parser


def main(argv: list[str] | None = None) -> int:
    require_public_data_dependencies()
    args = build_parser().parse_args(argv)
    if args.horizon_months <= 0 or args.sample_per_cohort <= 0 or args.max_cohorts <= 0:
        raise SystemExit("horizon, sample size, and cohort count must be positive")
    input_paths = [Path(value) for value in args.input]
    frame, provenance = load_and_prepare(
        input_paths,
        horizon_months=args.horizon_months,
        selected_program=args.program,
        chunksize=args.chunksize,
        source_urls=args.source_url,
    )
    monitoring_start = pd.Timestamp(args.monitoring_start)
    probabilities, model_metadata = train_out_of_time_model(
        frame, monitoring_start, args.max_training_rows, args.seed
    )
    frame["predicted_default_probability"] = probabilities
    frame["score"] = probability_to_score(probabilities)
    features = model_features(frame)
    frame["region"] = features["region"]

    development = frame["origin_date"].lt(monitoring_start)
    monitoring = ~development
    if not monitoring.any():
        raise SystemExit("No eligible monitoring rows on or after --monitoring-start")
    reference = frame.loc[development]
    baseline_default_rate = float(reference["default"].mean())
    baseline_score_average = float(reference["score"].mean())

    format_string = "%Y-%m" if args.cohort == "month" else "%Y"
    frame["cohort_key"] = frame["origin_date"].dt.strftime(format_string)
    monitoring_frame = frame.loc[monitoring]
    cohort_sizes = monitoring_frame.groupby("cohort_key").size()
    selected = list(cohort_sizes[cohort_sizes >= 30].index[-args.max_cohorts :])
    if not selected:
        selected = list(cohort_sizes.index[-args.max_cohorts :])

    out_root = Path(args.out_root).resolve()
    (out_root / "datasets").mkdir(parents=True, exist_ok=True)
    (out_root / "evidence").mkdir(parents=True, exist_ok=True)
    invocation = [sys.executable, *sys.argv] if argv is None else [sys.executable, *argv]
    dump_json(
        out_root / "run_environment.json",
        run_environment(Path(args.repo_root).resolve(), invocation),
    )
    dump_json(out_root / "source_provenance.json", provenance)
    dump_json(
        out_root / "row_disposition.json",
        {
            "label_definition": (
                f"charge-off date on or before {args.horizon_months} months after first disbursement"
            ),
            "nondefault_seasoning_rule": (
                "file as-of date must reach the same fixed horizon"
            ),
            "counts": provenance["combined_row_disposition"],
        },
    )
    methodology = {
        "record_type": "public_data_monitoring_methodology",
        "created_at": now_iso(),
        "horizon_months": args.horizon_months,
        "time_origin": "FirstDisbursementDate",
        "event_date": "ChargeOffDate",
        "censor_date": "AsOfDate",
        "status_normalization": (
            "Uppercase and remove all non-alphanumeric characters; P I F becomes PIF."
        ),
        "development_rule": (
            f"FirstDisbursementDate before {monitoring_start.strftime('%Y-%m-%d')}"
        ),
        "monitoring_rule": (
            f"FirstDisbursementDate on or after {monitoring_start.strftime('%Y-%m-%d')}"
        ),
        "model": model_metadata,
        "psi_interpretive_bands": {
            "stable": "<0.10",
            "moderate_shift": "0.10 to <0.25",
            "high_shift": ">=0.25",
            "status": "demonstration review bands, not universal policy limits",
        },
        "nonclaims": [
            "No application approval or decline population is present.",
            "No override, manual-review, adverse-action-reason, notice, or protected-class fields are present.",
            "Outputs do not establish production use, institutional adoption, model validity for lending, or compliance.",
        ],
    }
    dump_json(out_root / "methodology.json", methodology)
    dump_json(out_root / "model_performance.json", model_metadata)

    from .monitoring import run_monthly_monitoring

    rng = np.random.default_rng(args.seed)
    summary_rows: list[dict[str, Any]] = []
    program_label = program_scope_label(args.program)
    for cohort in selected:
        full = monitoring_frame[monitoring_frame["cohort_key"] == cohort].copy()
        sample = full
        if len(full) > args.sample_per_cohort:
            selected_indexes = rng.choice(
                full.index.to_numpy(), size=args.sample_per_cohort, replace=False
            )
            sample = full.loc[selected_indexes].copy()
        cohort_id = f"sba-{cohort}"
        dataset_dir = out_root / "datasets" / cohort_id
        stats = write_cohort(
            cohort_id,
            sample,
            dataset_dir,
            program_label,
            args.horizon_months,
            baseline_default_rate,
            baseline_score_average,
            monitoring_start.strftime("%Y-%m-%d"),
        )
        result = run_monthly_monitoring(
            dataset_dir=dataset_dir, evidence_root=out_root / "evidence"
        )
        full_probabilities = full["predicted_default_probability"].to_numpy()
        row = {
            **stats,
            "full_cohort_rows": len(full),
            "default_rate": round(float(full["default"].mean()), 6),
            "score_average": round(float(full["score"].mean()), 4),
            "default_rate_delta_from_development": round(
                float(full["default"].mean() - baseline_default_rate), 6
            ),
            "model_performance": performance_metrics(
                full["default"], full_probabilities
            ),
            "drift_vs_development": cohort_drift(reference, full),
            "workflow_ok": result.ok,
            "workflow_errors": result.errors,
            "evidence_dir": result.output_dir,
            "module_status": {
                "decision_outcome_rates": "not_applicable",
                "manual_review": "not_applicable",
                "override_monitoring": "not_applicable",
                "adverse_action_reason_qa": "not_applicable",
                "fair_lending_screening": "not_applicable",
            },
        }
        summary_rows.append(row)
        print(
            f"[{cohort_id}] full_n={row['full_cohort_rows']} "
            f"sample_n={stats['evidence_sample_rows']} "
            f"default_rate={row['default_rate']} workflow_ok={result.ok}"
        )
    dump_json(out_root / "cross_cohort_drift_summary.json", summary_rows)
    flat_rows = [
        {
            "cohort": row["cohort"],
            "full_cohort_rows": row["full_cohort_rows"],
            "evidence_sample_rows": row["evidence_sample_rows"],
            "default_rate": row["default_rate"],
            "score_average": row["score_average"],
            "roc_auc": row["model_performance"]["roc_auc"],
            "brier_score": row["model_performance"]["brier_score"],
            "score_psi": row["drift_vs_development"]["score"]["psi"],
            "amount_psi": row["drift_vs_development"]["amount"]["psi"],
            "workflow_ok": row["workflow_ok"],
        }
        for row in summary_rows
    ]
    pd.DataFrame(flat_rows).to_csv(
        out_root / "cross_cohort_drift_summary.csv", index=False
    )
    run_metadata = {
        "created_at": now_iso(),
        "horizon_months": args.horizon_months,
        "monitoring_start": monitoring_start.strftime("%Y-%m-%d"),
        "eligible_rows": len(frame),
        "development_rows": int(development.sum()),
        "monitoring_rows": int(monitoring.sum()),
    }
    write_run_summary(out_root, run_metadata, summary_rows)
    write_output_hashes(out_root)
    if not all(row["workflow_ok"] for row in summary_rows):
        return 1
    print(f"Reproducible run written to {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
