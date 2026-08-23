"""Deterministic lock/finalize helpers for blind forecast and historical calibration."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Mapping, Optional, Tuple
from zoneinfo import ZoneInfo

from engine.bazi.calendar import solar_term_time
from engine.historical.selection_integrity import verify_selection_result

from .case_identity import parse_case_filename
from .case_pack import BASE_CASE_FILES, CASE_FILES, set_case_calibration_status, update_case_record
from .errors import DistributionError


_VERIFICATION_STATES = frozenset(("matched", "partial", "not_matched", "cannot_recall"))
_BLINDNESS_STATES = frozenset(("blind", "contaminated"))


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise DistributionError("invalid_calibration_payload", "%s must be a mapping" % field, {"field": field})
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DistributionError("invalid_calibration_payload", "%s must be non-empty text" % field, {"field": field})
    return value.strip()


def _jsonable(value):
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def canonical_digest(value: object) -> str:
    raw = json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _canonical_case_sources(sources, subject_id=None) -> Tuple[list, list]:
    if not isinstance(sources, (list, tuple)):
        raise DistributionError("blind_source_violation", "source_files_used must be a list of Case files")
    canonical = []
    actual = []
    subject_short_ids = set()
    legacy_count = 0
    for source in sources:
        if not isinstance(source, str):
            raise DistributionError("blind_source_violation", "source_files_used entries must be text")
        try:
            parsed = parse_case_filename(source, CASE_FILES)
        except ValueError as exc:
            raise DistributionError(
                "blind_source_violation",
                "first-stage source is not a canonical Case file",
                {"source": source},
            ) from exc
        canonical.append(parsed["canonical_filename"])
        actual.append(source)
        if parsed["legacy"]:
            legacy_count += 1
        else:
            subject_short_ids.add(parsed["subject_short_id"])
    if legacy_count and subject_short_ids:
        raise DistributionError(
            "blind_source_violation",
            "first-stage blind forecast cannot mix legacy and subject-aware Case filenames",
            {"actual_sources": actual},
        )
    if len(subject_short_ids) > 1:
        raise DistributionError(
            "blind_source_violation",
            "first-stage blind forecast sources must belong to one subject",
            {"subject_short_ids": sorted(subject_short_ids), "actual_sources": actual},
        )
    if subject_short_ids:
        resolved_subject = str(subject_id or "")
        subject_hex = resolved_subject[5:] if resolved_subject.startswith("subj_") else ""
        is_hex = len(subject_hex) >= 12 and all(ch in "0123456789abcdef" for ch in subject_hex.lower())
        short_id = next(iter(subject_short_ids))
        if not is_hex or not subject_hex.upper().startswith(short_id):
            raise DistributionError(
                "blind_source_violation",
                "subject-aware blind sources must match payload subject_id",
                {"subject_id": resolved_subject, "subject_short_id": short_id, "actual_sources": actual},
            )
    return canonical, actual


def _actual_case_filename(case_files: Mapping[str, object], canonical: str) -> str:
    matches = []
    for filename in case_files:
        if not isinstance(filename, str):
            continue
        try:
            parsed = parse_case_filename(filename, CASE_FILES)
        except ValueError:
            continue
        if parsed["canonical_filename"] == canonical:
            matches.append(filename)
    if len(matches) != 1:
        raise DistributionError(
            "case_file_set_mismatch",
            "Case must contain exactly one requested canonical slot",
            {"canonical_filename": canonical, "matches": matches},
        )
    return matches[0]


def lock_blind_forecast(payload: Mapping[str, object]) -> dict:
    payload = _mapping(payload, "payload")
    subject_id = _text(payload.get("subject_id"), "subject_id")
    canonical_sources, actual_sources = _canonical_case_sources(payload.get("source_files_used"), subject_id)
    if len(canonical_sources) != len(BASE_CASE_FILES) or set(canonical_sources) != set(BASE_CASE_FILES):
        raise DistributionError(
            "blind_source_violation",
            "first-stage blind forecast must be locked from exactly the Base Case slots 00-04",
            {"required_sources": list(BASE_CASE_FILES), "actual_sources": actual_sources, "canonical_sources": canonical_sources},
        )
    if len(set(canonical_sources)) != len(BASE_CASE_FILES):
        raise DistributionError(
            "blind_source_violation",
            "first-stage blind forecast cannot use duplicate Base Case slots",
            {"canonical_sources": canonical_sources},
        )
    locked = {
        "blind_forecast_id": _text(payload.get("blind_forecast_id"), "blind_forecast_id"),
        "subject_id": _text(payload.get("subject_id"), "subject_id"),
        "question_type": _text(payload.get("question_type"), "question_type"),
        "question_reference": _text(payload.get("question_reference"), "question_reference"),
        "locked_at": _text(payload.get("locked_at"), "locked_at"),
        "source_files_used": actual_sources,
        "source_slots_used": list(BASE_CASE_FILES),
        "forbidden_source_slots": list(CASE_FILES[5:]),
        "blind_forecast_payload": _jsonable(_mapping(payload.get("blind_forecast_payload"), "blind_forecast_payload")),
    }
    return {"locked_payload": locked, "payload_digest": canonical_digest(locked)}


def _selector_point_map(selector: Mapping[str, object]) -> Tuple[list, dict]:
    high = selector.get("high_years")
    control = selector.get("control_year")
    if not isinstance(high, (list, tuple)) or len(high) != 4 or not isinstance(control, Mapping):
        raise DistributionError("invalid_selector_result", "selector_result must contain four high years and one control year")
    rows = []
    order = []
    for row in list(high) + [control]:
        if not isinstance(row, Mapping) or not isinstance(row.get("label_year"), int):
            raise DistributionError("invalid_selector_result", "selector year rows are malformed")
        year = int(row["label_year"])
        order.append(year)
        rows.append((year, row))
    return order, dict(rows)


def _normalize_test_point(raw: Mapping[str, object], selector_row: Mapping[str, object], origin: str) -> dict:
    year = raw.get("reference_year")
    if not isinstance(year, int):
        raise DistributionError("invalid_calibration_point", "reference_year must be an integer")
    blindness = raw.get("blindness_status", "blind")
    if blindness not in _BLINDNESS_STATES:
        raise DistributionError("invalid_calibration_point", "blindness_status must be blind or contaminated")
    domains = raw.get("primary_domains", [])
    event_family = raw.get("event_family", [])
    if not isinstance(domains, (list, tuple)) or not isinstance(event_family, (list, tuple)):
        raise DistributionError("invalid_calibration_point", "domains and event_family must be lists")
    return {
        "reference_year": year,
        "role": _text(raw.get("role"), "role"),
        "origin": origin,
        "period_start": selector_row.get("period_start"),
        "period_end": selector_row.get("period_end"),
        "primary_domains": [str(item) for item in domains],
        "event_family": [str(item) for item in event_family],
        "confidence": str(raw.get("confidence", "medium")),
        "interpretation_text": _text(raw.get("interpretation_text"), "interpretation_text"),
        "blindness_status": blindness,
    }


def lock_historical_calibration(payload: Mapping[str, object]) -> dict:
    payload = _mapping(payload, "payload")
    selector = _mapping(payload.get("selector_result"), "selector_result")
    try:
        selection_digest = verify_selection_result(selector)
    except ValueError as exc:
        raise DistributionError("selector_integrity_mismatch", str(exc)) from exc
    canonical = payload.get("canonical_test_points")
    if not isinstance(canonical, (list, tuple)) or len(canonical) != 5:
        raise DistributionError("invalid_calibration_point", "canonical_test_points must contain exactly five points")
    expected_order, selector_rows = _selector_point_map(selector)
    actual_order = [item.get("reference_year") if isinstance(item, Mapping) else None for item in canonical]
    if actual_order != expected_order:
        raise DistributionError(
            "selector_binding_mismatch",
            "canonical test points must preserve selector Top 4 + Bottom 1 selection and order",
            {"expected_years": expected_order, "actual_years": actual_order},
        )
    normalized = []
    for index, raw in enumerate(canonical):
        if not isinstance(raw, Mapping):
            raise DistributionError("invalid_calibration_point", "canonical point must be a mapping")
        expected_role = "control" if index == 4 else "high_activation"
        if raw.get("role") != expected_role:
            raise DistributionError("selector_binding_mismatch", "canonical test point role does not match selector role")
        normalized.append(_normalize_test_point(raw, selector_rows[expected_order[index]], "canonical"))

    supplemental = payload.get("supplemental_blind_points", [])
    if not isinstance(supplemental, (list, tuple)):
        raise DistributionError("invalid_calibration_point", "supplemental_blind_points must be a list")
    normalized_supplemental = []
    ranked = selector.get("ranked_periods", [])
    ranked_map = {
        int(row["label_year"]): row for row in ranked
        if isinstance(row, Mapping) and isinstance(row.get("label_year"), int)
    } if isinstance(ranked, (list, tuple)) else {}
    canonical_years = set(expected_order)
    seen_supplemental = set()
    for raw in supplemental:
        if not isinstance(raw, Mapping):
            raise DistributionError("invalid_calibration_point", "supplemental point must be a mapping")
        year = raw.get("reference_year")
        if not isinstance(year, int) or year not in ranked_map:
            raise DistributionError(
                "supplemental_outside_selector_window",
                "supplemental point must come from the selector's ranked ten-year window",
                {"reference_year": year, "ranked_years": sorted(ranked_map)},
            )
        if year in canonical_years:
            raise DistributionError(
                "supplemental_duplicates_canonical",
                "supplemental point must not duplicate a canonical Top 4 + Bottom 1 year",
                {"reference_year": year},
            )
        if year in seen_supplemental:
            raise DistributionError(
                "duplicate_supplemental_point",
                "supplemental blind points must use unique selector years",
                {"reference_year": year},
            )
        seen_supplemental.add(year)
        normalized_supplemental.append(_normalize_test_point(raw, ranked_map[year], "supplemental"))

    locked = {
        "calibration_id": _text(payload.get("calibration_id"), "calibration_id"),
        "subject_id": _text(payload.get("subject_id"), "subject_id"),
        "locked_at": _text(payload.get("locked_at"), "locked_at"),
        "canonical_selection_digest": selection_digest,
        "selector_profile_id": selector.get("profile_id"),
        "selector_rule_version": selector.get("rule_version"),
        "timezone": selector.get("timezone"),
        "control_quality": selector.get("control_quality"),
        "canonical_test_points": normalized,
        "supplemental_blind_points": normalized_supplemental,
    }
    return {
        "canonical_selection_digest": selection_digest,
        "locked_payload": locked,
        "payload_digest": canonical_digest(locked),
    }


def _actual_date(value: object) -> Optional[date]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise DistributionError("invalid_calibration_response", "actual_date must be YYYY-MM-DD text")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DistributionError("invalid_calibration_response", "actual_date must be YYYY-MM-DD text") from exc


def _flow_label_for_date(actual: date, timezone: object) -> Tuple[Optional[int], bool]:
    if isinstance(timezone, str) and timezone:
        zone = ZoneInfo(timezone)
        boundary = solar_term_time(actual.year, "立春", zone)
        if actual == boundary.date():
            return None, True
        return (actual.year if actual > boundary.date() else actual.year - 1), False
    if actual.month == 1:
        return actual.year - 1, False
    if actual.month >= 3:
        return actual.year, False
    return None, True


def _timing_evaluation(point: Mapping[str, object], response: Mapping[str, object], timezone: object) -> dict:
    state = response.get("verification_state")
    reference = int(point["reference_year"])
    if state == "cannot_recall":
        return {"timing_status": "unscorable", "offset_flow_years": None, "boundary_ambiguity": False}
    actual = _actual_date(response.get("actual_date"))
    if actual is not None:
        start = datetime.fromisoformat(str(point["period_start"]))
        end = datetime.fromisoformat(str(point["period_end"]))
        if actual in (start.date(), end.date()):
            return {"timing_status": "unscorable_or_ambiguous", "offset_flow_years": None, "boundary_ambiguity": True}
        if start.date() < actual < end.date():
            return {"timing_status": "exact_flow_year", "offset_flow_years": 0, "boundary_ambiguity": False}
        label, ambiguous = _flow_label_for_date(actual, timezone)
        if ambiguous or label is None:
            return {"timing_status": "unscorable_or_ambiguous", "offset_flow_years": None, "boundary_ambiguity": True}
        return {"timing_status": "shifted" if label != reference else "exact_flow_year", "offset_flow_years": label - reference, "boundary_ambiguity": False}
    actual_year = response.get("actual_year")
    actual_month = response.get("actual_month")
    if actual_year is not None:
        if not isinstance(actual_year, int):
            raise DistributionError("invalid_calibration_response", "actual_year must be an integer")
        if actual_month is None:
            return {"timing_status": "unscorable_or_ambiguous", "offset_flow_years": None, "boundary_ambiguity": True}
        if not isinstance(actual_month, int) or not 1 <= actual_month <= 12:
            raise DistributionError("invalid_calibration_response", "actual_month must be 1..12")
        if actual_month == 2:
            return {"timing_status": "unscorable_or_ambiguous", "offset_flow_years": None, "boundary_ambiguity": True}
        label = actual_year - 1 if actual_month == 1 else actual_year
        return {"timing_status": "shifted" if label != reference else "exact_flow_year", "offset_flow_years": label - reference, "boundary_ambiguity": False}
    if state in ("matched", "partial"):
        return {"timing_status": "exact_flow_year", "offset_flow_years": 0, "boundary_ambiguity": False}
    return {"timing_status": "missed", "offset_flow_years": None, "boundary_ambiguity": False}


def _dimension_status(state: str) -> str:
    return {"matched": "matched", "partial": "partial", "not_matched": "missed", "cannot_recall": "unscorable"}[state]


def finalize_historical_calibration(payload: Mapping[str, object]) -> dict:
    payload = _mapping(payload, "payload")
    locked = _mapping(payload.get("locked_payload"), "locked_payload")
    digest = _text(payload.get("payload_digest"), "payload_digest")
    if canonical_digest(locked) != digest:
        raise DistributionError("immutable_calibration_violation", "locked historical calibration payload digest does not match")
    responses = payload.get("responses", [])
    if not isinstance(responses, (list, tuple)):
        raise DistributionError("invalid_calibration_response", "responses must be a list")
    points = list(locked.get("canonical_test_points", [])) + list(locked.get("supplemental_blind_points", []))
    point_map = {int(point["reference_year"]): point for point in points if isinstance(point, Mapping) and isinstance(point.get("reference_year"), int)}
    records = []
    blind_scorable = 0
    seen_references = set()
    for index, raw in enumerate(responses, start=1):
        response = _mapping(raw, "response")
        reference = response.get("reference_year")
        if not isinstance(reference, int) or reference not in point_map:
            raise DistributionError("invalid_calibration_response", "response reference_year is not in locked test points")
        if reference in seen_references:
            raise DistributionError("duplicate_calibration_response", "each locked historical test point may be answered only once", {"reference_year": reference})
        seen_references.add(reference)
        state = response.get("verification_state")
        if state not in _VERIFICATION_STATES:
            raise DistributionError("invalid_calibration_response", "verification_state is invalid")
        point = point_map[reference]
        if state != "cannot_recall" and point.get("blindness_status") == "blind":
            blind_scorable += 1
        timing = _timing_evaluation(point, response, locked.get("timezone"))
        record = {
            "record_id": "%s-%02d" % (locked["calibration_id"], index),
            "record_type": "historical_calibration",
            "calibration_id": locked["calibration_id"],
            "origin": point.get("origin", "canonical"),
            "blind_prediction": {
                "classification": "命理推論", "predicted_flow_year": reference,
                "period_start": point.get("period_start"), "period_end": point.get("period_end"),
                "role": point.get("role"), "primary_domains": list(point.get("primary_domains", [])),
                "event_family": list(point.get("event_family", [])), "hypothesis": point.get("interpretation_text"),
                "blindness_status": point.get("blindness_status"),
            },
            "evaluation": {
                "classification": "已校驗資料", "verification_state": state, **timing,
                "domain_status": response.get("domain_status", _dimension_status(state)),
                "event_form_status": response.get("event_form_status", _dimension_status(state)),
            },
        }
        actual_event = response.get("actual_event")
        if state != "cannot_recall" and actual_event is not None:
            record["user_confirmed_actual"] = {
                "classification": "已驗證事件", "actual_date": response.get("actual_date"),
                "actual_year": response.get("actual_year"), "actual_month": response.get("actual_month"),
                "actual_event": str(actual_event),
            }
        if point.get("role") == "control" and locked.get("control_quality") == "relative_low":
            record["evaluation"]["control_evaluation_scope"] = "relative_low_only"
        records.append(record)
    status = "basic" if blind_scorable >= 3 else "uncalibrated"
    result = {"calibration_id": locked.get("calibration_id"), "records": records, "blind_scorable_count": blind_scorable, "historical_calibration_status": status}
    case_files = payload.get("case_files")
    if case_files is not None:
        if not isinstance(case_files, Mapping):
            raise DistributionError("invalid_case_payload", "case_files must be a mapping")
        updated_at = _text(payload.get("updated_at"), "updated_at")
        modified_by = _text(payload.get("last_modified_by", "ai"), "last_modified_by")
        current = dict(case_files)
        changed_files = {}
        for record in records:
            update = update_case_record({
                "case_files": current, "filename": "05_驗證事件紀錄.md", "operation": "append",
                "updated_at": updated_at, "last_modified_by": modified_by, "entry": record,
            })
            current.update(update["changed_files"])
            changed_files.update(update["changed_files"])
        index_actual = _actual_case_filename(current, "00_專案索引.md")
        changed_files[index_actual] = set_case_calibration_status(current[index_actual], status, updated_at, modified_by)
        result["changed_files"] = changed_files
    return result
