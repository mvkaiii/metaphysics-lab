import copy
import hashlib
import json
import unittest

from engine.distribution.event_family_attribution import EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION
from engine.distribution.prospective import lock_prospective_forecast
from tools.pilot3_yearly_claim_universe import (
    build_multi_segment_yearly_claim_universe,
    build_yearly_segment_snapshot_manifest,
)
from tools.pilot5_segment_aware_downstream_authority import (
    SEGMENT_AWARE_WINDOW_AUTHORITY_PROFILE,
    SEGMENT_AWARE_WINDOW_AUTHORITY_RULE,
    PREDICTION_BRIDGE_RULE,
    build_segment_aware_window_authority,
    validate_locked_forecast_against_segment_aware_authority,
)

WINDOW_POLICY_DIGEST="a"*64
START="2027-07-01T00:00:00+08:00"
END="2027-08-31T23:59:59+08:00"

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def seal(body,field):
    out=copy.deepcopy(body);out[field]=digest(body);return out

def child(cid,parent,domain,family,ranking,structural,opened=True):
    return {
        "child_claim_id":cid,"parent_claim_id":parent,"primary_domain":domain,"event_family":family,
        "target_scope":"yearly","candidate_source":"phase3","child_opened":opened,
        "bazi_target_feature_ids":[],"ziwei_target_feature_ids":[],"modifier_feature_ids":[],
        "timing_trigger_feature_ids":[],"direct_target_dependency_families":[],
        "direct_target_systems":["bazi"] if opened else [],"maturity_summary":["experimental"] if opened else [],
        "qualification_summary":["qualified"] if opened else [],"required_verification_caveat":False,
        "family_specificity_ceiling":"event_family" if opened else None,
        "source_ranking_digest":ranking,"source_structural_interpretation_digest":structural,
    }

def segment(snapshot_id,structural,ranking,children,render_specs,confidence_by_parent):
    parents={}
    for c in children:
        pid=c["parent_claim_id"]
        parents.setdefault(pid,{
            "claim_id":pid,"primary_domain":c["primary_domain"],"event_family_candidates":[],
            "time_scope":"yearly","confidence_class":confidence_by_parent[pid],
        })
        parents[pid]["event_family_candidates"].append(c["event_family"])
    claim=seal({
        "profile_version":"lin_tianji_claim_evidence_v1-exp","target_scope":"yearly",
        "base_ranking_digest":ranking,"structural_interpretation_digest":structural,
        "packets":list(parents.values()),"global_conflicts":[],
    },"claim_evidence_digest")
    c1=seal({
        "profile_version":"lin_tianji_claim_consumption_v1-exp","claim_evidence_digest":claim["claim_evidence_digest"],
        "coordination_digest":"c"*64,"target_scope":"yearly",
        "decisions":[{"claim_id":p["claim_id"],"primary_domain":p["primary_domain"],"decision":"render","authorized_specificity":"concrete_event"} for p in parents.values()],
    },"claim_consumption_digest")
    efa=seal({
        "profile_version":EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION,"target_scope":"yearly",
        "base_ranking_digest":ranking,"structural_interpretation_digest":structural,"children":children,
    },"event_family_attribution_digest")
    c2=seal({
        "profile_version":"lin_tianji_hierarchical_claim_authority_v1-exp","target_scope":"yearly",
        "claim_evidence_digest":claim["claim_evidence_digest"],"claim_consumption_digest":c1["claim_consumption_digest"],
        "event_family_attribution_digest":efa["event_family_attribution_digest"],
        "decisions":[{"child_claim_id":c["child_claim_id"],"parent_claim_id":c["parent_claim_id"],"primary_domain":c["primary_domain"],"event_family":c["event_family"],"decision":"render" if c["child_opened"] else "abstain_child"} for c in children],
    },"hierarchical_claim_authority_digest")
    interpretation=seal({
        "profile_version":"lin_tianji_interpretation_contract_v1-exp","target_scope":"yearly",
        "base_ranking_digest":ranking,"domain_interpretation":[],
    },"interpretation_contract_digest")
    ordinary_ids={cid for spec in render_specs for cid in spec["members"]}
    hcc_children=[]
    for c in children:
        ordinary=c["child_claim_id"] in ordinary_ids
        hcc_children.append({
            "child_claim_id":c["child_claim_id"],"parent_claim_id":c["parent_claim_id"],
            "primary_domain":c["primary_domain"],"event_family":c["event_family"],
            "authority_decision":"render" if ordinary else "abstain_child",
            "authorized_specificity":"concrete_event" if ordinary else None,
            "source_systems":["bazi"] if ordinary else [],
            "cross_system_relation":"single_system_qualified" if ordinary else "no_direct_target_support",
            "visibility":"primary" if ordinary else "audit_only","required_caveats":[],
        })
    hcc=seal({
        "profile_version":"lin_tianji_hybrid_claim_composer_v1-exp","target_scope":"yearly",
        "hierarchical_claim_authority_digest":c2["hierarchical_claim_authority_digest"],
        "event_family_attribution_digest":efa["event_family_attribution_digest"],
        "source_interpretation_contract_digest":interpretation["interpretation_contract_digest"],
        "source_claim_evidence_digest":claim["claim_evidence_digest"],"children":hcc_children,"composition_groups":[],
    },"hybrid_claim_composer_digest")
    by_id={c["child_claim_id"]:c for c in hcc_children}
    render_units=[]
    for spec in render_specs:
        members=spec["members"]
        ident={"target_scope":"yearly","primary_domain":spec["domain"],"composition_type":spec["composition"],"member_child_claim_ids":members}
        render_units.append({
            "render_unit_id":"render-unit:"+digest(ident),"member_child_claim_ids":members,
            "primary_domain":spec["domain"],"target_scope":"yearly","composition_type":spec["composition"],
            "cross_system_relations":spec.get("relations",["single_system_qualified"]),
            "visibility":spec.get("visibility","primary"),"authorized_specificity":spec.get("specificity","concrete_event"),
            "required_caveats":spec.get("caveats",[]),"causality_allowed":False,
            "source_efa_digest":efa["event_family_attribution_digest"],
            "source_c2_digest":c2["hierarchical_claim_authority_digest"],
            "source_hcc_digest":hcc["hybrid_claim_composer_digest"],
        })
    ordinary=[by_id[cid] for cid in sorted(ordinary_ids)]
    audit=[row for cid,row in sorted(by_id.items()) if cid not in ordinary_ids]
    hoc=seal({
        "profile_version":"lin_tianji_hybrid_output_contract_v1-exp","target_scope":"yearly",
        "source_hybrid_claim_composer_digest":hcc["hybrid_claim_composer_digest"],
        "render_units":render_units,"children":ordinary,"audit_only_children":audit,
    },"hybrid_output_contract_digest")
    return {
        "snapshot_id":snapshot_id,"structural_interpretation_digest":structural,"base_ranking_digest":ranking,
        "claim_evidence_bundle":claim,"claim_consumption_bundle":c1,"event_family_attribution_bundle":efa,
        "hierarchical_claim_authority_bundle":c2,"interpretation_contract_bundle":interpretation,
        "hybrid_claim_composer_bundle":hcc,"hybrid_output_contract_bundle":hoc,
    },efa

class Pilot5SegmentAwareAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.s0="1"*64;self.s1="2"*64;self.r0="3"*64;self.r1="4"*64
        self.career="child:yearly:career:role_change"
        self.finance="child:yearly:finance:income_assets"
        self.a="child:yearly:network:family_a";self.b="child:yearly:network:family_b"
        c0=[
            child(self.career,"claim:yearly:career","career","role_change",self.r0,self.s0),
            child(self.finance,"claim:yearly:finance","finance","income_assets",self.r0,self.s0),
            child(self.a,"claim:yearly:network","network","family_a",self.r0,self.s0),
            child(self.b,"claim:yearly:network","network","family_b",self.r0,self.s0),
        ]
        c1=[
            child(self.career,"claim:yearly:career","career","role_change",self.r1,self.s1),
            child(self.finance,"claim:yearly:finance","finance","income_assets",self.r1,self.s1),
            child(self.a,"claim:yearly:network","network","family_a",self.r1,self.s1),
            child(self.b,"claim:yearly:network","network","family_b",self.r1,self.s1),
        ]
        self.seg0,self.efa0=segment("snap-0",self.s0,self.r0,c0,[
            {"members":[self.career],"domain":"career","composition":"single_child","specificity":"concrete_event"},
            {"members":[self.finance],"domain":"finance","composition":"single_child"},
            {"members":[self.a,self.b],"domain":"network","composition":"parallel_sibling_group"},
        ],{"claim:yearly:career":"high_confidence","claim:yearly:finance":"moderate_confidence","claim:yearly:network":"high_confidence"})
        self.seg1,self.efa1=segment("snap-1",self.s1,self.r1,c1,[
            {"members":[self.career],"domain":"career","composition":"single_child","specificity":"event_family","visibility":"secondary","caveats":["experimental_only"]},
            {"members":[self.a,self.b],"domain":"network","composition":"parallel_sibling_group"},
        ],{"claim:yearly:career":"moderate_confidence","claim:yearly:finance":"high_confidence","claim:yearly:network":"moderate_confidence"})
        self.manifest=build_yearly_segment_snapshot_manifest(
            window_policy_digest=WINDOW_POLICY_DIGEST,
            snapshots=[
                {"snapshot_index":0,"snapshot_id":"snap-0","structural_state_digest":self.s0},
                {"snapshot_index":1,"snapshot_id":"snap-1","structural_state_digest":self.s1},
            ],
        )
        self.universe=build_multi_segment_yearly_claim_universe(
            snapshot_manifest=self.manifest,
            efa_snapshots=[
                {"snapshot_id":"snap-0","event_family_attribution_bundle":self.efa0},
                {"snapshot_id":"snap-1","event_family_attribution_bundle":self.efa1},
            ],
        )

    def authority(self):
        return build_segment_aware_window_authority(
            snapshot_manifest=self.manifest,
            yearly_claim_universe=self.universe,
            segment_outputs=[self.seg0,self.seg1],
        )

    def test_profile_and_rule_are_preregistered(self):
        result=self.authority()
        self.assertEqual(result["profile_version"],SEGMENT_AWARE_WINDOW_AUTHORITY_PROFILE)
        self.assertEqual(result["authority_rule"],SEGMENT_AWARE_WINDOW_AUTHORITY_RULE)
        self.assertEqual(result["prediction_bridge_rule"],PREDICTION_BRIDGE_RULE)
        self.assertFalse(result["best_snapshot_selection_allowed"])
        self.assertFalse(result["synthetic_single_source_authority_allowed"])

    def test_unanimous_single_child_is_conservatively_authorized(self):
        result=self.authority()
        self.assertEqual(result["prediction_lock_eligible_claim_ids"],[self.career])
        row=result["prediction_claim_authority"][0]
        self.assertEqual(row["authorized_specificity"],"event_family")
        self.assertEqual(row["visibility"],"secondary")
        self.assertEqual(row["confidence_cap"],"medium")
        self.assertEqual(row["required_caveats"],["experimental_only"])

    def test_nonpersistent_render_and_multi_member_group_do_not_enter_prediction_lock(self):
        result=self.authority()
        abstain={row["child_claim_id"]:row["reason"] for row in result["window_abstained_claims"]}
        self.assertEqual(abstain[self.finance],"not_renderable_in_every_segment")
        ineligible={row["child_claim_id"]:row["reason"] for row in result["prediction_lock_ineligible_claims"]}
        self.assertIn(self.a,ineligible);self.assertIn(self.b,ineligible)

    def test_segment_order_or_provenance_tampering_fails_closed(self):
        with self.assertRaises(ValueError):
            build_segment_aware_window_authority(
                snapshot_manifest=self.manifest,yearly_claim_universe=self.universe,
                segment_outputs=[self.seg1,self.seg0],
            )
        bad=copy.deepcopy(self.seg0);bad["structural_interpretation_digest"]="f"*64
        with self.assertRaises(ValueError):
            build_segment_aware_window_authority(
                snapshot_manifest=self.manifest,yearly_claim_universe=self.universe,
                segment_outputs=[bad,self.seg1],
            )

    def test_prediction_lock_must_use_all_and_only_eligible_ids_and_respect_confidence_cap(self):
        authority=self.authority()
        anchor={
            "query_anchor_at":"2027-06-30T12:00:00+08:00","query_timezone":"Asia/Taipei",
            "knowledge_cutoff_at":"2027-06-30T12:00:00+08:00","prospective_window_start":START,
            "prospective_window_end":END,"question_reference":"pilot5-synthetic","status":"ok",
        }
        claim={
            "claim_id":self.career,"forecast_window":{"start":START,"end":END},
            "primary_domain":"career","event_family":"role_change","prediction":"Synthetic role-change claim.",
            "matched_if":"Synthetic matched criterion.","not_matched_if":"Synthetic unmatched criterion.",
            "evidence_layers":["yearly","monthly"],"evidence_time_scales":["yearly","monthly"],
            "capability_maturity":"experimental","confidence":"medium",
            "knowledge_cutoff_at":"2027-06-30T12:00:00+08:00","evaluation_eligibility":"clean_scorable",
            "contamination_state":"clean_prospective","method_version":"lin_tianji_v1.5-exp",
        }
        locked=lock_prospective_forecast({"anchor":anchor,"claims":[claim]})
        checked=validate_locked_forecast_against_segment_aware_authority(
            locked_forecast=locked,segment_aware_authority=authority,
            approved_window_start=START,approved_window_end=END,
        )
        self.assertEqual(checked["status"],"valid")
        bad=copy.deepcopy(claim);bad["confidence"]="high"
        locked_bad=lock_prospective_forecast({"anchor":anchor,"claims":[bad]})
        with self.assertRaises(ValueError):
            validate_locked_forecast_against_segment_aware_authority(
                locked_forecast=locked_bad,segment_aware_authority=authority,
                approved_window_start=START,approved_window_end=END,
            )

if __name__=="__main__":
    unittest.main()
