"""Phase 3B adverse-action reason generation for synthetic governance datasets.

This module turns ranked, per-decision driver contributions into governed
adverse-action reason outputs. Reason *generation* is deliberately separated
from reason *quality assurance* (see ``monitoring.compute_reason_qa``): a
decisioning process generates candidate reasons, and an independent governance
step reviews them. Keeping the two apart mirrors the control separation a model
risk or compliance reviewer would expect.

The logic is deterministic and synthetic. It does not represent a production
adverse-action notice process and encodes no legal conclusions.
"""

from __future__ import annotations

from typing import Any

from .reason_fidelity import ReasonFidelityContext, rank_decision_contributions

DEFAULT_MAX_REASONS = 4


def build_mapping_index(reason_mappings: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index governed reason-code mappings by driver/signal name."""
    return {record["driver_or_signal"]: record for record in reason_mappings}


def rank_adverse_contributions(contributions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return adverse driver contributions sorted by magnitude, deterministically.

    Ties are broken by driver name so output ordering is stable across runs.
    """
    adverse = [
        item
        for item in contributions
        if item.get("direction", "adverse") == "adverse"
    ]
    return sorted(
        adverse,
        key=lambda item: (-float(item["contribution"]), str(item["driver_or_signal"])),
    )


def generate_reasons_for_decision(
    decision_id: str,
    contributions: list[dict[str, Any]],
    mapping_index: dict[str, dict[str, Any]],
    version_id: str,
    max_reasons: int = DEFAULT_MAX_REASONS,
    decision_context: dict[str, Any] | None = None,
    fidelity_context: ReasonFidelityContext | None = None,
) -> list[dict[str, Any]]:
    """Generate governed adverse-action reason outputs for a single decision.

    Only drivers that resolve to a governed reason-code mapping are emitted.
    The absence of any mapped adverse driver yields no outputs, which the
    downstream reason QA step surfaces as a ``missing_reason_code`` exception.
    """
    decision_context = decision_context or {}
    decision_component = decision_context.get("decision_component", "scoring")
    if fidelity_context is not None:
        ranked = rank_decision_contributions(contributions, decision_context)
        if not ranked and decision_component == "combined":
            raise ValueError(
                "Combined decision must record failed_components and adverse contributions "
                "from those source components."
            )
    else:
        ranked = rank_adverse_contributions(contributions)
    outputs: list[dict[str, Any]] = []
    numeric_id = decision_id.split("-")[-1]
    rank = 0
    for source_driver_rank, item in enumerate(ranked, start=1):
        mapping = mapping_index.get(item["driver_or_signal"])
        if mapping is None:
            continue
        rank += 1
        output = {
            "record_type": "adverse_action_reason_output",
            "reason_output_id": f"rso-{numeric_id}-{rank}",
            "decision_id": decision_id,
            "version_id": version_id,
            "reason_code": mapping["reason_code"],
            "driver_or_signal": mapping["driver_or_signal"],
            "reason_rank": rank,
            "mapping_version": mapping["mapping_version"],
        }
        if fidelity_context is not None:
            method = fidelity_context.methods_by_component.get(decision_component)
            if method is None:
                raise ValueError(
                    f"No reason-selection method is configured for decision component "
                    f"{decision_component!r}"
                )
            notice_template = fidelity_context.notice_template
            output.update(
                {
                    "mapping_id": mapping["mapping_id"],
                    "mapping_effective_date": mapping["effective_date"],
                    "disclosed_reason_text": mapping["reason_text"],
                    "notice_template_id": notice_template["template_id"],
                    "notice_template_version": notice_template["template_version"],
                    "selection_method_id": method["selection_method_id"],
                    "selection_method_version": method["selection_method_version"],
                    "decision_component": decision_component,
                    "source_decision_component": item["decision_component"],
                    "source_driver_rank": source_driver_rank,
                    "policy_version": decision_context["underwriting"]["policy_version"],
                }
            )
        outputs.append(output)
        if rank >= max_reasons:
            break
    return outputs


def generate_adverse_action_reasons(
    decisions: list[dict[str, Any]],
    driver_contributions: list[dict[str, Any]],
    reason_mappings: list[dict[str, Any]],
    version_id: str,
    max_reasons: int = DEFAULT_MAX_REASONS,
    fidelity_context: ReasonFidelityContext | None = None,
) -> list[dict[str, Any]]:
    """Generate adverse-action reason outputs for all declined decisions.

    Reasons are only generated for declined decisions. Contributions for other
    decisions, if present, are ignored. Output is deterministic and ordered by
    decision id then reason rank.
    """
    mapping_index = build_mapping_index(reason_mappings)
    contributions_by_decision: dict[str, list[dict[str, Any]]] = {}
    for record in driver_contributions:
        contributions_by_decision[record["decision_id"]] = record.get("contributions", [])

    declined_decisions = sorted(
        (record for record in decisions if record["decision_outcome"] == "declined"),
        key=lambda record: record["decision_id"],
    )

    outputs: list[dict[str, Any]] = []
    for decision in declined_decisions:
        decision_id = decision["decision_id"]
        contributions = contributions_by_decision.get(decision_id, [])
        outputs.extend(
            generate_reasons_for_decision(
                decision_id,
                contributions,
                mapping_index,
                version_id,
                max_reasons=max_reasons,
                decision_context=decision,
                fidelity_context=fidelity_context,
            )
        )
    return outputs


def summarize_generation(
    decisions: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Provenance summary for the generation step (governance evidence)."""
    declined = [record for record in decisions if record["decision_outcome"] == "declined"]
    covered = {output["decision_id"] for output in outputs}
    uncovered = sorted(
        record["decision_id"] for record in declined if record["decision_id"] not in covered
    )
    return {
        "label": "synthetic_reason_generation_not_a_notice_process",
        "declined_decision_count": len(declined),
        "declined_with_generated_reasons": len(covered),
        "declined_without_generated_reasons": uncovered,
        "reason_output_count": len(outputs),
    }
