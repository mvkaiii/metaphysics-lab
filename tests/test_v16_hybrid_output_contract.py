from __future__ import annotations

import copy
import hashlib
import json
import unittest

from engine.distribution.hybrid_output_contract import (
    COMPOSITION_TYPES,
    HYBRID_OUTPUT_CONTRACT_PROFILE_VERSION,
    build_hybrid_output_contract,
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


def hcc_bundle(children, groups=()):
    body = {
        "profile_version": "lin_tianji_hybrid_claim_composer_v1-exp",
        "target_scope": "yearly",
        "hierarchical_claim_authority_digest": "c" * 64,
        "event_family_attribution_digest": "e" * 64,
        "source_interpretation_contract_digest": "i" * 64,
        "source_claim_evidence_digest": "d" * 64,
        "children": [copy.deepcopy(item) for item in children],
        "composition_groups": [copy.deepcopy(item) for item in groups],
    }
    body["hybrid_claim_composer_digest"] = digest(body)
    return body


def child(
    family,
    relation,
    *,
    decision="render",
    specificity="concrete_event",
    visibility="primary",
    caveats=(),
    systems=("bazi", "ziwei"),
):
    return {
        "child_claim_id": "child:yearly:career:%s" % family,
        "parent_claim_id": "claim:yearly:career",
        "primary_domain": "career",
        "event_family": family,
        "authority_decision": decision,
        "authorized_specificity": None if decision == "abstain_child" else specificity,
        "source_systems": list(systems),
        "cross_system_relation": relation,
        "visibility": "audit_only" if decision == "abstain_child" else visibility,
        "required_caveats": list(caveats),
    }


def unit_for_member(result, child_id):
    return next(
        unit
        for unit in result["render_units"]
        if child_id in unit["member_child_claim_ids"]
    )


class HybridOutputContractTests(unittest.TestCase):
    def test_profile_and_composition_enums_are_frozen(self):
        self.assertEqual(
            HYBRID_OUTPUT_CONTRACT_PROFILE_VERSION,
            "lin_tianji_hybrid_output_contract_v1-exp",
        )
        self.assertEqual(
            COMPOSITION_TYPES,
            (
                "single_child",
                "direct_convergence_child",
                "parallel_sibling_group",
                "layered_complement_child",
                "divergence_child",
            ),
        )

    def test_relation_to_composition_mapping_and_causality_boundary(self):
        rows = [
            child("single", "single_system_qualified", systems=("bazi",)),
            child("converged", "direct_convergence"),
            child("layered", "layered_complement", systems=("bazi",)),
            child(
                "divergent",
                "divergence",
                caveats=("parent_requires_caveat", "explicit_divergence"),
            ),
        ]
        result = build_hybrid_output_contract(
            hybrid_claim_composer_bundle=hcc_bundle(rows)
        )
        expected = {
            "single": "single_child",
            "converged": "direct_convergence_child",
            "layered": "layered_complement_child",
            "divergent": "divergence_child",
        }
        for family, composition_type in expected.items():
            unit = unit_for_member(result, "child:yearly:career:%s" % family)
            self.assertEqual(unit["composition_type"], composition_type)
            self.assertFalse(unit["causality_allowed"])
            self.assertIn(unit["authorized_specificity"], {"event_family", "concrete_event"})

    def test_renderable_membership_is_complete_and_audit_children_are_isolated(self):
        rows = [
            child("visible_a", "single_system_qualified", systems=("bazi",)),
            child("visible_b", "direct_convergence"),
            child(
                "audit",
                None,
                decision="abstain_child",
                specificity=None,
                systems=(),
            ),
        ]
        result = build_hybrid_output_contract(
            hybrid_claim_composer_bundle=hcc_bundle(rows)
        )
        renderable_ids = {
            "child:yearly:career:visible_a",
            "child:yearly:career:visible_b",
        }
        referenced = {
            child_id
            for unit in result["render_units"]
            for child_id in unit["member_child_claim_ids"]
        }
        self.assertEqual(referenced, renderable_ids)
        self.assertEqual(
            {row["child_claim_id"] for row in result["children"]},
            renderable_ids,
        )
        self.assertEqual(
            [row["child_claim_id"] for row in result["audit_only_children"]],
            ["child:yearly:career:audit"],
        )
        self.assertNotIn("child:yearly:career:audit", referenced)

    def test_parallel_group_consumes_members_once_and_uses_conservative_authority(self):
        rows = [
            child(
                "role_change",
                "single_system_qualified",
                specificity="concrete_event",
                caveats=("single_system_support",),
                systems=("bazi",),
            ),
            child(
                "leadership_change",
                "single_system_qualified",
                specificity="event_family",
                caveats=("needs_verification", "single_system_support"),
                systems=("ziwei",),
            ),
        ]
        group = {
            "composition_type": "parallel_sibling",
            "primary_domain": "career",
            "member_child_claim_ids": [
                "child:yearly:career:role_change",
                "child:yearly:career:leadership_change",
            ],
        }
        result = build_hybrid_output_contract(
            hybrid_claim_composer_bundle=hcc_bundle(rows, (group,))
        )
        self.assertEqual(len(result["render_units"]), 1)
        unit = result["render_units"][0]
        self.assertEqual(unit["composition_type"], "parallel_sibling_group")
        self.assertEqual(
            unit["member_child_claim_ids"], group["member_child_claim_ids"]
        )
        self.assertEqual(unit["authorized_specificity"], "event_family")
        self.assertEqual(
            unit["required_caveats"],
            ["single_system_support", "needs_verification"],
        )
        self.assertEqual(unit["cross_system_relations"], ["single_system_qualified"])
        self.assertFalse(unit["causality_allowed"])

    def test_render_units_bind_efa_c2_and_hcc_source_digests(self):
        rows = [child("role_change", "direct_convergence")]
        source = hcc_bundle(rows)
        result = build_hybrid_output_contract(
            hybrid_claim_composer_bundle=source
        )
        unit = result["render_units"][0]
        self.assertEqual(unit["source_efa_digest"], "e" * 64)
        self.assertEqual(unit["source_c2_digest"], "c" * 64)
        self.assertEqual(
            unit["source_hcc_digest"], source["hybrid_claim_composer_digest"]
        )
        self.assertEqual(
            result["source_hybrid_claim_composer_digest"],
            source["hybrid_claim_composer_digest"],
        )

    def test_group_cannot_reference_audit_or_unknown_child(self):
        rows = [
            child("role_change", "single_system_qualified", systems=("bazi",)),
            child(
                "audit",
                None,
                decision="abstain_child",
                systems=(),
            ),
        ]
        for bad_member in (
            "child:yearly:career:audit",
            "child:yearly:career:missing",
        ):
            group = {
                "composition_type": "parallel_sibling",
                "primary_domain": "career",
                "member_child_claim_ids": [
                    "child:yearly:career:role_change",
                    bad_member,
                ],
            }
            with self.subTest(bad_member=bad_member):
                with self.assertRaises(ValueError):
                    build_hybrid_output_contract(
                        hybrid_claim_composer_bundle=hcc_bundle(rows, (group,))
                    )

    def test_hcc_digest_tamper_fails_closed(self):
        source = hcc_bundle([child("role_change", "direct_convergence")])
        bad = copy.deepcopy(source)
        bad["children"][0]["authorized_specificity"] = "event_family"
        with self.assertRaises(ValueError):
            build_hybrid_output_contract(hybrid_claim_composer_bundle=bad)

    def test_same_semantic_input_is_byte_deterministic(self):
        source = hcc_bundle(
            [
                child(
                    "role_change",
                    "divergence",
                    caveats=("explicit_divergence", "parent_requires_caveat"),
                )
            ]
        )
        first = build_hybrid_output_contract(hybrid_claim_composer_bundle=source)
        second = build_hybrid_output_contract(
            hybrid_claim_composer_bundle=json.loads(
                json.dumps(source, ensure_ascii=False, sort_keys=False)
            )
        )
        self.assertEqual(first, second)
        self.assertEqual(
            first["hybrid_output_contract_digest"],
            second["hybrid_output_contract_digest"],
        )


if __name__ == "__main__":
    unittest.main()
