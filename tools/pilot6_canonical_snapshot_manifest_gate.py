"""Pilot-6 canonical pre-EFA snapshot-manifest gate.

Research-only. It binds the already-approved enumeration output and one
pre-EFA structural-state digest per segment to the existing canonical manifest
builder. Any EFA execution before this gate is READY permanently invalidates
the run; no retrospective repair is allowed.
"""
from __future__ import annotations
import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from tools.pilot4_structural_snapshot_enumerator import (
    build_snapshot_manifest_from_enumeration,
    validate_structural_snapshot_enumeration,
)
from tools.pilot3_yearly_claim_universe import (
    YEARLY_SEGMENT_SNAPSHOT_MANIFEST_PROFILE,
    YEARLY_SEGMENT_SNAPSHOT_MANIFEST_SCHEMA,
)

CANONICAL_PRE_EFA_MANIFEST_GATE_SCHEMA="pilot6-canonical-pre-efa-manifest-gate.v1"
CANONICAL_PRE_EFA_MANIFEST_GATE_PROFILE="lin_tianji_canonical_pre_efa_snapshot_manifest_gate_v1"
CANONICAL_PRE_EFA_MANIFEST_GATE_RULE="canonical_helper_materialize_exact_schema_validate_digest_before_any_efa"
READY_STATUS="READY_FOR_EFA"

def _canonical_bytes(value):
    try:
        return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")
    except (TypeError,ValueError) as exc:
        raise ValueError("manifest gate input must contain canonical JSON values") from exc

def _digest(value): return hashlib.sha256(_canonical_bytes(value)).hexdigest()

def _scan_forbidden(value,path="root"):
    if isinstance(value,Mapping):
        for key,child in value.items():
            lowered=str(key).lower()
            if any(token in lowered for token in ("claim","event_family_attribution","prediction","outcome","score")):
                raise ValueError(f"{path}: forbidden pre-EFA content field {key!r}")
            _scan_forbidden(child,f"{path}.{key}")
    elif isinstance(value,list):
        for i,child in enumerate(value): _scan_forbidden(child,f"{path}[{i}]")

def build_canonical_pre_efa_manifest_gate(
    *,
    enumeration: Mapping[str,object],
    structural_state_digests: Sequence[str],
    supplied_snapshot_manifest: Mapping[str,object],
    efa_execution_started: bool,
) -> dict:
    if efa_execution_started is not False:
        raise ValueError("MANIFEST-01 must be READY before any EFA execution starts")
    validated=validate_structural_snapshot_enumeration(enumeration)
    expected=build_snapshot_manifest_from_enumeration(
        enumeration=validated,
        structural_state_digests=structural_state_digests,
    )
    supplied=copy.deepcopy(dict(supplied_snapshot_manifest))
    _scan_forbidden(supplied)
    if _canonical_bytes(supplied)!=_canonical_bytes(expected):
        raise ValueError("supplied snapshot manifest must exactly equal canonical helper output")
    if supplied.get("schema_version")!=YEARLY_SEGMENT_SNAPSHOT_MANIFEST_SCHEMA:
        raise ValueError("canonical snapshot manifest schema mismatch")
    if supplied.get("profile_version")!=YEARLY_SEGMENT_SNAPSHOT_MANIFEST_PROFILE:
        raise ValueError("canonical snapshot manifest profile mismatch")
    if supplied.get("promotion_allowed") is not False:
        raise ValueError("promotion_allowed must remain false")
    body={
        "schema_version":CANONICAL_PRE_EFA_MANIFEST_GATE_SCHEMA,
        "profile_version":CANONICAL_PRE_EFA_MANIFEST_GATE_PROFILE,
        "manifest_rule":CANONICAL_PRE_EFA_MANIFEST_GATE_RULE,
        "status":READY_STATUS,
        "enumeration_digest":validated["enumeration_digest"],
        "snapshot_manifest_digest":supplied["snapshot_manifest_digest"],
        "window_policy_digest":supplied["window_policy_digest"],
        "canonical_manifest_schema":YEARLY_SEGMENT_SNAPSHOT_MANIFEST_SCHEMA,
        "canonical_manifest_profile":YEARLY_SEGMENT_SNAPSHOT_MANIFEST_PROFILE,
        "efa_execution_started":False,
        "retrospective_repair_allowed":False,
        "manual_override_allowed":False,
        "promotion_allowed":False,
    }
    return {**body,"manifest_gate_digest":_digest(body)}
