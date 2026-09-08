"""Public dispatcher for the portable Metaphysics Lab distribution runtime."""

from __future__ import annotations

from datetime import datetime
from typing import Mapping, Optional
from zoneinfo import ZoneInfo

from engine.birth.errors import BirthFoundationError
from engine.birth.offline_registry import offline_birth_place_registry_metadata

from .constants import (
    CASE_SCHEMA_VERSION,
    DISTRIBUTION_RUNTIME_VERSION,
    PROJECT_CONTRACT_VERSION,
    RUNTIME_SCHEMA_VERSION,
    SUPPORTED_ACTIONS,
)
from .dependencies import (
    inspect_bundled_dependencies,
    inspect_external_dependencies,
    inspect_optional_external_dependencies,
)
from .errors import DistributionError
from .manifest import CAPABILITY_MANIFEST_VERSION, load_capabilities


def _ok(action: str, data: Mapping[str, object]) -> dict:
    return {"ok": True, "action": action, "runtime_version": DISTRIBUTION_RUNTIME_VERSION, "data": dict(data)}


def _error(action: str, code: str, message: str, details: Optional[Mapping[str, object]] = None) -> dict:
    return {
        "ok": False, "action": action, "runtime_version": DISTRIBUTION_RUNTIME_VERSION,
        "error": {"code": code, "message": message, "details": dict(details or {})},
    }


def _offline_location_registry_info() -> dict:
    try:
        metadata = dict(offline_birth_place_registry_metadata())
    except BirthFoundationError:
        return {
            "version": None,
            "record_count": 0,
            "coverage_profile": None,
            "source_profiles": [],
            "bundled": False,
            "available": False,
        }
    metadata["bundled"] = True
    metadata["available"] = True
    return metadata


def runtime_info() -> dict:
    return {
        "project_contract_version": PROJECT_CONTRACT_VERSION,
        "runtime_schema_version": RUNTIME_SCHEMA_VERSION,
        "case_schema_version": CASE_SCHEMA_VERSION,
        "distribution_runtime_version": DISTRIBUTION_RUNTIME_VERSION,
        "capability_manifest_version": CAPABILITY_MANIFEST_VERSION,
        "supported_actions": list(SUPPORTED_ACTIONS),
        "capabilities": load_capabilities(),
        "dependency_authority": {
            "calendar_core": "bundled",
            "network_location": "execution_environment_optional",
        },
        "bundled_dependencies": inspect_bundled_dependencies(),
        "optional_external_dependencies": inspect_optional_external_dependencies(),
        "offline_location_registry": _offline_location_registry_info(),
        "external_dependencies": inspect_external_dependencies(),
    }


def _selected_historical_rows(selector_result: Mapping[str, object]):
    high = selector_result.get("high_years")
    control = selector_result.get("control_year")
    if not isinstance(high, (list, tuple)) or len(high) != 4:
        raise DistributionError("historical_selector_invalid", "selector result must contain exactly four high years")
    profile_id = selector_result.get("profile_id")
    rule_version = selector_result.get("rule_version")
    if profile_id == "historical-activation-bazi-v1" and rule_version == "1.0-exp":
        if not isinstance(control, Mapping):
            raise DistributionError("historical_selector_invalid", "v1 selector result must contain one control year")
        rows = list(high) + [control]
    elif profile_id == "historical-activation-bazi-v2" and rule_version == "2.0-exp":
        selection = selector_result.get("control_selection")
        if selection == "selected":
            if not isinstance(control, Mapping):
                raise DistributionError("historical_selector_invalid", "v2 selected selector result must contain one control year")
            rows = list(high) + [control]
        elif selection == "abstain":
            if control is not None:
                raise DistributionError("historical_selector_invalid", "v2 abstain selector result cannot contain a control year")
            rows = list(high)
        else:
            raise DistributionError("historical_selector_invalid", "v2 selector control_selection is invalid")
    else:
        raise DistributionError("historical_selector_invalid", "unsupported selector profile")
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
    selected_rows = _selected_historical_rows(selector_result)
    expected_count = len(selected_rows)
    for row in selected_rows:
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
    if len(support_rows) == expected_count:
        status, reason = "available", None
    elif support_rows:
        status, reason = "partial", "Ziwei yearly support was unavailable for %d of %d canonical years" % (len(failures), expected_count)
    else:
        status, reason = "unavailable", failures[0]["reason"] if failures else "Ziwei yearly support is unavailable"
    result = {"status": status, "role": "support_only", "ranking_authority": False, "years": support_rows}
    if reason is not None:
        result["reason"] = reason
    if failures:
        result["failures"] = failures
    return result


def _prepare_historical_calibration(payload: Mapping[str, object]) -> dict:
    from engine.historical.selector import select_historical_activation, select_historical_activation_v2

    selector_profile_id = payload.get("selector_profile_id", "historical-activation-bazi-v1")
    selector_payload = dict(payload)
    selector_payload.pop("selector_profile_id", None)
    try:
        if selector_profile_id == "historical-activation-bazi-v1":
            selector_result = select_historical_activation(selector_payload)
        elif selector_profile_id == "historical-activation-bazi-v2":
            selector_result = select_historical_activation_v2(selector_payload)
        else:
            raise DistributionError("historical_selector_invalid", "unsupported selector profile")
    except ValueError as exc:
        raise DistributionError("historical_selector_invalid", str(exc)) from exc
    result = dict(selector_result)
    result["ziwei_support"] = _ziwei_historical_support(selector_result, selector_payload)
    return result


def _interpret_structural_summary(payload: Mapping[str, object]) -> dict:
    if not isinstance(payload, Mapping):
        raise DistributionError(
            "invalid_structural_interpretation_payload",
            "structural interpretation payload must be a mapping",
            {"type": type(payload).__name__},
        )
    allowed = {"forecast_context", "target_scope"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise DistributionError(
            "invalid_structural_interpretation_payload",
            "structural interpretation payload contains unknown fields",
            {"unknown_fields": unknown},
        )
    from .structural_interpretation import interpret_structural_evidence
    return interpret_structural_evidence(
        payload.get("forecast_context"),
        payload.get("target_scope"),
    )


def _rank_evidence_summary(payload: Mapping[str, object]) -> dict:
    from .capabilities import get_capability
    from .evidence_ranker import detect_local_spike, rank_evidence

    if not isinstance(payload, Mapping):
        raise DistributionError(
            "invalid_evidence_ranking",
            "rank_evidence payload must be a mapping",
            {"type": type(payload).__name__},
        )

    ranking = rank_evidence(
        payload.get("features"),
        target_scope=payload.get("target_scope"),
        parent_ranking=payload.get("parent_ranking"),
    )
    parent_ranking = payload.get("parent_ranking")
    local_windows = [] if parent_ranking is None else detect_local_spike(parent_ranking, ranking)
    capability = get_capability("distribution.evidence_engine")
    return {
        "capability_id": capability["id"],
        "maturity": capability["maturity"],
        "routing": capability["routing"],
        "rule_version": capability["rule_version"],
        "ranking_authority": capability["ranking_authority"],
        "ranking": ranking,
        "local_windows": local_windows,
    }


def _personalize_ranking_summary(payload: Mapping[str, object]) -> dict:
    if not isinstance(payload, Mapping):
        raise DistributionError(
            "invalid_historical_personalization",
            "personalize_ranking payload must be a mapping",
        )
    allowed = {"base_ranking", "historical_calibration_status", "historical_records"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise DistributionError(
            "invalid_historical_personalization",
            "personalize_ranking payload contains unknown fields",
            {"unknown_fields": unknown},
        )
    from .historical_personalization import personalize_ranking
    return personalize_ranking(
        payload.get("base_ranking"),
        payload.get("historical_calibration_status"),
        payload.get("historical_records"),
    )


def _build_interpretation_contract_summary(payload: Mapping[str, object]) -> dict:
    if not isinstance(payload, Mapping):
        raise DistributionError(
            "invalid_interpretation_contract",
            "build_interpretation_contract payload must be a mapping",
        )
    allowed = {
        "base_ranking",
        "anchor",
        "personalization",
        "local_windows",
        "locked_forecast",
        "interpretation_profile_version",
        "structural_interpretation",
    }
    unknown = sorted(set(payload) - allowed)
    missing = sorted({"base_ranking", "anchor"} - set(payload))
    if unknown or missing:
        raise DistributionError(
            "invalid_interpretation_contract",
            "interpretation contract payload fields do not match the fixed contract",
            {"unknown_fields": unknown, "missing_fields": missing},
        )

    v1_profile = "lin_tianji_interpretation_contract_v1-exp"
    v2_profile = "lin_tianji_interpretation_contract_v2-exp"
    profile = payload.get("interpretation_profile_version", v1_profile)
    common = {
        "personalization": payload.get("personalization"),
        "local_windows": payload.get("local_windows"),
        "locked_forecast": payload.get("locked_forecast"),
    }
    if profile == v1_profile:
        if "structural_interpretation" in payload:
            raise DistributionError(
                "invalid_interpretation_contract",
                "v1 interpretation contract does not accept structural_interpretation",
            )
        from .interpretation_contract import build_interpretation_contract
        return build_interpretation_contract(
            payload.get("base_ranking"),
            payload.get("anchor"),
            **common,
        )
    if profile == v2_profile:
        structural = payload.get("structural_interpretation")
        if not isinstance(structural, Mapping):
            raise DistributionError(
                "invalid_interpretation_contract",
                "v2 interpretation contract requires structural_interpretation",
            )
        from .interpretation_contract_v2 import build_interpretation_contract_v2
        return build_interpretation_contract_v2(
            payload.get("base_ranking"),
            payload.get("anchor"),
            structural_interpretation=structural,
            **common,
        )
    raise DistributionError(
        "invalid_interpretation_contract",
        "unsupported interpretation profile",
        {"interpretation_profile_version": profile},
    )


def _export_case(request: Mapping[str, object]) -> dict:
    has_full = request.get("normalized_natal") is not None
    has_partial = request.get("candidate_envelope") is not None
    if has_full and has_partial:
        raise DistributionError(
            "ambiguous_case_natal_source",
            "Case export must use exactly one natal source: normalized_natal or candidate_envelope",
        )
    if has_partial:
        from .partial_case import export_partial_case_markdown
        return export_partial_case_markdown(request)
    if not has_full:
        raise DistributionError(
            "missing_case_natal_source",
            "Case export requires normalized_natal or candidate_envelope",
        )
    from .case_pack import export_case_markdown
    return export_case_markdown(request)


def dispatch(action: str, payload: Optional[Mapping[str, object]] = None) -> dict:
    """Dispatch one portable runtime action and always return a structured envelope."""
    if not isinstance(action, str) or not action.strip():
        return _error(str(action), "invalid_action", "action must be a non-empty string")
    if action == "runtime_info":
        return _ok(action, runtime_info())
    request = {} if payload is None else payload
    try:
        if action in ("subject.create_identity", "subject.registry_validate", "subject.rename", "subject.prepare_astralium_references"):
            from .subjects import create_subject_identity, prepare_astralium_references, rename_subject, validate_subject_registry
            handler = {
                "subject.create_identity": create_subject_identity,
                "subject.registry_validate": validate_subject_registry,
                "subject.rename": rename_subject,
                "subject.prepare_astralium_references": prepare_astralium_references,
            }[action]
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
        if action in ("resolve_query_anchor", "lock_prospective_forecast"):
            from .prospective import lock_prospective_forecast, resolve_query_anchor
            handler = {
                "resolve_query_anchor": resolve_query_anchor,
                "lock_prospective_forecast": lock_prospective_forecast,
            }[action]
            return _ok(action, handler(request))
        if action == "interpret_structural_evidence":
            return _ok(action, _interpret_structural_summary(request))
        if action == "rank_evidence":
            return _ok(action, _rank_evidence_summary(request))
        if action == "personalize_ranking":
            return _ok(action, _personalize_ranking_summary(request))
        if action == "build_interpretation_contract":
            return _ok(action, _build_interpretation_contract_summary(request))
        if action == "prepare_historical_calibration":
            return _ok(action, _prepare_historical_calibration(request))
        if action in ("lock_blind_forecast", "lock_historical_calibration", "finalize_historical_calibration"):
            from .calibration import finalize_historical_calibration, lock_blind_forecast, lock_historical_calibration
            handler = {"lock_blind_forecast": lock_blind_forecast, "lock_historical_calibration": lock_historical_calibration, "finalize_historical_calibration": finalize_historical_calibration}[action]
            if action == "lock_historical_calibration":
                case_files = request.get("case_files")
                if not isinstance(case_files, Mapping) or not case_files:
                    raise DistributionError(
                        "lock_authority_required",
                        "historical calibration lock requires authoritative Case files",
                    )
            result = handler(request)
            if action == "lock_historical_calibration":
                lock_record_id = result.get("lock_record_id")
                changed_files = result.get("changed_files")
                if not isinstance(lock_record_id, str) or not lock_record_id.strip() or not isinstance(changed_files, Mapping):
                    raise DistributionError(
                        "lock_authority_required",
                        "historical calibration lock did not produce persistent Case authority",
                    )
            return _ok(action, result)
        if action == "export_case_markdown":
            return _ok(action, _export_case(request))
        if action == "build_delivery_bundle":
            from .delivery import build_delivery_bundle
            return _ok(action, build_delivery_bundle(request))
        if action in ("validate_case", "migrate_case", "update_case_record"):
            from .case_pack import migrate_case, update_case_record, validate_case
            handler = {"validate_case": validate_case, "migrate_case": migrate_case, "update_case_record": update_case_record}[action]
            return _ok(action, handler(request))
    except DistributionError as exc:
        return _error(action, exc.code, str(exc), exc.details)
    return _error(action, "unsupported_action", "unsupported distribution runtime action", {"supported_actions": list(SUPPORTED_ACTIONS)})
