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


def _prepare_historical_calibration(payload: Mapping[str, object]) -> dict:
    from engine.historical.selector import select_historical_activation

    try:
        return select_historical_activation(payload)
    except ValueError as exc:
        raise DistributionError(
            "historical_selector_invalid",
            str(exc),
        ) from exc


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

    request = {} if payload is None else payload
    try:
        if action == "build_natal":
            from .natal import build_natal

            return _ok(action, build_natal(request))
        if action == "reconcile_natal":
            from .natal import reconcile_natal

            return _ok(action, reconcile_natal(request))
        if action == "resolve_forecast_context":
            from .forecast import resolve_forecast_context

            return _ok(action, resolve_forecast_context(request))
        if action == "prepare_historical_calibration":
            return _ok(action, _prepare_historical_calibration(request))
        if action in (
            "lock_blind_forecast",
            "lock_historical_calibration",
            "finalize_historical_calibration",
        ):
            from .calibration import (
                finalize_historical_calibration,
                lock_blind_forecast,
                lock_historical_calibration,
            )

            handler = {
                "lock_blind_forecast": lock_blind_forecast,
                "lock_historical_calibration": lock_historical_calibration,
                "finalize_historical_calibration": finalize_historical_calibration,
            }[action]
            return _ok(action, handler(request))
        if action in (
            "export_case_markdown",
            "validate_case",
            "migrate_case",
            "update_case_record",
        ):
            from .case_pack import (
                export_case_markdown,
                migrate_case,
                update_case_record,
                validate_case,
            )

            handler = {
                "export_case_markdown": export_case_markdown,
                "validate_case": validate_case,
                "migrate_case": migrate_case,
                "update_case_record": update_case_record,
            }[action]
            return _ok(action, handler(request))
    except DistributionError as exc:
        return _error(action, exc.code, str(exc), exc.details)

    return _error(
        action,
        "unsupported_action",
        "unsupported distribution runtime action",
        {"supported_actions": list(SUPPORTED_ACTIONS)},
    )
