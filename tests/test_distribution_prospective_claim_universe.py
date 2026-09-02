import hashlib
import importlib
import importlib.util
import json
import unittest

from engine.distribution.errors import DistributionError
from engine.distribution.event_family_attribution import EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION
from engine.distribution.event_family_legacy_adapter import (
    EVENT_FAMILY_LEGACY_ADAPTER_PROFILE_VERSION,
)
from engine.distribution.hybrid_output_contract import (
    HYBRID_OUTPUT_CONTRACT_PROFILE_VERSION,
)


def _digest(payload):
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _efa_bundle(children=None):
    if children is None:
        children = [
            {
                "child_claim_id": "child:yearly:career:career_role",
                "child_opened": True,
            },
            {
                "child_claim_id": "child:yearly:finance:earned_income",
                "child_opened": False,
            },
        ]
    body = {
        "profile_version": EVENT_FAMILY_ATTRIBUTION_PROFILE_VERSION,
        "target_scope": "yearly",
        "base_ranking_digest": "1" * 64,
        "structural_interpretation_digest": "2" * 64,
        "children": children,
    }
    return {**body, "event_family_attribution_digest": _digest(body)}


def _legacy_bundle(ids=None):
    if ids is None:
        ids = [
            "child:yearly:career:career_role",
            "child:yearly:finance:earned_income",
        ]
    body = {
        "profile_version": EVENT_FAMILY_LEGACY_ADAPTER_PROFILE_VERSION,
        "target_scope": "yearly",
        "source_interpretation_contract_digest": "3" * 64,
        "children": [{"child_claim_id": child_id} for child_id in ids],
    }
    return {**body, "legacy_adapter_digest": _digest(body)}


def _hoc_bundle(ordinary=None, audit=None):
    if ordinary is None:
        ordinary = ["child:yearly:career:career_role"]
    if audit is None:
        audit = ["child:yearly:finance:earned_income"]
    body = {
        "profile_version": HYBRID_OUTPUT_CONTRACT_PROFILE_VERSION,
        "target_scope": "yearly",
        "source_hybrid_claim_composer_digest": "4" * 64,
        "render_units": [
            {
                "member_child_claim_ids": list(ordinary),
            }
        ],
        "children": [{"child_claim_id": child_id} for child_id in ordinary],
        "audit_only_children": [{"child_claim_id": child_id} for child_id in audit],
    }
    return {**body, "hybrid_output_contract_digest": _digest(body)}


class DistributionProspectiveClaimUniverseTests(unittest.TestCase):
    def _module(self):
        spec = importlib.util.find_spec("engine.distribution.prospective_claim_universe")
        self.assertIsNotNone(
            spec,
            "pre-arm claim-universe governance requires engine.distribution.prospective_claim_universe",
        )
        return importlib.import_module("engine.distribution.prospective_claim_universe")

    def test_efa_inventory_contains_opened_and_unopened_children(self):
        module = self._module()
        ids = module.child_ids_from_efa_bundle(_efa_bundle())
        self.assertEqual(
            ids,
            (
                "child:yearly:career:career_role",
                "child:yearly:finance:earned_income",
            ),
        )

    def test_efa_child_ids_must_be_unique_and_nonempty(self):
        module = self._module()
        invalid_children = (
            [
                {"child_claim_id": "child:yearly:career:career_role", "child_opened": True},
                {"child_claim_id": "child:yearly:career:career_role", "child_opened": False},
            ],
            [{"child_claim_id": "", "child_opened": True}],
        )
        for children in invalid_children:
            with self.subTest(children=children):
                with self.assertRaises(DistributionError) as caught:
                    module.child_ids_from_efa_bundle(_efa_bundle(children))
                self.assertEqual(caught.exception.code, "invalid_prospective_claim_universe")

    def test_s1_locked_ids_must_exact_match_complete_efa_inventory(self):
        module = self._module()
        locked = [
            "child:yearly:finance:earned_income",
            "child:yearly:career:career_role",
        ]
        receipt = module.validate_s1_case_claims_against_efa(
            locked_claim_ids=locked,
            efa_bundle=_efa_bundle(),
        )
        self.assertEqual(receipt["status"], "valid")
        self.assertEqual(receipt["claim_count"], 2)
        self.assertNotIn("locked_claim_ids", receipt)
        self.assertNotIn("child_claim_ids", receipt)

    def test_s1_missing_extra_or_rewritten_ids_fail_closed(self):
        module = self._module()
        cases = (
            ["child:yearly:career:career_role"],
            [
                "child:yearly:career:career_role",
                "child:yearly:finance:earned_income",
                "child:yearly:health:health_load",
            ],
            [
                "child:yearly:career:career_role:q4",
                "child:yearly:finance:earned_income:q4",
            ],
        )
        for locked in cases:
            with self.subTest(locked=locked):
                with self.assertRaises(DistributionError) as caught:
                    module.validate_s1_case_claims_against_efa(
                        locked_claim_ids=locked,
                        efa_bundle=_efa_bundle(),
                    )
                self.assertEqual(caught.exception.code, "invalid_prospective_claim_universe")

    def test_legacy_children_must_exact_match_s1_locked_universe(self):
        module = self._module()
        locked = [
            "child:yearly:career:career_role",
            "child:yearly:finance:earned_income",
        ]
        receipt = module.validate_downstream_arm_universe(
            locked_claim_ids=locked,
            arm_type="legacy",
            arm_bundle=_legacy_bundle(),
        )
        self.assertEqual(receipt["status"], "valid")
        self.assertEqual(receipt["arm_type"], "legacy")
        self.assertEqual(receipt["claim_count"], 2)

    def test_hoc_universe_is_ordinary_plus_audit_only_children(self):
        module = self._module()
        locked = [
            "child:yearly:career:career_role",
            "child:yearly:finance:earned_income",
        ]
        receipt = module.validate_downstream_arm_universe(
            locked_claim_ids=locked,
            arm_type="candidate_hoc",
            arm_bundle=_hoc_bundle(),
        )
        self.assertEqual(receipt["status"], "valid")
        self.assertEqual(receipt["arm_type"], "candidate_hoc")
        self.assertEqual(receipt["claim_count"], 2)

    def test_hoc_render_subset_cannot_define_shared_universe(self):
        module = self._module()
        with self.assertRaises(DistributionError) as caught:
            module.validate_downstream_arm_universe(
                locked_claim_ids=["child:yearly:career:career_role"],
                arm_type="candidate_hoc",
                arm_bundle=_hoc_bundle(),
            )
        self.assertEqual(caught.exception.code, "invalid_prospective_claim_universe")

    def test_downstream_arm_with_missing_or_extra_id_fails_closed(self):
        module = self._module()
        locked = [
            "child:yearly:career:career_role",
            "child:yearly:finance:earned_income",
        ]
        invalid = (
            ("legacy", _legacy_bundle(["child:yearly:career:career_role"])),
            (
                "candidate_hoc",
                _hoc_bundle(
                    ordinary=["child:yearly:career:career_role"],
                    audit=[
                        "child:yearly:finance:earned_income",
                        "child:yearly:health:health_load",
                    ],
                ),
            ),
        )
        for arm_type, bundle in invalid:
            with self.subTest(arm_type=arm_type):
                with self.assertRaises(DistributionError) as caught:
                    module.validate_downstream_arm_universe(
                        locked_claim_ids=locked,
                        arm_type=arm_type,
                        arm_bundle=bundle,
                    )
                self.assertEqual(caught.exception.code, "invalid_prospective_claim_universe")

    def test_validation_receipts_are_aggregate_only(self):
        module = self._module()
        locked = [
            "child:yearly:career:career_role",
            "child:yearly:finance:earned_income",
        ]
        s1 = module.validate_s1_case_claims_against_efa(
            locked_claim_ids=locked,
            efa_bundle=_efa_bundle(),
        )
        hoc = module.validate_downstream_arm_universe(
            locked_claim_ids=locked,
            arm_type="candidate_hoc",
            arm_bundle=_hoc_bundle(),
        )
        serialized = json.dumps([s1, hoc], ensure_ascii=False, sort_keys=True)
        self.assertNotIn("child:yearly:career:career_role", serialized)
        self.assertNotIn("child:yearly:finance:earned_income", serialized)
        self.assertNotIn("outcome", serialized)
        self.assertNotIn("oracle", serialized)


if __name__ == "__main__":
    unittest.main()
