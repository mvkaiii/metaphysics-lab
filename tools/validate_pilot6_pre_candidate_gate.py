"""Validate Pilot-6's fail-closed pre-candidate gate."""
from __future__ import annotations
import re
from collections.abc import Mapping
from tools.pilot4_structural_snapshot_enumerator import STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE,STRUCTURAL_SNAPSHOT_ENUMERATION_RULE
from tools.pilot3_yearly_claim_universe import MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE,MULTI_SEGMENT_YEARLY_UNIVERSE_RULE
from tools.pilot5_segment_aware_downstream_authority import SEGMENT_AWARE_WINDOW_AUTHORITY_PROFILE,SEGMENT_AWARE_WINDOW_AUTHORITY_RULE,PREDICTION_BRIDGE_RULE
from tools.pilot6_canonical_snapshot_manifest_gate import CANONICAL_PRE_EFA_MANIFEST_GATE_PROFILE,CANONICAL_PRE_EFA_MANIFEST_GATE_RULE
_PREREQS=("protocol_decisions_approved","enum01_approved","manifest01_approved","agg01_approved","auth01_approved","start_authorization_bound","source_census_frozen","intake_registry_valid","intake_eligible_for_s1","s1_source_manifest_frozen","s1_candidate_exposure_unexposed","s1_manifest_predates_candidate_processing")
_BINDINGS=("candidate_commit","package_sha256","manifest_sha256","protocol_sha256","window_policy_digest","enumeration_decision_sha256","enumeration_profile","enumeration_rule","manifest_decision_sha256","manifest_gate_profile","manifest_gate_rule","aggregation_decision_sha256","aggregation_profile","aggregation_rule","downstream_authority_decision_sha256","downstream_authority_profile","downstream_authority_rule","prediction_bridge_rule")
_SHA=re.compile(r"^[0-9a-f]{64}$");_COMMIT=re.compile(r"^[0-9a-f]{40,64}$")
def validate_pilot6_pre_candidate_gate(payload):
    e=[]
    if not isinstance(payload,Mapping): return ["gate: expected object"]
    if payload.get("schema_version")!="1.0": e.append("gate.schema_version")
    if payload.get("pilot_id")!="Pilot-6": e.append("gate.pilot_id")
    if payload.get("gate_profile")!="pilot6_pre_candidate_gate_v1": e.append("gate.gate_profile")
    if payload.get("gate_status") not in ("BLOCKED","READY"): e.append("gate.gate_status")
    p=payload.get("prerequisites");b=payload.get("public_bindings")
    if not isinstance(p,Mapping): e.append("gate.prerequisites");p={}
    if not isinstance(b,Mapping): e.append("gate.public_bindings");b={}
    if set(p)!=set(_PREREQS): e.append("gate.prerequisites.fields")
    if set(b)!=set(_BINDINGS): e.append("gate.public_bindings.fields")
    vals=[];seen_false=False
    for k in _PREREQS:
        v=p.get(k)
        if not isinstance(v,bool): e.append(f"gate.prerequisites.{k}")
        vals.append(v is True)
        if v is not True: seen_false=True
        elif seen_false: e.append(f"gate.prerequisites.{k}: sequencing")
    processing=payload.get("candidate_case_processing_allowed")
    if not isinstance(processing,bool): e.append("gate.candidate_case_processing_allowed")
    if payload.get("private_material_disclosed") is not False: e.append("gate.private_material_disclosed")
    if payload.get("manual_override_allowed") is not False: e.append("gate.manual_override_allowed")
    if p.get("start_authorization_bound") is True:
        if not isinstance(b.get("candidate_commit"),str) or not _COMMIT.fullmatch(b["candidate_commit"]): e.append("gate.public_bindings.candidate_commit")
        for k in ("package_sha256","manifest_sha256","protocol_sha256","window_policy_digest","enumeration_decision_sha256","manifest_decision_sha256","aggregation_decision_sha256","downstream_authority_decision_sha256"):
            if not isinstance(b.get(k),str) or not _SHA.fullmatch(b[k]): e.append(f"gate.public_bindings.{k}")
        expected={"enumeration_profile":STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE,"enumeration_rule":STRUCTURAL_SNAPSHOT_ENUMERATION_RULE,"manifest_gate_profile":CANONICAL_PRE_EFA_MANIFEST_GATE_PROFILE,"manifest_gate_rule":CANONICAL_PRE_EFA_MANIFEST_GATE_RULE,"aggregation_profile":MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE,"aggregation_rule":MULTI_SEGMENT_YEARLY_UNIVERSE_RULE,"downstream_authority_profile":SEGMENT_AWARE_WINDOW_AUTHORITY_PROFILE,"downstream_authority_rule":SEGMENT_AWARE_WINDOW_AUTHORITY_RULE,"prediction_bridge_rule":PREDICTION_BRIDGE_RULE}
        for k,v in expected.items():
            if b.get(k)!=v: e.append(f"gate.public_bindings.{k}")
    else:
        if any(b.get(k) is not None for k in _BINDINGS): e.append("gate.public_bindings: must be null before start authorization")
    ready=bool(vals) and all(vals)
    if ready!=(payload.get("gate_status")=="READY"): e.append("gate.gate_status: readiness mismatch")
    if ready!=(processing is True): e.append("gate.candidate_case_processing_allowed: readiness mismatch")
    return sorted(set(e))
def candidate_case_processing_allowed(payload):
    return not validate_pilot6_pre_candidate_gate(payload) and payload.get("gate_status")=="READY" and payload.get("candidate_case_processing_allowed") is True
