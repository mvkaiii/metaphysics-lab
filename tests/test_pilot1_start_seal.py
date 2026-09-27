import hashlib
import json
from pathlib import Path
import unittest

from engine.distribution.manifest import capability_manifest_digest
from tools.validate_prospective_pilot_decision import (
    pilot_start_allowed,
    validate_decision_receipt,
)


ROOT = Path(__file__).resolve().parents[1]
SEAL_PATH = ROOT / "docs" / "research" / "pilot1-start-seal.v1.json"
RECEIPT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "prospective-pilot-decision-receipt.template.json"
)
PROTOCOL_PATH = ROOT / "docs" / "research" / "prospective-pilot-protocol.md"


class Pilot1StartSealTests(unittest.TestCase):
    def setUp(self):
        self.seal = json.loads(SEAL_PATH.read_text(encoding="utf-8"))
        self.receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))

    def test_seal_binds_expected_frozen_candidate(self):
        frozen = self.seal["frozen_candidate"]
        self.assertEqual(
            frozen["candidate_commit"],
            "79eae136a65aeb14a913a3ecdb2310d22f2ece74",
        )
        self.assertEqual(
            frozen["package_sha256"],
            "cb175e2d482fe9ca8e2d46d6c55c4b0237f1cbb9a631e0d3c50aef75f8e1e0c4",
        )

    def test_manifest_digest_is_recomputed_from_canonical_registry_truth(self):
        self.assertEqual(
            capability_manifest_digest(),
            self.seal["frozen_candidate"]["capability_manifest_sha256"],
        )
        self.assertEqual(
            self.seal["frozen_candidate"]["capability_manifest_sha256"],
            "d11a63ec5194fb49939f4b02583a8bddf7bcfb0e9e7bbd9f547af1047837e7b0",
        )

    def test_protocol_digest_is_recomputed_from_raw_approved_protocol_bytes(self):
        digest = hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            self.seal["frozen_candidate"]["protocol_sha256"],
        )
        self.assertEqual(
            digest,
            "3c836f6c711b7675960722923f8e8c6199081f1be14ffb4995024b7979762126",
        )

    def test_public_seal_does_not_publish_private_storage_digest_or_payload(self):
        storage = self.seal["private_storage_access_record"]
        self.assertEqual(storage["status"], "VERIFIED_PRIVATE")
        self.assertFalse(storage["public_digest_published"])
        serialized = json.dumps(self.seal, ensure_ascii=False).lower()
        self.assertNotIn("birth_data", serialized)
        self.assertNotIn("private_digest", serialized)
        self.assertNotIn("outcome_text", serialized)
        self.assertNotIn("prediction_text", serialized)

    def test_receipt_is_valid_and_explicitly_opens_start_gate(self):
        self.assertEqual(validate_decision_receipt(self.receipt), [])
        self.assertTrue(pilot_start_allowed(self.receipt))
        self.assertEqual(self.receipt["pilot_status"], "AUTHORIZED_NOT_STARTED")
        auth = self.receipt["pilot_start_authorization"]
        self.assertTrue(auth["authorized"])
        self.assertEqual(
            auth["candidate_commit"],
            self.seal["frozen_candidate"]["candidate_commit"],
        )
        self.assertEqual(
            auth["package_sha256"],
            self.seal["frozen_candidate"]["package_sha256"],
        )
        self.assertEqual(
            auth["manifest_sha256"],
            self.seal["frozen_candidate"]["capability_manifest_sha256"],
        )
        self.assertEqual(
            auth["protocol_sha256"],
            self.seal["frozen_candidate"]["protocol_sha256"],
        )

    def test_authorization_does_not_fabricate_execution(self):
        state = self.seal["execution_state"]
        self.assertEqual(state["real_case"], "NOT_ENROLLED")
        self.assertEqual(state["prediction_lock"], "NOT_CREATED")
        self.assertEqual(state["outcome_collection"], "NOT_STARTED")
        self.assertEqual(state["adjudication"], "NOT_STARTED")
        self.assertEqual(state["scoring"], "NOT_STARTED")


if __name__ == "__main__":
    unittest.main()
