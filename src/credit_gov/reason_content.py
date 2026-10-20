"""Fail-closed local export of reviewed adverse-action reason content.

This boundary checks reason content and declared review records. It never grants
operational authorization or validates a complete notice, lending system,
delivery, or regulatory compliance. Diagnostic generation remains available.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from credit_gov.monitoring import compute_reason_qa, load_dataset_payloads
from credit_gov.reason_fidelity import source_components_for_decision
from credit_gov.result_scope import non_authorization_fields as _authorization_boundary
from credit_gov.schemas import validate_dataset
from credit_gov.schemas.models import require_utc_timestamp
from credit_gov.schemas import validators


GATE_VERSION = "reason-content-review-v4"
REVIEW_FILE = "reason-content-review.json"
LEGACY_REVIEW_FILE = "final-use-review.json"
REQUIRED_REVIEWS = (
    "actual_factors_and_principal_reasons",
    "specificity_and_accuracy",
    "notice_applicability_and_timing",
    "lifecycle_basis",
)
SCOPE = "reason_content_checks_only_not_full_notice_or_operational_authorization"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON number: {value}")


def _finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("JSON number is outside the finite numeric range.")
    return result


def _json(data: bytes) -> Any:
    return json.loads(data, object_pairs_hook=_strict_object,
                      parse_constant=_reject_constant, parse_float=_finite_float)


def _snapshot(dataset_dir: Path) -> dict[str, bytes]:
    if not dataset_dir.is_dir():
        raise ValueError("Dataset directory is missing.")
    result = {}
    for path in sorted(dataset_dir.iterdir()):
        if path.suffix.lower() != ".json":
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError("Dataset JSON inputs must be regular files, not links or directories.")
        result[path.name] = path.read_bytes()
    return result


def _control_fingerprints() -> dict[str, str]:
    """Bind review to the installed control sources and effective schemas.

    This is change detection in a trusted local process, not executable
    attestation or authentication of the reviewer.
    """
    package = Path(__file__).resolve().parent
    sources = (
        "__init__.py", "reason_content.py", "monitoring.py", "reason_fidelity.py", "result_scope.py",
        "schemas/__init__.py", "schemas/models.py", "schemas/validators.py",
        "schemas/governance_models.py",
    )
    result = {f"package/{name}": hashlib.sha256((package / name).read_bytes()).hexdigest()
              for name in sources}
    schema_names = {spec.schema_file for spec in (
        *validators.SCHEMA_SPECS, *validators.OPTIONAL_GOVERNANCE_SCHEMA_SPECS,
    )} | {"monitoring-applicability.schema.json", "rendered-adverse-action-notice.schema.json"}
    for name in sorted(schema_names):
        path = validators.SCHEMA_DIR / name
        if not path.is_file():
            path = package / "schemas/json" / name
        result[f"schemas/{name}"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _binding(files: dict[str, bytes], controls: dict[str, str]) -> tuple[str, dict[str, str]]:
    hashes = {
        name: hashlib.sha256(data).hexdigest()
        for name, data in files.items() if name != REVIEW_FILE
    }
    binding = json.dumps(
        {"gate_version": GATE_VERSION, "input_sha256": hashes, "control_sha256": controls},
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(binding).hexdigest(), hashes


class _CapturedPath:
    """Read-only adapter for existing path-based validators over captured bytes.

    References outside the captured, flat input set are absent. Validation and
    QA therefore cannot read newer files or follow external manifest paths.
    """

    def __init__(self, files: dict[str, bytes], name: str = ""):
        self.files, self.name = files, name

    def __truediv__(self, name: str) -> _CapturedPath:
        return _CapturedPath(self.files, f"{self.name}/{name}" if self.name else name)

    def __str__(self) -> str:
        return "captured-dataset/" + self.name

    def is_file(self) -> bool:
        return self.name in self.files

    def open(self, encoding: str = "utf-8") -> io.StringIO:
        return io.StringIO(self.files[self.name].decode(encoding))


def _nonempty(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string.")


def _unique(records: list[dict[str, Any]], field: str, label: str) -> None:
    values = [record[field] for record in records]
    if len(values) != len(set(values)):
        raise ValueError(f"{label}: ambiguous duplicate {field}.")


def _validate_reason_records(payloads: dict[str, Any]) -> None:
    """Apply the export boundary's additional record and coverage checks.

    Policy, template and method configuration is validated by the shared
    build_reason_fidelity_context used by compute_reason_qa and generation.
    Missing or inapplicable QA can never satisfy this boundary.
    """
    mappings = payloads["reason_mappings"]
    for field in ("reason_code", "driver_or_signal"):
        _unique(mappings, field, "reason mappings")
    used_codes = {output["reason_code"] for output in payloads["reason_outputs"]}
    for mapping in mappings:
        if mapping["reason_code"] in used_codes:
            if "effective_date" not in mapping or "retired_date" not in mapping:
                raise ValueError("Used mapping lifecycle requires explicit effective and retirement status.")
            if mapping["retired_date"] is not None and mapping["retired_date"] <= mapping["effective_date"]:
                raise ValueError("Used mapping retirement must follow its effective date.")
    outputs_by_decision: dict[str, list[dict[str, Any]]] = {}
    for output in payloads["reason_outputs"]:
        outputs_by_decision.setdefault(output["decision_id"], []).append(output)
    for outputs in outputs_by_decision.values():
        identities = [(item.get("source_decision_component", item.get("decision_component")),
                       item["driver_or_signal"]) for item in outputs]
        if len(identities) != len(set(identities)):
            raise ValueError("Duplicate source reason within a decision.")
        if sorted(item["reason_rank"] for item in outputs) != list(range(1, len(outputs) + 1)):
            raise ValueError("Reason ranks must be contiguous starting at one.")
    if payloads.get("rendered_notices") is not None:
        _unique(payloads["rendered_notices"], "notice_id", "rendered notices")
    drivers = payloads.get("driver_contributions")
    if drivers is None:
        return
    if not isinstance(drivers, list):
        raise ValueError("Driver contributions must be an array.")
    _unique(drivers, "decision_id", "driver contributions")
    decision_ids = {item["decision_id"] for item in payloads["decisions"]}
    for record in drivers:
        if record["decision_id"] not in decision_ids:
            raise ValueError("Driver contributions reference an unknown decision.")
        if not isinstance(record["contributions"], list):
            raise ValueError("Decision contributions must be an array.")
        identities = set()
        for contribution in record["contributions"]:
            _nonempty(contribution["driver_or_signal"], "driver_or_signal")
            component = contribution["decision_component"]
            if component not in {"scoring", "judgmental", "automatic_denial"}:
                raise ValueError("Unrecognized contribution decision component.")
            if contribution["direction"] not in {"adverse", "favorable", "neutral"}:
                raise ValueError("Unrecognized contribution direction.")
            amount = contribution["contribution"]
            if type(amount) not in (int, float) or not math.isfinite(amount):
                raise ValueError("Contribution must be a finite number.")
            identity = (component, contribution["driver_or_signal"])
            if identity in identities:
                raise ValueError("Ambiguous duplicate source driver.")
            identities.add(identity)
    by_decision = {record["decision_id"]: record["contributions"] for record in drivers}
    for decision in payloads["decisions"]:
        if decision["decision_outcome"] != "declined":
            continue
        components = source_components_for_decision(decision)
        available = {c["decision_component"] for c in by_decision.get(decision["decision_id"], [])
                     if c["direction"] == "adverse"}
        if components and not set(components).issubset(available):
            raise ValueError(f"{decision['decision_id']}: missing adverse source evidence for a failed component.")


def _has_evidence_content(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_has_evidence_content(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_evidence_content(item) for item in value)
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None


def _qa_contract_errors(qa: Any, payloads: dict[str, Any]) -> list[str]:
    """Require explicit, internally consistent completion and coverage results."""
    try:
        if qa["label"] != "qa_screening_only_not_legal_conclusion":
            raise ValueError("Unrecognized reason-QA result contract.")
        expected = {
            "declined_decision_count": sum(d["decision_outcome"] == "declined" for d in payloads["decisions"]),
            "reason_output_count": len(payloads["reason_outputs"]),
        }
        for field, count in expected.items():
            if type(qa[field]) is not int or qa[field] != count:
                raise ValueError(f"Reason-QA coverage mismatch: {field}.")
        findings = qa["exceptions"]
        if not isinstance(findings, list):
            raise ValueError("Reason-QA exceptions must be an explicit array.")
        if type(qa["exception_count"]) is not int or qa["exception_count"] != len(findings):
            raise ValueError("Reason-QA exception count disagrees with findings.")
        kinds = {finding["exception_type"] for finding in findings}
        for result in (qa["source_to_notice_fidelity"],
                       qa["source_to_notice_fidelity"]["rendered_notice_fidelity"]):
            count, types = result["exception_count"], result["exception_types"]
            if type(count) is not int or not 0 <= count <= len(findings):
                raise ValueError("Fidelity exception count disagrees with findings.")
            if (not isinstance(types, list) or any(not isinstance(t, str) for t in types)
                    or len(set(types)) != len(types) or not set(types).issubset(kinds)
                    or bool(count) != bool(types) or len(types) > count):
                raise ValueError("Fidelity exception types disagree with findings.")
        fidelity = qa["source_to_notice_fidelity"]
        policy, template = payloads["reason_fidelity_policy"], payloads["notice_template"]
        for field, expected_value in (
            ("policy_id", policy["policy_id"]), ("policy_version", policy["policy_version"]),
            ("notice_template_id", template["template_id"]),
            ("notice_template_version", template["template_version"]),
            ("selection_method_components", sorted(m["decision_component"] for m in payloads["reason_selection_methods"])),
        ):
            if fidelity[field] != expected_value:
                raise ValueError(f"Fidelity check used different or missing configuration: {field}.")
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        return [f"Required QA result is incomplete or inconsistent: {exc}"]
    return []


def _review_errors(
    review: Any, binding: str, files: dict[str, bytes],
    decision_times: dict[str, str], now: datetime,
) -> list[str]:
    if not isinstance(review, dict):
        return ["A complete, current reason-content review record is required."]
    try:
        if set(review) != {
            "gate_version", "snapshot_sha256", "reviewed_by", "reviewed_at",
            "valid_until", "decision_reviews", "material_defects", "known_defects_complete",
        }:
            raise ValueError("Review fields do not match the reason-content review contract.")
        if review["gate_version"] != GATE_VERSION or review["snapshot_sha256"] != binding:
            raise ValueError("Review is stale: gate version, control sources, schemas, or exact input hashes differ.")
        _nonempty(review["reviewed_by"], "reviewed_by")
        times = []
        for field in ("reviewed_at", "valid_until"):
            value = require_utc_timestamp(review[field], field)
            times.append(datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc))
        if not times[0] <= now < times[1]:
            raise ValueError("Review is future-dated, expired, or has an invalid validity interval.")
        for decision_id, timestamp in decision_times.items():
            decision_time = datetime.strptime(
                require_utc_timestamp(timestamp, "decision_timestamp"), "%Y-%m-%dT%H:%M:%SZ",
            ).replace(tzinfo=timezone.utc)
            if decision_time > times[0]:
                raise ValueError(f"{decision_id}: review predates the recorded final decision.")
        if review["known_defects_complete"] is not True:
            raise ValueError("Known material defects have not been fully accounted for.")

        def evidence(item: dict[str, Any]) -> None:
            _nonempty(item["rationale"], "review rationale")
            refs = item["evidence_files"]
            if not isinstance(refs, list) or not refs:
                raise ValueError("Review evidence files must be a non-empty array.")
            for name in refs:
                if not isinstance(name, str) or name == REVIEW_FILE or name not in files:
                    raise ValueError("Review evidence must reference a captured input JSON file.")
                value = _json(files[name])
                if not isinstance(value, (dict, list)) or not _has_evidence_content(value):
                    raise ValueError("Review evidence must contain a non-empty structured record.")

        records = review["decision_reviews"]
        if not isinstance(records, list):
            raise ValueError("Decision reviews must be an array.")
        _unique(records, "decision_id", "decision reviews")
        if {item["decision_id"] for item in records} != set(decision_times):
            raise ValueError("Review coverage must match every declined decision exactly.")
        for record in records:
            if set(record) != {"decision_id", "checks"} or set(record["checks"]) != set(REQUIRED_REVIEWS):
                raise ValueError("Every decision requires all four review checks.")
            for name, check in record["checks"].items():
                if set(check) != {"status", "rationale", "evidence_files"}:
                    raise ValueError(f"{name}: invalid review check fields.")
                if check["status"] != "satisfied":
                    raise ValueError(f"{record['decision_id']}: {name} is unresolved or unassessed.")
                evidence(check)
        defects = review["material_defects"]
        if not isinstance(defects, list):
            raise ValueError("Material defects must be an explicit array, including when empty.")
        _unique(defects, "defect_id", "material defects")
        for defect in defects:
            if set(defect) != {"defect_id", "material", "status", "rationale", "evidence_files"}:
                raise ValueError("Invalid material-defect record.")
            _nonempty(defect["defect_id"], "defect_id")
            if type(defect["material"]) is not bool or defect["status"] not in {"open", "resolved"}:
                raise ValueError("Defect materiality or resolution status is unknown.")
            if defect["material"] and defect["status"] != "resolved":
                raise ValueError(f"Unresolved material defect: {defect['defect_id']}.")
            evidence(defect)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        return [str(exc)]
    return []


def _assess_snapshot(files: dict[str, bytes]) -> dict[str, Any]:
    now = utc_now()
    result: dict[str, Any] = {
        "gate_version": GATE_VERSION,
        "scope": SCOPE,
        "status": "blocked",
        "reason_content_checks_passed": False,
        **_authorization_boundary(),
        "assessed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "review_sha256": hashlib.sha256(files[REVIEW_FILE]).hexdigest() if REVIEW_FILE in files else None,
        "required_review_checks": list(REQUIRED_REVIEWS),
        "blockers": [],
    }

    def block(code: str, message: str, decision_id: str | None = None) -> None:
        result["blockers"].append({"code": code, "message": message, "decision_id": decision_id})

    try:
        controls = _control_fingerprints()
        binding, hashes = _binding(files, controls)
        result.update(snapshot_sha256=binding, input_sha256=hashes, control_sha256=controls)
        if any(name.casefold() == LEGACY_REVIEW_FILE for name in files):
            block("legacy_review_file",
                  f"Retire {LEGACY_REVIEW_FILE} outside the dataset, account for its defects, "
                  f"and complete a fresh {REVIEW_FILE}; old reviews are not migrated automatically.")
            return result
        # Parse every captured input strictly, including review evidence. Validate
        # and assess one immutable byte snapshot; never export a later reread.
        parsed = {name: _json(data) for name, data in files.items()}
        snapshot = _CapturedPath(files)
        validation = validate_dataset(snapshot)
        if not validation.ok:
            for error in validation.errors:
                block("invalid_dataset", error)
            return result
        payloads = load_dataset_payloads(snapshot)
        _validate_reason_records(payloads)
        qa = compute_reason_qa(payloads)
        result["reason_qa"] = qa
        for error in _qa_contract_errors(qa, payloads):
            block("incomplete_qa_result", error)
        declined = {d["decision_id"] for d in payloads["decisions"] if d["decision_outcome"] == "declined"}
        if not declined:
            block("no_declined_decisions", "No declined decision reason set is available for review export.")
        fidelity = qa.get("source_to_notice_fidelity", {})
        if fidelity.get("status") != "ran_synthetic_source_to_rendered_notice_controls":
            block("required_checks_not_run", "Source-to-rendered-notice controls must run; missing or inapplicable is not a pass.")
        if fidelity.get("rendered_notice_fidelity", {}).get("status") != "ran_synthetic_rendered_notice_controls":
            block("rendered_checks_not_run", "Rendered reason checks must run.")
        # Every finding blocks, including newly added/unknown finding types.
        for finding in qa["exceptions"]:
            block(finding["exception_type"], finding["message"], finding.get("decision_id"))
        for output in payloads["reason_outputs"]:
            if output["decision_id"] not in declined:
                block("non_declined_reason_output", "Reason output is attached to a non-declined decision.", output["decision_id"])
            text = " ".join(output.get("disclosed_reason_text", "").casefold().split())
            if text in {"information from credit report", "credit report information", "credit report used"}:
                block("credit_report_only_placeholder", "Source identification alone does not state a specific reason.", output["decision_id"])
        for notice in payloads.get("rendered_notices") or []:
            if notice["decision_id"] not in declined:
                block("non_declined_notice", "Rendered notice is attached to a non-declined decision.", notice["decision_id"])
        now = utc_now()
        result["assessed_at"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        decision_times = {d["decision_id"]: d["underwriting"]["decision_timestamp"]
                          for d in payloads["decisions"] if d["decision_outcome"] == "declined"}
        for error in _review_errors(parsed.get(REVIEW_FILE), binding, files, decision_times, now):
            block("review_not_satisfied", error)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError) as exc:
        block("assessment_error", f"Required assessment could not complete: {exc}")
    if not result["blockers"]:
        result.update(status="reason_content_checks_passed", reason_content_checks_passed=True)
    return result


def assess_reason_content(dataset_dir: Path) -> dict[str, Any]:
    """Check a snapshot and its declared reviews; never authorize operational use."""
    try:
        files = _snapshot(Path(dataset_dir))
        assessment = _assess_snapshot(files)
        if assessment["reason_content_checks_passed"]:
            _check_freshness(Path(dataset_dir), files, assessment)
        return assessment
    except OSError:
        return _read_failure()
    except ValueError:
        return _read_failure()


def _read_failure() -> dict[str, Any]:
    return {
        "gate_version": GATE_VERSION, "scope": SCOPE,
        "status": "blocked", "reason_content_checks_passed": False,
        **_authorization_boundary(),
        "blockers": [{"code": "input_unreadable", "message": "Cannot capture the required dataset.", "decision_id": None}],
    }


def _block_assessment(assessment: dict[str, Any], code: str, message: str) -> None:
    assessment.update(status="blocked", reason_content_checks_passed=False,
                      **_authorization_boundary())
    assessment["blockers"].append({"code": code, "message": message, "decision_id": None})


def _check_freshness(dataset_dir: Path, files: dict[str, bytes], assessment: dict[str, Any]) -> None:
    try:
        if _snapshot(dataset_dir) != files:
            _block_assessment(assessment, "snapshot_changed",
                              "Inputs or declared review changed during this operation; reassessment is required.")
        if _control_fingerprints() != assessment["control_sha256"]:
            _block_assessment(assessment, "controls_changed",
                              "Control sources or schemas changed during this operation.")
    except (OSError, ValueError):
        _block_assessment(assessment, "freshness_unverifiable",
                          "Current input, declared review, or control state cannot be verified.")


def _install_new_file(source: Path, destination: Path) -> None:
    # Windows rename refuses an existing destination. POSIX rename replaces it,
    # so use an atomic, exclusive hard-link install there instead.
    if os.name == "nt":
        os.rename(source, destination)
    else:
        os.link(source, destination)


def export_reviewed_reasons(dataset_dir: Path, output_path: Path) -> dict[str, Any]:
    """Write a new local artifact only after reassessing its exact input bytes.

    There is deliberately no force/waiver option and no parameter accepting a
    previously passed assessment. Success exports a historical review snapshot;
    it never authorizes operational use or sends or delivers a notice.
    """
    dataset_dir, output_path = Path(dataset_dir).resolve(), Path(output_path).resolve()
    try:
        files = _snapshot(dataset_dir)
    except (OSError, ValueError):
        return {"ok": False, "assessment": _read_failure(), "exported": False,
                **_authorization_boundary()}
    assessment = _assess_snapshot(files)
    result = {"ok": False, "assessment": assessment, "exported": False,
              **_authorization_boundary()}
    if not assessment["reason_content_checks_passed"]:
        return result
    if output_path.is_relative_to(dataset_dir):
        result["export_error"] = "Export destination must be outside the input dataset."
        _block_assessment(assessment, "invalid_export_destination", result["export_error"])
        return result
    artifact = {
        "artifact_type": "reviewed_reason_content_snapshot",
        "scope": SCOPE,
        **_authorization_boundary(),
        "assessment": assessment,
        "review": _json(files[REVIEW_FILE]),
        "reason_outputs": _json(files["adverse-action-reason-outputs.json"]),
        "rendered_notices": _json(files["rendered-adverse-action-notices.json"]),
    }
    temporary: Path | None = None
    try:
        # Install a fully written file without replacing any existing artifact.
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=output_path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(artifact, handle, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        _check_freshness(dataset_dir, files, assessment)
        now = utc_now()
        review = artifact["review"]
        start = datetime.strptime(review["reviewed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        expiry = datetime.strptime(review["valid_until"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if not start <= now < expiry:
            _block_assessment(assessment, "review_invalid_before_export",
                              "Review is expired or future-dated at export time.")
        if not assessment["reason_content_checks_passed"]:
            return result
        _install_new_file(temporary, output_path)
        result.update(ok=True, exported=True, output=str(output_path))
    except OSError:
        result["export_error"] = "Export could not be installed; use a new filename in an existing writable directory."
        _block_assessment(assessment, "export_failed", result["export_error"])
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return result
