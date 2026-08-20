"""Adapter: SBA 7(a)/504 FOIA approved-loan CSV -> credit_gov monitoring datasets.

Reads a real SBA 7(a)/504 FOIA extract, trains a transparent DEMONSTRATION
default-risk model (logistic regression on non-protected loan features),
splits loans into monthly cohorts, and writes, for each cohort, the JSON input
files the public repo's Phase 2 monitoring workflow consumes. It then runs that
workflow per cohort and writes a cross-cohort drift summary.

SCOPE & LIMITATIONS (read before reusing these outputs):
- The default-risk model is a GOVERNED-MODEL STAND-IN so the monitoring
  workflow has something to monitor. It is NOT a proposed underwriting model
  and makes no lending recommendation.
- SBA FOIA is APPROVED-ONLY with no applicant demographics. Therefore
  decline_rate, override_rate, adverse-action reason QA, and fair-lending
  disparity are NOT meaningful on this dataset; those input files are
  schema-required placeholders and their derived metrics must be excluded from
  interpretation. The MEANINGFUL SBA signals are: score distribution & drift,
  charge-off (outcome) mix, and portfolio-composition drift across cohorts.
- Do not use this adapter for fairness, adverse-action, protected-class, or
  applicant-demographics claims. Those claims require the relevant application,
  decision, demographic/proxy, driver, notice, or review fields.

Usage:
  python scripts/sba_to_monitoring.py \
      --input data/sba-7a-504.csv \
      --repo-root . \
      --out-root model_risk_oversight_sba_run \
      --program all \
      --cohort month --max-cohorts 6 --sample-per-cohort 500
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
except ImportError as exc:  # pragma: no cover - exercised only without optional deps
    np = None
    pd = None
    LogisticRegression = None
    StandardScaler = None
    PUBLIC_DATA_IMPORT_ERROR = exc
else:
    PUBLIC_DATA_IMPORT_ERROR = None

CENSUS_REGION = {
    **{s: "west" for s in ["CA", "WA", "OR", "NV", "AZ", "CO", "UT", "ID", "MT", "WY", "NM", "AK", "HI"]},
    **{s: "midwest" for s in ["IL", "OH", "MI", "IN", "WI", "MN", "IA", "MO", "KS", "NE", "SD", "ND"]},
    **{s: "south" for s in ["TX", "FL", "GA", "NC", "SC", "VA", "TN", "AL", "MS", "LA", "AR", "OK", "KY", "WV", "MD", "DE", "DC"]},
    **{s: "northeast" for s in ["NY", "PA", "MA", "NJ", "CT", "RI", "NH", "VT", "ME"]},
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pick(df: pd.DataFrame, *candidates: str) -> str | None:
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def load_and_prepare(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    cols = {
        "amount": pick(df, "GrossApproval", "GrossApproval$", "gross_approval"),
        "term": pick(df, "TermInMonths", "TermMonths", "term"),
        "date": pick(df, "ApprovalDate", "approval_date"),
        "fy": pick(df, "ApprovalFiscalYear", "FiscalYear"),
        "state": pick(df, "BorrState", "ProjectState", "state"),
        "delivery": pick(df, "ProcessingMethod", "DeliveryMethod", "delivery"),
        "program": pick(df, "Program"),
        "biztype": pick(df, "BusinessType", "business_type"),
        "jobs": pick(df, "JobsSupported", "jobs"),
        "naics": pick(df, "NaicsCode", "NAICSCode", "naics"),
        "status": pick(df, "LoanStatus", "status"),
        "chargeoff": pick(df, "GrossChargeOffAmount", "ChargeOffAmount"),
    }
    missing = [k for k in ("amount", "term", "status") if cols[k] is None]
    if missing:
        raise SystemExit(f"Required columns not found: {missing}. Got: {list(df.columns)[:30]}")

    out = pd.DataFrame()
    out["amount"] = pd.to_numeric(df[cols["amount"]], errors="coerce")
    out["term"] = pd.to_numeric(df[cols["term"]], errors="coerce")
    out["state"] = df[cols["state"]].astype(str).str.strip().str.upper() if cols["state"] else "NA"
    out["delivery"] = df[cols["delivery"]].astype(str).str.strip() if cols["delivery"] else "unknown"
    out["program"] = df[cols["program"]].astype(str).str.strip().str.upper() if cols["program"] else "NA"
    out["biztype"] = df[cols["biztype"]].astype(str).str.strip().str.upper() if cols["biztype"] else "NA"
    out["jobs"] = pd.to_numeric(df[cols["jobs"]], errors="coerce").fillna(0) if cols["jobs"] else 0
    out["naics2"] = df[cols["naics"]].astype(str).str[:2] if cols["naics"] else "00"
    status = df[cols["status"]].astype(str).str.upper().str.strip()

    # date / cohort
    if cols["date"]:
        dt = pd.to_datetime(df[cols["date"]], errors="coerce")
    elif cols["fy"]:
        dt = pd.to_datetime(df[cols["fy"]].astype(str) + "-01-01", errors="coerce")
    else:
        raise SystemExit("Need ApprovalDate or ApprovalFiscalYear for cohorting.")
    out["date"] = dt

    # default label: charge-off. Keep only matured/terminated loans (PIF/CHGOFF)
    co_amt = pd.to_numeric(df[cols["chargeoff"]], errors="coerce").fillna(0) if cols["chargeoff"] else 0
    is_chgoff = status.str.contains("CHGOFF") | status.str.contains("CHARGED") | (np.asarray(co_amt) > 0)
    is_pif = status.str.contains("PIF") | status.str.contains("PAID")
    out["default"] = is_chgoff.astype(int)
    out["matured"] = (is_chgoff | is_pif).astype(int)

    out = out.dropna(subset=["amount", "term", "date"])
    out = out[out["matured"] == 1].copy()
    out = out[(out["date"].dt.year >= 2010)].copy()  # FY2010+ per data-quality note
    out = out.reset_index(drop=True)
    if out.empty:
        raise SystemExit("No matured (PIF/CHGOFF) FY2010+ rows after cleaning.")
    return out


def train_demo_model(df: pd.DataFrame) -> np.ndarray:
    """Transparent demonstration PD model. Returns a 300-850-style score."""
    num = np.column_stack([
        np.log1p(df["amount"].to_numpy()),
        df["term"].to_numpy(dtype=float),
        np.log1p(df["jobs"].to_numpy(dtype=float)),
    ])
    top_naics = df["naics2"].value_counts().head(8).index
    naics_oh = pd.get_dummies(df["naics2"].where(df["naics2"].isin(top_naics), "OTHER")).to_numpy(dtype=float)
    biz_oh = pd.get_dummies(df["biztype"]).to_numpy(dtype=float)
    X = np.hstack([StandardScaler().fit_transform(num), naics_oh, biz_oh])
    y = df["default"].to_numpy()
    if y.sum() < 5 or (len(y) - y.sum()) < 5:
        pd_hat = np.full(len(y), y.mean())
    else:
        clf = LogisticRegression(max_iter=1000, C=1.0)
        clf.fit(X, y)
        pd_hat = clf.predict_proba(X)[:, 1]
    score = 300 + (1.0 - pd_hat) * 550.0
    return np.round(score, 1)


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


MODEL_ID = "mdl-sba-public-monitoring-demo"
VERSION_ID = "ver-sba-public-monitoring-1"
MAP_VERSION = "mapver-sba-public-monitoring-1"


def program_scope_label(program: str) -> str:
    if program == "7a":
        return "SBA 7(a)"
    if program == "504":
        return "SBA 504"
    return "SBA 7(a)/504"


def write_cohort(cohort_id: str, sub: pd.DataFrame, scores: np.ndarray, out_dir: Path, program_label: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    c = cohort_id[4:] if cohort_id.startswith("sba-") else cohort_id
    run_token = f"run-{c}"
    decisions, score_outputs, outcomes = [], [], []
    for i, (_, row) in enumerate(sub.iterrows()):
        did = f"dec-{c}-{i:05d}"
        sc = float(scores[i])
        ts = row["date"].strftime("%Y-%m-%dT12:00:00Z")
        decisions.append({
            "record_type": "application_decision_record",
            "decision_id": did,
            "application_date": row["date"].strftime("%Y-%m-%d"),
            "segment": size_segment(float(row["amount"])),
            "decision_outcome": "approved",
            "manual_review_flag": False,
            "override_flag": False,  # SBA approved-only: no override data (override_rate=0, truthful)
            "underwriting": {
                "score": sc,
                "requested_amount": round(float(row["amount"]), 2),
                "decision_timestamp": ts,
            },
            "monitoring": {
                "region": CENSUS_REGION.get(str(row["state"]), "other"),
                "channel": str(row["delivery"]).lower().replace(" ", "_") or "unknown",
                "review_batch_id": run_token,
            },
        })
        score_outputs.append({
            "record_type": "score_output",
            "decision_id": did,
            "score_value": sc,
            "score_band": score_band(sc),
            "score_version": VERSION_ID,
        })
        outcomes.append({
            "record_type": "outcome_record",
            "outcome_id": f"out-{c}-{i:05d}",
            "decision_id": did,
            "observation_period": "60m",
            "repayment_or_default_indicator": "default" if int(row["default"]) == 1 else "performing",
            "realized_outcome_value": 0.0 if int(row["default"]) == 1 else 1.0,
        })

    def dump(name, obj):
        (out_dir / name).write_text(json.dumps(obj, indent=2), encoding="utf-8")

    dump("model-registry-record.json", {
        "record_type": "model_registry_record",
        "model_id": MODEL_ID,
        "model_name": f"{program_label} Public-Data Monitoring Demonstration Model (governance stand-in)",
        "business_owner": "Small Business Credit Risk (demonstration)",
        "technical_owner": "Model Risk Governance (demonstration)",
        "intended_use": f"Governance demonstration only. Risk-ranks matured {program_label} approved loans so the monitoring workflow has a governed model to monitor. Not an underwriting recommendation.",
        "target_population": f"Matured U.S. {program_label} small-business loans (approved-only public FOIA data)",
        "status": "active",
        "monitoring_only_fields": ["region", "channel", "review_batch_id"],
        "underwriting_fields": ["score", "requested_amount", "decision_timestamp"],
    })
    dump("model-version-record.json", {
        "record_type": "model_version_record",
        "model_id": MODEL_ID,
        "version_id": VERSION_ID,
        "effective_date": "2026-01-01",
        "change_summary": f"Demonstration default-risk model trained on real {program_label} FOIA matured loans.",
        "assumptions": [
            f"{program_label} FOIA is approved-only; no declines or applicant demographics are present.",
            "Default label = charge-off among matured (PIF/CHGOFF) loans.",
        ],
        "limitations": [
            "Governed-model stand-in for a monitoring demonstration; not a proposed underwriting model.",
            "decline_rate, override_rate, reason-QA, and fair-lending disparity are not meaningful on approved-only data.",
        ],
        "linked_validation_record": "val-sba-demo",
    })
    dump("threshold-set.json", {
        "record_type": "threshold_set",
        "threshold_set_id": f"thr-{c}",
        "model_id": MODEL_ID,
        "version_id": VERSION_ID,
        "review_cadence": "monthly",
        "thresholds": [
            {"metric_name": "override_rate", "comparison_rule": "greater_than", "threshold_value": 0.1, "severity": "high", "escalation_owner": "Credit Policy Review"},
            {"metric_name": "manual_review_rate", "comparison_rule": "greater_than", "threshold_value": 0.5, "severity": "medium", "escalation_owner": "Model Risk Governance"},
        ],
    })
    dump("fair-lending-screening-config.json", {
        "record_type": "fair_lending_screening_config",
        "screening_config_id": f"fls-{c}",
        "model_id": MODEL_ID,
        "version_id": VERSION_ID,
        "minimum_group_size": 30,
        "alpha": 0.05,
        "comparison_groups": [
            {"group_name": "region", "source": "monitoring", "field": "region"},
            {"group_name": "segment", "source": "decision", "field": "segment"},
        ],
        "screens": [
            {"screen_name": "Regional approval-rate ratio", "metric_name": "approval_rate_ratio", "comparison_rule": "less_than", "threshold_value": 0.8, "severity": "medium", "escalation_owner": "Fair Lending Review"},
            {"screen_name": "Regional override-rate difference", "metric_name": "override_rate_difference", "comparison_rule": "greater_than", "threshold_value": 0.25, "severity": "medium", "escalation_owner": "Fair Lending Review"},
        ],
    })
    dump("reason-code-mappings.json", [
        {"record_type": "reason_code_mapping", "mapping_id": "map-001", "version_id": VERSION_ID, "driver_or_signal": "loan_amount", "reason_code": "RC-201", "reason_text": "Requested amount relative to profile", "mapping_version": MAP_VERSION},
        {"record_type": "reason_code_mapping", "mapping_id": "map-002", "version_id": VERSION_ID, "driver_or_signal": "term_length", "reason_code": "RC-202", "reason_text": "Term length relative to profile", "mapping_version": MAP_VERSION},
    ])
    dump("application-decision-records.json", decisions)
    dump("score-outputs.json", score_outputs)
    dump("outcome-records.json", outcomes)
    dump("adverse-action-reason-outputs.json", [])
    dump("breach-records.json", [])
    dump("override-events.json", [{
        "record_type": "override_event",
        "override_id": f"ovr-{c}-placeholder",
        "decision_id": decisions[0]["decision_id"],
        "override_type": "policy_exception",
        "override_reason": "SCHEMA_PLACEHOLDER: SBA FOIA has no override data; this record only satisfies the non-empty file requirement. override_rate is not a meaningful SBA metric.",
        "reviewer": "n/a",
        "override_date": decisions[0]["application_date"],
    }])
    dump("evidence-pack-manifest.json", {
        "record_type": "evidence_pack_manifest",
        "run_id": run_token,
        "created_at": now_iso(),
        "model_id": MODEL_ID,
        "version_id": VERSION_ID,
        "input_references": [
            "model-registry-record.json", "model-version-record.json", "threshold-set.json",
            "fair-lending-screening-config.json", "application-decision-records.json",
            "adverse-action-reason-outputs.json",
        ],
        "output_files": [
            "metric_results.json", "breach_register.json", "reason_qa_results.json",
            "reason_stability_report.json", "fair_lending_screening_results.json",
            "fair_lending_escalation_register.json", "reviewer_notes.md", "monitoring_report.md",
        ],
        "reviewer_status": "pending_review",
    })
    return {
        "cohort": cohort_id,
        "n_loans": len(sub),
        "default_rate": round(float(sub["default"].mean()), 4),
        "mean_score": round(float(np.mean(scores)), 1),
        "program_scope": program_label,
    }


def require_public_data_dependencies() -> None:
    if PUBLIC_DATA_IMPORT_ERROR is not None:
        raise SystemExit(
            "Missing optional public-data dependencies. Install with "
            "`python -m pip install credit-gov[public-data]` or "
            "`python -m pip install -e .[public-data]` from a source checkout."
        ) from PUBLIC_DATA_IMPORT_ERROR


def main() -> None:
    require_public_data_dependencies()
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--out-root", default="model_risk_oversight_sba_run")
    ap.add_argument("--cohort", choices=["month", "year"], default="month")
    ap.add_argument("--max-cohorts", type=int, default=6)
    ap.add_argument("--sample-per-cohort", type=int, default=500)
    ap.add_argument("--program", choices=["all", "7a", "504"], default="all", help="Filter a combined SBA 7(a)/504 file by program.")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    sys.path.insert(0, str(repo_root / "src"))
    from credit_gov.monitoring import run_monthly_monitoring  # noqa: E402

    df = load_and_prepare(Path(args.input))
    program_label = program_scope_label(args.program)
    if args.program != "all":
        if df["program"].eq("NA").all():
            raise SystemExit("--program filtering requires a Program column; rerun with --program all for a single-program file.")
        is504 = df["program"].str.contains("504")
        df = df[is504 if args.program == "504" else ~is504].reset_index(drop=True)
        if df.empty:
            raise SystemExit(f"No rows for program={args.program}")
    df["score"] = train_demo_model(df)

    key = df["date"].dt.strftime("%Y-%m" if args.cohort == "month" else "%Y")
    df["cohort_key"] = key
    cohorts = [c for c in sorted(df["cohort_key"].unique())]
    # keep the most recent cohorts with enough loans
    sized = [(c, (df["cohort_key"] == c).sum()) for c in cohorts]
    sized = [c for c, n in sized if n >= 30][-args.max_cohorts:]
    if not sized:
        sized = cohorts[-args.max_cohorts:]

    out_root = Path(args.out_root).resolve()
    (out_root / "datasets").mkdir(parents=True, exist_ok=True)
    (out_root / "evidence").mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    summary_rows = []
    for c in sized:
        sub = df[df["cohort_key"] == c]
        if len(sub) > args.sample_per_cohort:
            idx = rng.choice(sub.index.to_numpy(), size=args.sample_per_cohort, replace=False)
            sub = sub.loc[idx]
        sub = sub.reset_index(drop=True)
        cohort_id = f"sba-{c}"
        ds_dir = out_root / "datasets" / cohort_id
        stats = write_cohort(cohort_id, sub, sub["score"].to_numpy(), ds_dir, program_label)
        result = run_monthly_monitoring(dataset_dir=ds_dir, evidence_root=out_root / "evidence")
        stats["workflow_ok"] = result.ok
        stats["evidence_dir"] = result.output_dir
        stats["outcome_summary"] = result.metrics.get("outcome_summary") if result.ok else None
        stats["score_avg"] = result.metrics.get("score_distribution", {}).get("average") if result.ok else None
        summary_rows.append(stats)
        print(f"[{cohort_id}] n={stats['n_loans']} default_rate={stats['default_rate']} "
              f"mean_score={stats['mean_score']} workflow_ok={result.ok}")

    sdf = pd.DataFrame(summary_rows)
    sdf.to_csv(out_root / "cross_cohort_drift_summary.csv", index=False)
    (out_root / "cross_cohort_drift_summary.json").write_text(sdf.to_json(orient="records", indent=2), encoding="utf-8")
    print("\nCross-cohort drift summary written to", out_root / "cross_cohort_drift_summary.csv")
    print(sdf[["cohort", "n_loans", "default_rate", "score_avg"]].to_string(index=False))


if __name__ == "__main__":
    main()
