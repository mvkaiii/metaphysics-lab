"""Validate Pilot-5's fail-closed pre-candidate sequencing gate."""
from __future__ import annotations
import re
from typing import Any, Mapping
from tools.pilot4_structural_snapshot_enumerator import STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE, STRUCTURAL_SNAPSHOT_ENUMERATION_RULE
from tools.pilot3_yearly_claim_universe import MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE, MULTI_SEGMENT_YEARLY_UNIVERSE_RULE
from tools.pilot5_segment_aware_downstream_authority import SEGMENT_AWARE_WINDOW_AUTHORITY_PROFILE, SEGMENT_AWARE_WINDOW_AUTHORITY_RULE, PREDICTION_BRIDGE_RULE
_TOP_FIELDS={"schema_version","pilot_id","gate_profile","gate_status","prerequisites","public_bindings","candidate_case_processing_allowed","private_material_disclosed","manual_override_allowed"}
_PREREQUISITES=("protocol_decisions_approved","enum01_approved","agg01_approved","auth01_approved","start_authorization_bound","source_census_frozen","intake_registry_valid","intake_eligible_for_s1","s1_source_manifest_frozen","s1_candidate_exposure_unexposed","s1_manifest_predates_candidate_processing")
_BINDINGS={"candidate_commit","package_sha256","manifest_sha256","protocol_sha256","window_policy_digest","enumeration_decision_sha256","enumeration_profile","enumeration_rule","aggregation_decision_sha256","aggregation_profile","aggregation_rule","downstream_authority_decision_sha256","downstream_authority_profile","downstream_authority_rule","prediction_bridge_rule"}
_SHA256=re.compile(r"^[0-9a-f]{64}$");_COMMIT=re.compile(r"^[0-9a-f]{40,64}$")
def _unknown(v,a,p,e):
    for k in sorted(set(v)-set(a)):e.append(f"{p}: unknown field {k!r}")
def _bool(v,p,e):
    if not isinstance(v,bool):e.append(f"{p}: expected boolean");return False
    return True
def _sha(v):return isinstance(v,str) and _SHA256.fullmatch(v) is not None
def _commit(v):return isinstance(v,str) and _COMMIT.fullmatch(v) is not None
def validate_pilot5_pre_candidate_gate(payload: Mapping[str,Any])->list[str]:
    e=[]
    if not isinstance(payload,Mapping):return ["gate: expected an object"]
    _unknown(payload,_TOP_FIELDS,"gate",e)
    for k in sorted(_TOP_FIELDS):
        if k not in payload:e.append(f"gate: missing field {k}")
    if payload.get("schema_version")!="1.0":e.append("gate.schema_version: expected '1.0'")
    if payload.get("pilot_id")!="Pilot-5":e.append("gate.pilot_id: expected 'Pilot-5'")
    if payload.get("gate_profile")!="pilot5_pre_candidate_gate_v1":e.append("gate.gate_profile: expected 'pilot5_pre_candidate_gate_v1'")
    status=payload.get("gate_status")
    if status not in {"BLOCKED","READY"}:e.append("gate.gate_status: expected BLOCKED or READY")
    p=payload.get("prerequisites");vals={}
    if not isinstance(p,Mapping):e.append("gate.prerequisites: expected an object")
    else:
        _unknown(p,set(_PREREQUISITES),"gate.prerequisites",e);seen=False
        for k in _PREREQUISITES:
            if k not in p:e.append(f"gate.prerequisites: missing field {k}");vals[k]=False
            else:_bool(p.get(k),f"gate.prerequisites.{k}",e);vals[k]=p.get(k) is True
        for k in _PREREQUISITES:
            if not vals.get(k,False):seen=True
            elif seen:e.append(f"gate.prerequisites.{k}: sequencing violation; an earlier prerequisite is false")
    b=payload.get("public_bindings")
    if not isinstance(b,Mapping):e.append("gate.public_bindings: expected an object");b={}
    else:
        _unknown(b,_BINDINGS,"gate.public_bindings",e)
        for k in sorted(_BINDINGS):
            if k not in b:e.append(f"gate.public_bindings: missing field {k}")
    processing=payload.get("candidate_case_processing_allowed");pb=_bool(processing,"gate.candidate_case_processing_allowed",e)
    private=payload.get("private_material_disclosed");_bool(private,"gate.private_material_disclosed",e)
    override=payload.get("manual_override_allowed");_bool(override,"gate.manual_override_allowed",e)
    if private is not False:e.append("gate.private_material_disclosed: public gate must keep private material undisclosed")
    if override is not False:e.append("gate.manual_override_allowed: Pilot-5 pre-candidate gate has no manual override")
    if vals.get("start_authorization_bound",False):
        if not _commit(b.get("candidate_commit")):e.append("gate.public_bindings.candidate_commit: invalid")
        for k in ("package_sha256","manifest_sha256","protocol_sha256","window_policy_digest","enumeration_decision_sha256","aggregation_decision_sha256","downstream_authority_decision_sha256"):
            if not _sha(b.get(k)):e.append(f"gate.public_bindings.{k}: invalid SHA256")
        expected={
          "enumeration_profile":STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE,
          "enumeration_rule":STRUCTURAL_SNAPSHOT_ENUMERATION_RULE,
          "aggregation_profile":MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE,
          "aggregation_rule":MULTI_SEGMENT_YEARLY_UNIVERSE_RULE,
          "downstream_authority_profile":SEGMENT_AWARE_WINDOW_AUTHORITY_PROFILE,
          "downstream_authority_rule":SEGMENT_AWARE_WINDOW_AUTHORITY_RULE,
          "prediction_bridge_rule":PREDICTION_BRIDGE_RULE,
        }
        for k,v in expected.items():
            if b.get(k)!=v:e.append(f"gate.public_bindings.{k}: does not match approved Pilot-5 contract")
    else:
        for k in sorted(_BINDINGS):
            if b.get(k) is not None:e.append(f"gate.public_bindings.{k}: must be null before start authorization is bound")
    ready=bool(vals) and all(vals.get(k,False) for k in _PREREQUISITES)
    if ready:
        if status!="READY":e.append("gate.gate_status: all prerequisites require READY")
        if processing is not True:e.append("gate.candidate_case_processing_allowed: all prerequisites require true")
    else:
        if status=="READY":e.append("gate.gate_status: READY requires every prerequisite true")
        if pb and processing is not False:e.append("gate.candidate_case_processing_allowed: must remain false until every prerequisite is true")
    return sorted(set(e))
def candidate_case_processing_allowed(payload: Mapping[str,Any])->bool:
    if validate_pilot5_pre_candidate_gate(payload):return False
    return payload.get("gate_status")=="READY" and payload.get("candidate_case_processing_allowed") is True and payload.get("manual_override_allowed") is False and payload.get("private_material_disclosed") is False and all(payload.get("prerequisites",{}).get(k) is True for k in _PREREQUISITES)
