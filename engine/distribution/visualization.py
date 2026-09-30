"""Portable visualization actions for the AI distribution runtime."""

from __future__ import annotations

import hashlib
from typing import Mapping

from engine.bazi.natal_models import BaziNatalProfile
from engine.visualization.bazi_decadal import canonical_json_bytes, project_bazi_decadal
from renderers.svg.bazi_decadal import render_bazi_decadal_svg, render_bazi_decadal_text

from .constants import DISTRIBUTION_RUNTIME_VERSION, RELEASE_VERSION
from .errors import DistributionError
from .manifest import capability_manifest_digest, load_capability_manifest


_ALLOWED_FIELDS = frozenset(("project_natal", "normalized_natal", "as_of", "visibility_mode"))
_REPO = "mvkaiii/metaphysics-lab"


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise DistributionError(
            "invalid_visualization_payload",
            "%s must be a structured mapping" % field,
            {"field": field},
        )
    return value


def _project_natal(payload: Mapping[str, object]) -> Mapping[str, object]:
    has_project = payload.get("project_natal") is not None
    has_normalized = payload.get("normalized_natal") is not None
    if has_project == has_normalized:
        raise DistributionError(
            "invalid_visualization_payload",
            "provide exactly one of project_natal or normalized_natal",
        )
    if has_project:
        return _mapping(payload.get("project_natal"), "project_natal")
    normalized = _mapping(payload.get("normalized_natal"), "normalized_natal")
    project = normalized.get("project")
    if project is None:
        raise DistributionError(
            "visualization_project_natal_required",
            "normalized_natal does not contain a Project natal view",
        )
    return _mapping(project, "normalized_natal.project")


def _engine_view(project_natal: Mapping[str, object]) -> tuple[dict, dict]:
    bazi = _mapping(project_natal.get("bazi"), "project_natal.bazi")
    time_basis = _mapping(project_natal.get("time_basis"), "project_natal.time_basis")
    source = _mapping(project_natal.get("source"), "project_natal.source")
    if source.get("source_type") != "project":
        raise DistributionError(
            "visualization_project_natal_required",
            "Bazi decadal visualization requires a Project natal source",
        )

    timezone = time_basis.get("timezone")
    direction = bazi.get("decadal_direction")
    periods = bazi.get("decadal_periods")
    if not isinstance(timezone, str) or not timezone:
        raise DistributionError("invalid_visualization_payload", "project_natal timezone is unavailable")
    if direction not in ("forward", "reverse"):
        raise DistributionError("invalid_visualization_payload", "project_natal decadal direction is unavailable")
    if not isinstance(periods, list) or not periods:
        raise DistributionError("invalid_visualization_payload", "project_natal decadal periods are unavailable")

    manifest = load_capability_manifest()
    capability = manifest["capabilities"]["bazi.natal_chart"]
    profile = BaziNatalProfile()
    source_payload = {
        "bazi": {
            "profile": {
                "profile_id": profile.profile_id,
                "rule_version": profile.rule_version,
                "age_basis": "continuous_years_from_jie_interval",
                "interval_semantics": "[start_at,end_at)",
            },
            "timezone": timezone,
            "decadal_direction": direction,
            "decadal_periods": periods,
        }
    }
    source_payload_sha256 = hashlib.sha256(canonical_json_bytes(source_payload)).hexdigest()
    engine_view = {
        "schema_version": "1.0",
        "input_status": "resolved_unique",
        "resolved_candidate_count": 1,
        "project_natal": source_payload,
        "source_capabilities": [{
            "capability_id": "bazi.natal_chart",
            "scope": "decadal_periods",
            "profile_id": profile.profile_id,
            "rule_version": capability["rule_version"],
            "maturity": capability["maturity"],
            "routing": capability["routing"],
        }],
        "provenance": {
            "repo": _REPO,
            "source_commit": None,
            "release_version": RELEASE_VERSION,
            "distribution_runtime_version": DISTRIBUTION_RUNTIME_VERSION,
            "manifest_sha256": capability_manifest_digest(manifest),
            "source_payload_sha256": source_payload_sha256,
            "projection_version": "runtime-adapter-v1",
        },
    }
    return engine_view, manifest


def render_bazi_decadal_timeline(payload: Mapping[str, object]) -> dict:
    if not isinstance(payload, Mapping):
        raise DistributionError("invalid_visualization_payload", "visualization payload must be a mapping")
    unknown = sorted(set(payload) - _ALLOWED_FIELDS)
    if unknown:
        raise DistributionError(
            "invalid_visualization_payload",
            "visualization payload contains unknown fields",
            {"unknown_fields": unknown},
        )
    as_of = payload.get("as_of")
    visibility_mode = payload.get("visibility_mode")
    if not isinstance(as_of, str) or not as_of:
        raise DistributionError("invalid_visualization_payload", "as_of must be an ISO datetime with offset")
    if visibility_mode not in ("blind", "identified"):
        raise DistributionError(
            "invalid_visualization_payload",
            "visibility_mode must be blind or identified",
        )

    project = _project_natal(payload)
    engine_view, manifest = _engine_view(project)
    timezone = engine_view["project_natal"]["bazi"]["timezone"]
    try:
        chart = project_bazi_decadal(
            engine_view,
            manifest,
            as_of=as_of,
            timezone=timezone,
            visibility_mode=visibility_mode,
        )
        svg = render_bazi_decadal_svg(chart)
        text = render_bazi_decadal_text(chart)
    except ValueError as exc:
        raise DistributionError("visualization_contract_error", str(exc)) from exc

    return {
        "chart": chart,
        "svg": svg,
        "text": text,
        "artifact": {
            "suggested_filename": "bazi-decadal-timeline.svg",
            "media_type": "image/svg+xml",
            "text_fallback_filename": "bazi-decadal-timeline.txt",
        },
        "presentation": {
            "surface": "experimental",
            "preferred": "svg",
            "fallback": "text",
            "ranking_authority": False,
            "predictive_evidence": False,
        },
    }
