import copy
import hashlib
import json
import unittest

from engine.distribution.event_family_attribution import build_event_family_attribution_bundle
from engine.distribution.event_family_legacy_adapter import (
    EVENT_FAMILY_LEGACY_ADAPTER_PROFILE_VERSION,
    build_event_family_legacy_adapter_bundle,
)
from engine.distribution.evidence_ranker import rank_evidence
from engine.distribution.interpretation_contract_v2 import INTERPRETATION_PROFILE_VERSION_V2
from tests.test_distribution_claim_evidence import feature, structural


def canonical_digest(value):
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def frozen_legacy_contract(
    *,
    decision="render",
    specificity="event_family",
    relation="direct_domain_convergence",
    families=("role_change", "leadership_change"),
):
    payload = {
        "profile_version": INTERPRETATION_PROFILE_VERSION_V2,
        "target_scope": "yearly",
        "domain_interpretation": [
            {
                "primary_domain": "career",
                "event_family_candidates": list(families),
            }
        ],
        "claim_consumption_decisions": [
            {
                "claim_id": "claim:yearly:career",
                "primary_domain": "career",
                "decision": decision,
                "authorized_specificity": specificity,
            }
        ],
        "coordination_relations": [
            {
                "primary_domain": "career",
                "coordination_relation": relation,
            }
        ],
    }
    payload["interpretation_contract_digest"] = canonical_digest(payload)
    return payload


class EventFamilyLegacyAdapterTests(unittest.TestCase):
    def test_renderable_parent_projects_all_existing_event_family_candidates(self):
        bundle = build_event_family_legacy_adapter_bundle(
            interpretation_contract_v2=frozen_legacy_contract(),
        )

        self.assertEqual(
            [row["event_family"] for row in bundle["children"]],
            ["role_change", "leadership_change"],
        )
        self.assertTrue(all(row["decision"] == "render" for row in bundle["children"]))
        self.assertTrue(
            all(row["authorized_specificity"] == "event_family" for row in bundle["children"])
        )
        self.assertEqual(
            bundle["profile_version"],
            EVENT_FAMILY_LEGACY_ADAPTER_PROFILE_VERSION,
        )

    def test_parent_abstain_or_domain_specificity_projects_abstained_children(self):
        for contract in (
            frozen_legacy_contract(decision="abstain_claim", specificity="event_family"),
            frozen_legacy_contract(decision="render", specificity="domain"),
        ):
            with self.subTest(contract=contract["claim_consumption_decisions"][0]):
                bundle = build_event_family_legacy_adapter_bundle(
                    interpretation_contract_v2=contract,
                )
                self.assertTrue(
                    all(row["decision"] == "abstain_child" for row in bundle["children"])
                )
                self.assertTrue(
                    all(row["authorized_specificity"] is None for row in bundle["children"])
                )

    def test_parent_caveat_projects_to_every_child_without_child_level_optimization(self):
        bundle = build_event_family_legacy_adapter_bundle(
            interpretation_contract_v2=frozen_legacy_contract(decision="render_with_caveat"),
        )

        self.assertTrue(
            all(row["decision"] == "render_with_caveat" for row in bundle["children"])
        )
        self.assertTrue(all(row["caveat_required"] is True for row in bundle["children"]))

    def test_relation_projection_is_closed_and_explicitly_marked_as_legacy_projection(self):
        expected = {
            "direct_domain_convergence": "direct_convergence_projection",
            "layered_complement": "layered_complement_projection",
            "single_system_support": "single_system_projection",
            "parallel_context": "parallel_context_projection",
            "parallel_signals": "parallel_signals_projection",
        }
        for source_relation, projected_relation in expected.items():
            with self.subTest(source_relation=source_relation):
                bundle = build_event_family_legacy_adapter_bundle(
                    interpretation_contract_v2=frozen_legacy_contract(relation=source_relation),
                )
                self.assertTrue(
                    all(
                        row["projected_cross_system_relation"] == projected_relation
                        for row in bundle["children"]
                    )
                )
                self.assertTrue(
                    all(
                        row["source_coordination_relation"] == source_relation
                        for row in bundle["children"]
                    )
                )

    def test_child_identity_is_byte_equivalent_to_efa_for_same_scope_domain_family(self):
        features = [
            feature(
                "b-career",
                system="bazi",
                domain="career",
                role="target_evidence",
                scope="yearly",
                families=("role_change", "leadership_change"),
                dependency="b-career",
            )
        ]
        ranking = rank_evidence(features, target_scope="yearly")
        efa = build_event_family_attribution_bundle(
            base_ranking=ranking,
            structural_interpretation=structural(features),
        )
        legacy = build_event_family_legacy_adapter_bundle(
            interpretation_contract_v2=frozen_legacy_contract(),
        )

        self.assertEqual(
            [row["child_claim_id"] for row in legacy["children"]],
            [row["child_claim_id"] for row in efa["children"]],
        )

    def test_repeated_build_is_deterministic_and_does_not_mutate_source(self):
        source = frozen_legacy_contract()
        frozen = copy.deepcopy(source)

        first = build_event_family_legacy_adapter_bundle(interpretation_contract_v2=source)
        second = build_event_family_legacy_adapter_bundle(interpretation_contract_v2=source)

        self.assertEqual(source, frozen)
        self.assertEqual(first, second)
        self.assertEqual(first["legacy_adapter_digest"], second["legacy_adapter_digest"])


if __name__ == "__main__":
    unittest.main()
