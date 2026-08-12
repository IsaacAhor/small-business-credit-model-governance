"""Shared controls for adverse-action reason source and notice fidelity.

The public workflow is deliberately synthetic.  These controls establish a
reviewable provenance chain; they do not determine legal sufficiency or create
a safe harbor under Regulation B, ECOA, FCRA, or any state law.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REQUIRED_REASON_FIDELITY_FIELDS = (
    "mapping_id",
    "mapping_effective_date",
    "disclosed_reason_text",
    "notice_template_id",
    "notice_template_version",
    "selection_method_id",
    "selection_method_version",
    "decision_component",
    "source_driver_rank",
    "policy_version",
)


@dataclass(frozen=True, slots=True)
class ReasonFidelityContext:
    """Versioned configuration required for source-to-notice QA."""

    policy: dict[str, Any]
    notice_template: dict[str, Any]
    methods_by_component: dict[str, dict[str, Any]]

    @property
    def principal_driver_rank_limit(self) -> int:
        return int(self.policy["principal_driver_rank_limit"])


def build_reason_fidelity_context(
    policy: Any,
    notice_template: Any,
    selection_methods: Any,
) -> ReasonFidelityContext | None:
    """Return a validated context when all optional fidelity inputs are present.

    Other repository datasets intentionally omit these synthetic-only inputs;
    their standard mapping QA remains available but source-to-notice fidelity is
    reported as not run rather than silently inferred.
    """
    if policy is None and notice_template is None and selection_methods is None:
        return None
    if not isinstance(policy, dict):
        raise ValueError("reason-fidelity-policy.json must be an object")
    if not isinstance(notice_template, dict):
        raise ValueError("adverse-action-notice-template.json must be an object")
    if not isinstance(selection_methods, list) or not selection_methods:
        raise ValueError("reason-selection-methods.json must be a non-empty array")

    require_fields(
        policy,
        ("policy_id", "policy_version", "principal_driver_rank_limit"),
        "reason-fidelity-policy.json",
    )
    if int(policy["principal_driver_rank_limit"]) < 1:
        raise ValueError("reason-fidelity-policy.json.principal_driver_rank_limit must be positive")
    require_fields(
        notice_template,
        ("template_id", "template_version", "effective_date"),
        "adverse-action-notice-template.json",
    )
    if "retired_date" not in notice_template:
        raise ValueError("adverse-action-notice-template.json is missing required field: retired_date")

    methods_by_component: dict[str, dict[str, Any]] = {}
    for index, method in enumerate(selection_methods):
        if not isinstance(method, dict):
            raise ValueError(f"reason-selection-methods.json[{index}] must be an object")
        require_fields(
            method,
            ("decision_component", "selection_method_id", "selection_method_version"),
            f"reason-selection-methods.json[{index}]",
        )
        component = method["decision_component"]
        if component in methods_by_component:
            raise ValueError(
                "reason-selection-methods.json contains duplicate decision_component "
                f"{component!r}"
            )
        methods_by_component[component] = method
    return ReasonFidelityContext(
        policy=policy,
        notice_template=notice_template,
        methods_by_component=methods_by_component,
    )


def require_fields(payload: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    missing = [field for field in fields if payload.get(field) in (None, "")]
    if missing:
        raise ValueError(f"{label} is missing required fields: {', '.join(missing)}")


def normalize_reason_text(value: str) -> str:
    """Normalize whitespace and case for deterministic template fidelity checks."""
    return " ".join(value.casefold().split())


def is_active_on_date(
    effective_date: Any,
    retired_date: Any,
    decision_date: Any,
) -> bool:
    """Return whether a versioned artifact applies on the supplied ISO date."""
    if not all(isinstance(value, str) and value for value in (effective_date, decision_date)):
        return False
    if decision_date < effective_date:
        return False
    return not isinstance(retired_date, str) or not retired_date or decision_date < retired_date


def rank_component_contributions(
    contributions: list[dict[str, Any]],
    decision_component: str,
) -> list[dict[str, Any]]:
    """Rank adverse contributions for one recorded decision component.

    This is a deterministic synthetic governance ranking, not a legal test for
    selecting adverse-action reasons in a real creditor's scoring system.
    """
    adverse = [
        contribution
        for contribution in contributions
        if contribution.get("direction", "adverse") == "adverse"
        and contribution.get("decision_component") == decision_component
    ]
    return sorted(
        adverse,
        key=lambda item: (-float(item["contribution"]), str(item["driver_or_signal"])),
    )
