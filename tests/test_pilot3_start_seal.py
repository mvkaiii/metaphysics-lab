import hashlib
import json
from pathlib import Path
import unittest

from tests.historical_manifest_support import historical_capability_manifest_digest
from tools.validate_prospective_pilot_decision import (
    pilot_start_allowed,
    validate_decision_receipt,
)
from tools.validate_pilot3_pre_candidate_gate import (
    candidate_case_processing_allowed,
    validate_pilot3_pre_candidate_gate,
)


ROOT = Path(__file__).resolve().parents[1]
SEAL_PATH = ROOT / "docs" / "research" / "pilot3-start-seal.v1.json"
RECEIPT_PATH = ROOT / "docs" / "research" / "pilot3-decision-receipt.template.json"
GATE_PATH = ROOT / "docs" / "research" / "pilot3-pre-candidate-gate.template.json"
PROTOCOL_PATH = ROOT / "docs" / "research" / "pilot3-protocol.md"
WINDOW_PATH = ROOT / "docs" / "research" / "pilot3-window-policy.v1.json"
AGG_PATH = ROOT / "docs" / "research" / "pilot3-aggregation-decision.v1.json"


class Pilot3StartSealTests(unittest.TestCase):
    def setUp(self):
        self.seal = json.loads(SEAL_PATH.read_text(encoding="utf-8"))
        self.receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        self.gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))

    def test_seal_binds_exact_frozen_candidate_and_package(self):
        frozen = self.seal["frozen_candidate"]
        self.assertEqual(
            frozen["candidate_commit"],
            "4b18d74b3e12ca3a1f0946a708099aaca155fd92",
        )
        self.assertEqual(
            frozen["package_sha256"],
            "cb175e2d482fe9ca8e2d46d6c55c4b0237f1cbb9a631e0d3c50aef75f8e1e0c4",
        )
        self.assertEqual(frozen["hosted_validation_run_id"], 36384302326)
        self.assertEqual(frozen["hosted_artifact_id"], 10954170370)

    def test_manifest_digest_recomputes_from_registry_truth(self):
        self.assertEqual(
            historical_capability_manifest_digest(self.seal["frozen_candidate"]["candidate_commit"]),
            "d11a63ec5194fb49939f4b02583a8bddf7bcfb0e9e7bbd9f547af1047837e7b0",
        )
        self.assertEqual(
            historical_capability_manifest_digest(self.seal["frozen_candidate"]["candidate_commit"]),
            self.seal["frozen_candidate"]["capability_manifest_sha256"],
        )

    def test_protocol_digest_recomputes_from_final_authorized_bytes(self):
        digest = hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest()
        self.assertEqual(digest, "a9c6ed74a17f8688a25b69f2f53ad526ff67e747c5caf2308b14f1351148d548")
        self.assertEqual(
            digest,
            self.seal["frozen_candidate"]["protocol_sha256"],
        )

    def test_window_policy_digest_recomputes_from_final_authorized_bytes(self):
        digest = hashlib.sha256(WINDOW_PATH.read_bytes()).hexdigest()
        self.assertEqual(digest, "c4366eca5895215f00a44e6c7827309653a679c060acad33082c5a121cfa257e")
        self.assertEqual(
            digest,
            self.seal["frozen_candidate"]["window_policy_sha256"],
        )

    def test_aggregation_decision_digest_and_identity_are_bound(self):
        digest = hashlib.sha256(AGG_PATH.read_bytes()).hexdigest()
        frozen = self.seal["frozen_candidate"]
        self.assertEqual(digest, "443e50f78bbaec887f2cad73461096f6a13475a9ab287557148930b1519e3ad7")
        self.assertEqual(digest, frozen["aggregation_decision_sha256"])
        self.assertEqual(
            frozen["aggregation_profile"],
            "lin_tianji_multi_segment_yearly_claim_universe_v1",
        )
        self.assertEqual(
            frozen["aggregation_rule"],
            "complete_union_of_all_manifested_efa_child_inventories",
        )

    def test_start_receipt_is_authorized(self):
        self.assertEqual(validate_decision_receipt(self.receipt), [])
        self.assertTrue(pilot_start_allowed(self.receipt))
        self.assertEqual(self.receipt["pilot_status"], "AUTHORIZED_NOT_STARTED")
        auth = self.receipt["pilot_start_authorization"]
        self.assertEqual(
            auth["candidate_commit"],
            self.seal["frozen_candidate"]["candidate_commit"],
        )
        self.assertEqual(
            auth["protocol_sha256"],
            self.seal["frozen_candidate"]["protocol_sha256"],
        )

    def test_public_storage_record_discloses_no_private_digest_or_payload(self):
        storage = self.seal["private_storage_access_record"]
        self.assertEqual(storage["status"], "VERIFIED_PRIVATE")
        self.assertEqual(storage["verified_by_role"], "human_decision_owner")
        self.assertFalse(storage["digest_disclosure"])
        serialized = json.dumps(self.seal, ensure_ascii=False).lower()
        self.assertNotIn("birth_data", serialized)
        self.assertNotIn("private_digest", serialized)
        self.assertNotIn("prediction_text", serialized)
        self.assertNotIn("outcome_text", serialized)

    def test_pcg_remains_blocked_immediately_after_start_authorization(self):
        self.assertEqual(validate_pilot3_pre_candidate_gate(self.gate), [])
        prerequisites = self.gate["prerequisites"]
        self.assertTrue(prerequisites["protocol_decisions_approved"])
        self.assertTrue(prerequisites["agg01_approved"])
        self.assertTrue(prerequisites["start_authorization_bound"])
        for key in (
            "source_census_frozen",
            "intake_registry_valid",
            "intake_eligible_for_s1",
            "s1_source_manifest_frozen",
            "s1_candidate_exposure_unexposed",
            "s1_manifest_predates_candidate_processing",
        ):
            self.assertFalse(prerequisites[key], key)
        self.assertEqual(self.gate["gate_status"], "BLOCKED")
        self.assertFalse(candidate_case_processing_allowed(self.gate))

    def test_start_seal_does_not_fabricate_real_execution(self):
        state = self.seal["execution_state"]
        self.assertEqual(state["source_census"], "NOT_FROZEN")
        self.assertEqual(state["intake_registry"], "NOT_CREATED")
        self.assertEqual(state["s1_source_manifest"], "NOT_CREATED")
        self.assertEqual(state["candidate_processing"], "NOT_STARTED")
        self.assertEqual(state["claim_universe_lock"], "NOT_CREATED")
        self.assertEqual(state["prediction_lock"], "NOT_CREATED")
        self.assertEqual(state["outcome_collection"], "NOT_STARTED")


if __name__ == "__main__":
    unittest.main()