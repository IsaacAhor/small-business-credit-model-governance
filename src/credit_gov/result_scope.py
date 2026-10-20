"""Scope labels for diagnostic results; these do not implement authorization."""

from __future__ import annotations

from typing import Any


def non_authorization_fields() -> dict[str, Any]:
    return {
        "operational_authorization_status": "not_provided",
        "authorized_for_operational_use": False,
        "eligible_for_final_use": False,
    }


def diagnostic_scope(purpose: str) -> dict[str, Any]:
    """Keep execution or integrity success separate from content review and use."""
    return {
        "purpose": purpose,
        "final_use_status": "not_assessed",
        **non_authorization_fields(),
    }
