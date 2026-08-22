#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.natal.capabilities import get_capability as get_natal_capability


FORBIDDEN_KEYS = frozenset((
    "name",
    "full_name",
    "full_address",
    "hospital",
    "birth_datetime",
    "raw_birth_input",
    "raw_chart",
    "raw_payload",
    "external_raw",
))

REQUIRED_SECTIONS = (
    "birth_location_time",
    "bazi_natal",
    "ziwei_natal",
    "reconciliation",
    "markdown_export",
    "regression",
    "privacy",
    "phase2c_boundary",
)

_BIRTH_SUMMARY = Path("qualification/birth/location-provider-summary.json")
_BAZI_PUBLIC = Path("qualification/bazi/natal/public-lunar-python-1.4.8.json")
_BAZI_PRIVATE = Path("qualification/bazi/natal/private-summary.json")
_ZIWEI_PUBLIC = Path("qualification/ziwei/natal/public-iztro-814b77e6.json")
_ZIWEI_PRIVATE = Path("qualification/ziwei/natal/private-astralium-summary.json")

# Phase 2C0 summary is a historical qualification snapshot. Later Phase 2C
# activation must not rewrite the boundary that was true when Phase 2C0 closed.
_PHASE2C0_FLOWING_STARS_BOUNDARY = {
    "ziwei_flowing_stars_implementation": "planned",
    "ziwei_flowing_stars_maturity": None,
    "ziwei_flowing_stars_routing": "on_demand",
    "ziwei_flowing_stars_rule_version": None,
    "phase2c0_only": True,
}


def find_forbidden_keys(value: Any, prefix: str = "") -> Tuple[str, ...]:
    found = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            path = "%s.%s" % (prefix, key_text) if prefix else key_text
            if key_text in FORBIDDEN_KEYS:
                found.append(path)
            found.extend(find_forbidden_keys(item, path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, item in enumerate(value):
            path = "%s.%d" % (prefix, index) if prefix else str(index)
            found.extend(find_forbidden_keys(item, path))
    return tuple(found)


def _read_json(path: Path) -> Dict[str, Any]:
    absolute = path if path.is_absolute() else ROOT / path
    try:
        value = json.loads(absolute.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("qualification summary unavailable or invalid: %s" % path) from exc
    if not isinstance(value, dict):
        raise RuntimeError("qualification summary must be a JSON object: %s" % path)
    return value


def _content_digest(path: Path) -> str:
    absolute = path if path.is_absolute() else ROOT / path
    try:
        payload = absolute.read_bytes()
    except OSError as exc:
        raise RuntimeError("qualification evidence unavailable: %s" % path) from exc
    return "sha256:%s" % hashlib.sha256(payload).hexdigest()


def _capability_summary(capability_id: str) -> Dict[str, Any]:
    cap = get_natal_capability(capability_id)
    return {
        "implementation": cap["implementation"],
        "maturity": cap["maturity"],
        "routing": cap["routing"],
        "rule_version": cap["rule_version"],
    }


def _safe_private_runtime_aggregate(private_summary_path: Optional[Path]) -> Dict[str, Any]:
    if private_summary_path is None:
        return {
            "status": "NOT_SUPPLIED",
            "case_count": 0,
            "match_count": 0,
            "conflict_count": 0,
            "promotion_allowed": False,
            "source_digest": None,
        }

    payload = _read_json(private_summary_path)

    status = payload.get("status", "UNKNOWN")
    if not isinstance(status, str):
        status = "UNKNOWN"

    def safe_count(key: str) -> int:
        value = payload.get(key, 0)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            return 0
        return value

    promotion_allowed = payload.get("promotion_allowed", False)
    if not isinstance(promotion_allowed, bool):
        promotion_allowed = False

    return {
        "status": status,
        "case_count": safe_count("case_count"),
        "match_count": safe_count("match_count"),
        "conflict_count": safe_count("conflict_count"),
        "promotion_allowed": promotion_allowed,
        "source_digest": _content_digest(private_summary_path),
    }


def build_phase2c0_summary(private_summary_path: Optional[Path] = None) -> Dict[str, Any]:
    birth = _read_json(_BIRTH_SUMMARY)
    bazi_public = _read_json(_BAZI_PUBLIC)
    bazi_private = _read_json(_BAZI_PRIVATE)
    ziwei_public = _read_json(_ZIWEI_PUBLIC)
    ziwei_private = _read_json(_ZIWEI_PRIVATE)

    oracle = ziwei_public.get("oracle", {})
    if not isinstance(oracle, dict):
        raise RuntimeError("ziwei public contract oracle must be an object")
    component_fixtures = ziwei_public.get("component_fixtures", [])
    integration_matrix = ziwei_public.get("integration_matrix", {})
    boundary_matrix = ziwei_public.get("boundary_matrix", [])
    if not isinstance(component_fixtures, list):
        raise RuntimeError("ziwei component_fixtures must be a list")
    if not isinstance(integration_matrix, dict):
        raise RuntimeError("ziwei integration_matrix must be an object")
    if not isinstance(boundary_matrix, list):
        raise RuntimeError("ziwei boundary_matrix must be a list")

    summary = {
        "schema_version": "1.0",
        "classification": "phase2c0_qualification_summary",
        "status": "PENDING_FINAL_ACCEPTANCE",
        "birth_location_time": {
            "public_status": birth.get("status"),
            "provider": "%s@%s" % (birth.get("provider_name"), birth.get("provider_version")),
            "query_count": len(birth.get("queries", [])) if isinstance(birth.get("queries", []), list) else 0,
            "pass_count": birth.get("pass_count", 0),
            "fail_count": birth.get("fail_count", 0),
            "source_digest": _content_digest(_BIRTH_SUMMARY),
        },
        "bazi_natal": {
            "public_status": bazi_public.get("status"),
            "reference": "%s@%s" % (
                bazi_public.get("reference_engine"),
                bazi_public.get("reference_version"),
            ),
            "reference_revision": bazi_public.get("reference_source_revision"),
            "case_count": bazi_public.get("case_count", 0),
            "matched_field_count": bazi_public.get("matched_field_count", 0),
            "profile_difference_count": bazi_public.get("profile_difference_count", 0),
            "unexpected_mismatch_count": bazi_public.get("unexpected_mismatch_count", 0),
            "public_source_digest": _content_digest(_BAZI_PUBLIC),
            "private_status": bazi_private.get("status"),
            "private_case_count": bazi_private.get("case_count", 0),
            "private_source_digest": _content_digest(_BAZI_PRIVATE),
        },
        "ziwei_natal": {
            "public_contract_status": "PINNED",
            "reference": "%s@%s" % (oracle.get("engine"), oracle.get("version")),
            "oracle_revision": oracle.get("revision"),
            "component_expected_check_count": sum(
                int(item.get("expected_checks", 0))
                for item in component_fixtures
                if isinstance(item, dict)
            ),
            "integration_expected_chart_count": integration_matrix.get("expected_chart_count", 0),
            "boundary_expected_case_count": len(boundary_matrix),
            "public_source_digest": _content_digest(_ZIWEI_PUBLIC),
            "private_status": ziwei_private.get("status"),
            "private_case_count": ziwei_private.get("case_count", 0),
            "private_promotion_allowed": bool(ziwei_private.get("promotion_allowed", False)),
            "private_source_digest": _content_digest(_ZIWEI_PRIVATE),
        },
        "reconciliation": _capability_summary("natal.reconciliation"),
        "markdown_export": _capability_summary("natal.markdown_export"),
        "regression": {
            "status": "PENDING_FINAL_ACCEPTANCE",
            "phase2c0_acceptance_pass": False,
            "final_gate_task": 10,
        },
        "privacy": {
            "status": "PASS",
            "forbidden_key_count": 0,
            "private_runtime_aggregate": _safe_private_runtime_aggregate(private_summary_path),
        },
        "phase2c_boundary": dict(_PHASE2C0_FLOWING_STARS_BOUNDARY),
    }

    forbidden = find_forbidden_keys(summary)
    if forbidden:
        raise RuntimeError("phase summary contains forbidden keys: %s" % ", ".join(forbidden))
    return summary


def _write_json(value: Dict[str, Any], output: Optional[Path], compact: bool) -> None:
    if compact:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    else:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if output is None:
        sys.stdout.write(text)
    else:
        output.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate privacy-safe Phase 2C0 qualification evidence.")
    parser.add_argument("--private-summary", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()

    summary = build_phase2c0_summary(private_summary_path=args.private_summary)
    _write_json(summary, args.output, args.compact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
