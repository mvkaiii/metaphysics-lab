"""Public dispatcher for the portable Metaphysics Lab distribution runtime."""

from __future__ import annotations

from typing import Mapping, Optional

from .constants import (
    CASE_SCHEMA_VERSION,
    DISTRIBUTION_RUNTIME_VERSION,
    PROJECT_CONTRACT_VERSION,
    RUNTIME_SCHEMA_VERSION,
    SUPPORTED_ACTIONS,
)
from .dependencies import inspect_external_dependencies
from .errors import DistributionError
from .manifest import load_capabilities


def _ok(action: str, data: Mapping[str, object]) -> dict:
    return {
        "ok": True,
        "action": action,
        "runtime_version": DISTRIBUTION_RUNTIME_VERSION,
        "data": dict(data),
    }


def _error(action: str, code: str, message: str, details: Optional[Mapping[str, object]] = None) -> dict:
    return {
        "ok": False,
        "action": action,
        "runtime_version": DISTRIBUTION_RUNTIME_VERSION,
        "error": {
            "code": code,
            "message": message,
            "details": dict(details or {}),
        },
    }


def runtime_info() -> dict:
    return {
        "project_contract_version": PROJECT_CONTRACT_VERSION,
        "runtime_schema_version": RUNTIME_SCHEMA_VERSION,
        "case_schema_version": CASE_SCHEMA_VERSION,
        "distribution_runtime_version": DISTRIBUTION_RUNTIME_VERSION,
        "supported_actions": list(SUPPORTED_ACTIONS),
        "capabilities": load_capabilities(),
        "external_dependencies": inspect_external_dependencies(),
    }


def dispatch(action: str, payload: Optional[Mapping[str, object]] = None) -> dict:
    """Dispatch one portable runtime action and always return a structured envelope."""
    if not isinstance(action, str) or not action.strip():
        return _error(
            str(action),
            "invalid_action",
            "action must be a non-empty string",
        )

    if action == "runtime_info":
        return _ok(action, runtime_info())

    try:
        if action == "build_natal":
            from .natal import build_natal

            return _ok(action, build_natal({} if payload is None else payload))
        if action == "reconcile_natal":
            from .natal import reconcile_natal

            return _ok(action, reconcile_natal({} if payload is None else payload))
        if action == "resolve_forecast_context":
            from .forecast import resolve_forecast_context

            return _ok(action, resolve_forecast_context({} if payload is None else payload))
    except DistributionError as exc:
        return _error(action, exc.code, str(exc), exc.details)

    return _error(
        action,
        "unsupported_action",
        "unsupported distribution runtime action",
        {"supported_actions": list(SUPPORTED_ACTIONS)},
    )
