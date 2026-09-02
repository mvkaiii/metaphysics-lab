from __future__ import annotations

import copy
import hashlib
import json
import unittest

from engine.distribution.hybrid_claim_composer import (
    HYBRID_CLAIM_COMPOSER_PROFILE_VERSION,
    build_hybrid_claim_composer_bundle,
)


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def claim_evidence(families, *, bazi=(), ziwei=(), global_conflicts=()):
    packet = {
        "claim_id": "claim:yearly:career",
        "primary_domain": "career",
        "event_family_candidates": list(families),
        "time_scope": "yearly",
        "bazi_evidence": [
            {"feature_id": feature_id, "system": "bazi", "role": role}
            for feature_id, role in bazi
        ],
        "ziwei_evidence": [
            {"feature_id": feature_id, "system": "ziwei", "role": role}
            for feature_id, role in ziwei
        ],
    }
    body = {
        "profile_version": "lin_tianji_claim_evidence_v1-exp",
        "target_scope": "yearly",
        "base_ranking_digest": "a" * 64,
        "structural_interpretation_digest": "b" * 64,
        "packets": [packet],
        "global_conflicts": [dict(item) for item in global_conflicts],
    }
    body["claim_evidence_digest"] = digest(body)
    return body


def child(family, systems, *, modifier_ids=(), timing_ids=(), opened=True):
    return {
        "child_claim_id": "child:yearly:career:%s" % family,
        "parent_claim_id": "claim:yearly:career",
        "primary_domain": "career",
        "event_family": family,
        "target_scope": "yearly",
        "candidate_source": "phase3",
        "child_opened": opened,
        "bazi_target_feature_ids": ["b:%s" % family] if "bazi" in systems else [],
        "ziwei_target_feature_ids": ["z:%s" % family] if "ziwei" in systems else [],
        "modifier_feature_ids": list(modifier_ids),
        "timing_trigger_feature_ids": list(timing_ids),
        "direct_target_dependency_families": ["dep:%s:%s" % (system, family) for system in systems],
        "direct_target_systems": list(systems),
        "maturity_summary": ["stable"] if opened else [],
        "qualification_summary": ["qualified"] if opened else [],
        "required_verification_caveat": False,
        "family_specificity_ceiling": "concrete_event" if opened and len(systems) == 2 else ("event_family" if opened else None),
        "source_ranking_digest": "a" * 64,
        "source_structural_interpretation_digest": "b" * 64,
    }


def efa(children):
    body = {
        "profile_version": "lin_tianji_event_family_attribution_v1-exp",
        "target_scope": "yearly",
        "base_ranking_digest": "a" * 64,
        "structural_interpretation_digest": "b" * 64,
        "children": [copy.deepcopy(item) for item in children],
    }
    body["event_family_attribution_digest"] = digest(body)
    return body


def c2(ce, efa_bundle, children, *, abstain=()):
    decisions = []
    for item in children:
        is_abstain = item["event_family"] in set(abstain)
        decisions.append(
            {
                "child_claim_id": item["child_claim_id"],
                "parent_claim_id": item["parent_claim_id"],
                "primary_domain": item["primary_domain"],
                "event_family": item["event_family"],
                "decision": "abstain_child" if is_abstain else "render_with_caveat",
                "parent_decision": "render",
                "parent_authorized_specificity": "concrete_event",
                "family_specificity_ceiling": item["family_specificity_ceiling"],
                "authorized_specificity": None if is_abstain else (item["family_specificity_ceiling"] or "event_family"),
                "source_systems": list(item["direct_target_systems"]),
                "reason_codes": ["no_direct_target_support"] if is_abstain else ["single_system_support"],
            }
        )
    body = {
        "profile_version": "lin_tianji_hierarchical_claim_authority_v1-exp",
        "target_scope": "yearly",
        "claim_evidence_digest": ce["claim_evidence_digest"],
        "claim_consumption_digest": "c" * 64,
        "event_family_attribution_digest": efa_bundle["event_family_attribution_digest"],
        "decisions": decisions,
    }
    body["hierarchical_claim_authority_digest"] = digest(body)
    return body


def interpretation(families, *, order=None, primary=True):
    order = list(families if order is None else order)
    body = {
        "profile_version": "lin_tianji_interpretation_contract_v1-exp",
        "target_scope": "yearly",
        "base_ranking_digest": "a" * 64,
        "primary_domains": ["career"] if primary else [],
        "secondary_domains": [] if primary else ["career"],
        "domain_interpretation": [
            {
                "primary_domain": "career",
                "presentation_rank": 1,
                "event_family_candidates": list(families),
                "personalized_event_family_order": order,
            }
        ],
    }
    body["interpretation_contract_digest"] = digest(body)
    return body


def compose(children, *, bazi=(), ziwei=(), conflicts=(), order=None, primary=True, abstain=()):
    families = [item["event_family"] for item in children]
    ce = claim_evidence(families, bazi=bazi, ziwei=ziwei, global_conflicts=conflicts)
    efa_bundle = efa(children)
    authority = c2(ce, efa_bundle, children, abstain=abstain)
    contract = interpretation(families, order=order, primary=primary)
    return build_hybrid_claim_composer_bundle(
        hierarchical_authority_bundle=authority,
        event_family_attribution_bundle=efa_bundle,
        interpretation_contract=contract,
        claim_evidence_bundle=ce,
    )


def by_family(bundle, family):
    return next(item for item in bundle["children"] if item["event_family"] == family)


class HybridClaimComposerTests(unittest.TestCase):
    def test_profile_version_is_explicit(self):
        self.assertEqual(
            HYBRID_CLAIM_COMPOSER_PROFILE_VERSION,
            "lin_tianji_hybrid_claim_composer_v1-exp",
        )

    def test_two_system_same_child_is_direct_convergence(self):
        rows = [child("role_change", ["bazi", "ziwei"])]
        result = compose(
            rows,
            bazi=(("b:role_change", "target_evidence"),),
            ziwei=(("z:role_change", "target_evidence"),),
        )
        self.assertEqual(by_family(result, "role_change")["cross_system_relation"], "direct_convergence")

    def test_single_system_qualified_has_no_absence_penalty(self):
        rows = [child("role_change", ["bazi"])]
        result = compose(rows, bazi=(("b:role_change", "target_evidence"),))
        row = by_family(result, "role_change")
        self.assertEqual(row["cross_system_relation"], "single_system_qualified")
        self.assertEqual(row["visibility"], "primary")
        self.assertNotIn("divergence", row["required_caveats"])

    def test_other_system_context_produces_layered_complement_without_reopening(self):
        rows = [child("role_change", ["bazi"], modifier_ids=("z:context",))]
        result = compose(
            rows,
            bazi=(("b:role_change", "target_evidence"),),
            ziwei=(("z:context", "modifier"),),
        )
        self.assertEqual(by_family(result, "role_change")["cross_system_relation"], "layered_complement")

        closed = [child("role_change", [], modifier_ids=("z:context",), opened=False)]
        result = compose(
            closed,
            ziwei=(("z:context", "modifier"),),
            abstain=("role_change",),
        )
        row = by_family(result, "role_change")
        self.assertEqual(row["visibility"], "audit_only")
        self.assertEqual(row["authority_decision"], "abstain_child")

    def test_different_systems_on_different_children_form_parallel_sibling_group(self):
        rows = [
            child("role_change", ["bazi"]),
            child("leadership_change", ["ziwei"]),
        ]
        result = compose(
            rows,
            bazi=(("b:role_change", "target_evidence"),),
            ziwei=(("z:leadership_change", "target_evidence"),),
        )
        self.assertEqual(by_family(result, "role_change")["cross_system_relation"], "single_system_qualified")
        self.assertEqual(by_family(result, "leadership_change")["cross_system_relation"], "single_system_qualified")
        self.assertEqual(len(result["composition_groups"]), 1)
        group = result["composition_groups"][0]
        self.assertEqual(group["composition_type"], "parallel_sibling")
        self.assertEqual(
            group["member_child_claim_ids"],
            [
                "child:yearly:career:role_change",
                "child:yearly:career:leadership_change",
            ],
        )

    def test_explicit_structured_conflict_has_divergence_precedence(self):
        rows = [child("role_change", ["bazi", "ziwei"])]
        conflict = {
            "reason": "disjoint_target_domain_sets",
            "bazi_target_domains": ["career"],
            "ziwei_target_domains": ["finance"],
        }
        result = compose(
            rows,
            bazi=(("b:role_change", "target_evidence"),),
            ziwei=(("z:role_change", "target_evidence"),),
            conflicts=(conflict,),
        )
        row = by_family(result, "role_change")
        self.assertEqual(row["cross_system_relation"], "divergence")
        self.assertIn("explicit_divergence", row["required_caveats"])

    def test_different_family_names_without_conflict_are_not_divergence(self):
        rows = [child("role_change", ["bazi"]), child("leadership_change", ["ziwei"])]
        result = compose(
            rows,
            bazi=(("b:role_change", "target_evidence"),),
            ziwei=(("z:leadership_change", "target_evidence"),),
        )
        self.assertNotEqual(by_family(result, "role_change")["cross_system_relation"], "divergence")
        self.assertNotEqual(by_family(result, "leadership_change")["cross_system_relation"], "divergence")

    def test_visibility_inherits_domain_presentation_and_abstention(self):
        rows = [child("role_change", ["bazi"]), child("leadership_change", ["ziwei"])]
        secondary = compose(
            rows,
            bazi=(("b:role_change", "target_evidence"),),
            ziwei=(("z:leadership_change", "target_evidence"),),
            primary=False,
            abstain=("leadership_change",),
        )
        self.assertEqual(by_family(secondary, "role_change")["visibility"], "secondary")
        self.assertEqual(by_family(secondary, "leadership_change")["visibility"], "audit_only")

    def test_event_family_presentation_order_is_inherited_without_dropping_children(self):
        rows = [child("role_change", ["bazi"]), child("leadership_change", ["ziwei"])]
        result = compose(
            rows,
            bazi=(("b:role_change", "target_evidence"),),
            ziwei=(("z:leadership_change", "target_evidence"),),
            order=("leadership_change", "role_change"),
        )
        self.assertEqual(
            [row["event_family"] for row in result["children"]],
            ["leadership_change", "role_change"],
        )
        self.assertEqual(len(result["children"]), 2)

    def test_source_digest_mismatch_fails_closed(self):
        rows = [child("role_change", ["bazi"])]
        families = ["role_change"]
        ce = claim_evidence(families, bazi=(("b:role_change", "target_evidence"),))
        efa_bundle = efa(rows)
        authority = c2(ce, efa_bundle, rows)
        contract = interpretation(families)
        bad = copy.deepcopy(authority)
        bad["event_family_attribution_digest"] = "f" * 64
        bad.pop("hierarchical_claim_authority_digest", None)
        bad["hierarchical_claim_authority_digest"] = digest(bad)
        with self.assertRaises(ValueError):
            build_hybrid_claim_composer_bundle(
                hierarchical_authority_bundle=bad,
                event_family_attribution_bundle=efa_bundle,
                interpretation_contract=contract,
                claim_evidence_bundle=ce,
            )


if __name__ == "__main__":
    unittest.main()
