"""Public dispatcher for the portable Metaphysics Lab distribution runtime."""

from __future__ import annotations

from datetime import datetime
from typing import Mapping, Optional
from zoneinfo import ZoneInfo

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
    return {"ok": True, "action": action, "runtime_version": DISTRIBUTION_RUNTIME_VERSION, "data": dict(data)}


def _error(action: str, code: str, message: str, details: Optional[Mapping[str, object]] = None) -> dict:
    return {
        "ok": False, "action": action, "runtime_version": DISTRIBUTION_RUNTIME_VERSION,
        "error": {"code": code, "message": message, "details": dict(details or {})},
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


def _selected_historical_rows(selector_result: Mapping[str, object]):
    high = selector_result.get("high_years")
    control = selector_result.get("control_year")
    if not isinstance(high, (list, tuple)) or len(high) != 4 or not isinstance(control, Mapping):
        raise DistributionError("historical_selector_invalid", "selector result must contain four high years and one control year")
    rows = list(high) + [control]
    if any(not isinstance(row, Mapping) for row in rows):
        raise DistributionError("historical_selector_invalid", "selector result contains malformed selected years")
    return rows


def _ziwei_historical_support(selector_result: Mapping[str, object], payload: Mapping[str, object]) -> dict:
    """Attach optional Ziwei yearly context without changing Bazi ranking truth."""
    from .forecast import resolve_forecast_context

    normalized = payload.get("normalized_natal")
    timezone = selector_result.get("timezone")
    if not isinstance(normalized, Mapping) or not isinstance(timezone, str) or not timezone.strip():
        return {"status": "unavailable", "role": "support_only", "ranking_authority": False, "years": [], "reason": "normalized natal facts and selector timezone are required for Ziwei support"}
    try:
        zone = ZoneInfo(timezone.strip())
    except Exception as exc:
        return {"status": "unavailable", "role": "support_only", "ranking_authority": False, "years": [], "reason": "selector timezone cannot be resolved: %s" % exc}
    support_rows = []
    failures = []
    for row in _selected_historical_rows(selector_result):
        label_year = row.get("label_year")
        try:
            start = datetime.fromisoformat(str(row["period_start"]))
            end = datetime.fromisoformat(str(row["period_end"]))
            if start.tzinfo is None or start.utcoffset() is None or end.tzinfo is None or end.utcoffset() is None:
                raise ValueError("historical flow-year boundaries must include timezone offsets")
            midpoint = start + (end - start) / 2
            local_midpoint = midpoint.astimezone(zone)
            target_local = local_midpoint.replace(tzinfo=None).isoformat(timespec="seconds")
            context = resolve_forecast_context({"normalized_natal": normalized, "target": {"civil_datetime": target_local, "timezone": timezone.strip()}, "requested_scopes": ["yearly"]})
            yearly = context.get("ziwei", {}).get("yearly")
            if not isinstance(yearly, Mapping):
                raise ValueError("yearly Ziwei context is unavailable")
            support_row = dict(yearly)
            support_row["label_year"] = label_year
            support_row["sample_datetime"] = local_midpoint.isoformat()
            support_rows.append(support_row)
        except (DistributionError, KeyError, TypeError, ValueError) as exc:
            failures.append({"label_year": label_year, "reason": str(exc), "error_code": getattr(exc, "code", None)})
    if len(support_rows) == 5:
        status, reason = "available", None
    elif support_rows:
        status, reason = "partial", "Ziwei yearly support was unavailable for %d of 5 canonical years" % len(failures)
    else:
        status, reason = "unavailable", failures[0]["reason"] if failures else "Ziwei yearly support is unavailable"
    result = {"status": status, "role": "support_only", "ranking_authority": False, "years": support_rows}
    if reason is not None:
        result["reason"] = reason
    if failures:
        result["failures"] = failures
    return result


def _prepare_historical_calibration(payload: Mapping[str, object]) -> dict:
    from engine.historical.selector import select_historical_activation
    try:
        selector_result = select_historical_activation(payload)
    except ValueError as exc:
        raise DistributionError("historical_selector_invalid", str(exc)) from exc
    result = dict(selector_result)
    result["ziwei_support"] = _ziwei_historical_support(selector_result, payload)
    return result


def dispatch(action: str, payload: Optional[Mapping[str, object]] = None) -> dict:
    """Dispatch one portable runtime action and always return a structured envelope."""
    if not isinstance(action, str) or not action.strip():
        return _error(str(action), "invalid_action", "action must be a non-empty string")
    if action == "runtime_info":
        return _ok(action, runtime_info())
    request = {} if payload is None else payload
    try:
        if action in ("subject.create_identity", "subject.registry_validate", "subject.rename"):
            from .subjects import create_subject_identity, rename_subject, validate_subject_registry
            handler = {"subject.create_identity": create_subject_identity, "subject.registry_validate": validate_subject_registry, "subject.rename": rename_subject}[action]
            return _ok(action, handler(request))
        if action == "build_natal":
            from .natal import build_natal
            return _ok(action, build_natal(request))
        if action == "natal.candidate_envelope":
            from .natal import build_candidate_natal
            return _ok(action, build_candidate_natal(request))
        if action == "reconcile_natal":
            from .natal import reconcile_natal
            return _ok(action, reconcile_natal(request))
        if action == "resolve_forecast_context":
            from .forecast import resolve_forecast_context
            return _ok(action, resolve_forecast_context(request))
        if action == "prepare_historical_calibration":
            return _ok(action, _prepare_historical_calibration(request))
        if action in ("lock_blind_forecast", "lock_historical_calibration", "finalize_historical_calibration"):
            from .calibration import finalize_historical_calibration, lock_blind_forecast, lock_historical_calibration
            handler = {"lock_blind_forecast": lock_blind_forecast, "lock_historical_calibration": lock_historical_calibration, "finalize_historical_calibration": finalize_historical_calibration}[action]
            return _ok(action, handler(request))
        if action in ("export_case_markdown", "validate_case", "migrate_case", "update_case_record"):
            from .case_pack import export_case_markdown, migrate_case, update_case_record, validate_case
            handler = {"export_case_markdown": export_case_markdown, "validate_case": validate_case, "migrate_case": migrate_case, "update_case_record": update_case_record}[action]
            return _ok(action, handler(request))
    except DistributionError as exc:
        return _error(action, exc.code, str(exc), exc.details)
    return _error(action, "unsupported_action", "unsupported distribution runtime action", {"supported_actions": list(SUPPORTED_ACTIONS)})
