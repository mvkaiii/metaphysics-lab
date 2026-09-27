import copy
import hashlib
import unittest

from tools.validate_prospective_pilot_decision import (
    pilot_start_allowed,
    validate_decision_receipt,
)


DECISION_IDS = ["D%02d" % index for index in range(1, 13)]


def _sha(label):
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _receipt():
    return {
        "schema_version": "1.0",
        "protocol_decision_status": "PENDING_ITEM_APPROVAL",
        "pilot_status": "NOT_STARTED",
        "decisions": [
            {
                "id": decision_id,
                "status": "PENDING",
                "public_summary": "",
                "approver_role": None,
                "approved_at": None,
                "evidence_refs": [],
            }
            for decision_id in DECISION_IDS
        ],
        "pilot_start_authorization": {
            "authorized": False,
            "authorized_by_role": None,
            "authorized_at": None,
            "candidate_commit": None,
            "package_sha256": None,
            "manifest_sha256": None,
            "protocol_sha256": None,
        },
    }


def _approve_all(receipt):
    receipt["protocol_decision_status"] = "ALL_ITEMS_APPROVED"
    receipt["pilot_status"] = "READY_FOR_START_AUTHORIZATION"
    for row in receipt["decisions"]:
        row["status"] = "APPROVED"
        row["public_summary"] = "Approved de-identified public summary for %s." % row["id"]
        row["approver_role"] = "study_owner"
        row["approved_at"] = "2026-09-27T16:00:00+08:00"
    return receipt


class ProspectivePilotDecisionReceiptTests(unittest.TestCase):
    def test_all_pending_template_is_valid_and_not_startable(self):
        receipt = _receipt()
        self.assertEqual(validate_decision_receipt(receipt), [])
        self.assertFalse(pilot_start_allowed(receipt))

    def test_receipt_requires_exact_d01_to_d12_census(self):
        receipt = _receipt()
        receipt["decisions"].pop()
        errors = validate_decision_receipt(receipt)
        self.assertTrue(any("D12" in error or "decision census" in error for error in errors), errors)

    def test_approved_row_requires_public_summary_role_and_timestamp(self):
        receipt = _receipt()
        row = receipt["decisions"][0]
        row["status"] = "APPROVED"
        errors = validate_decision_receipt(receipt)
        self.assertTrue(any("D01" in error and "public_summary" in error for error in errors), errors)
        self.assertTrue(any("D01" in error and "approver_role" in error for error in errors), errors)
        self.assertTrue(any("D01" in error and "approved_at" in error for error in errors), errors)

    def test_all_items_approved_does_not_authorize_pilot_start(self):
        receipt = _approve_all(_receipt())
        self.assertEqual(validate_decision_receipt(receipt), [])
        self.assertFalse(pilot_start_allowed(receipt))

    def test_start_authorization_requires_explicit_binding_and_approver(self):
        receipt = _approve_all(_receipt())
        receipt["pilot_start_authorization"]["authorized"] = True
        receipt["pilot_status"] = "AUTHORIZED_NOT_STARTED"
        errors = validate_decision_receipt(receipt)
        self.assertTrue(any("candidate_commit" in error for error in errors), errors)
        self.assertFalse(pilot_start_allowed(receipt))

    def test_fully_bound_explicit_start_authorization_can_open_start_gate(self):
        receipt = _approve_all(_receipt())
        auth = receipt["pilot_start_authorization"]
        auth.update({
            "authorized": True,
            "authorized_by_role": "human_decision_owner",
            "authorized_at": "2026-09-27T16:30:00+08:00",
            "candidate_commit": "a" * 40,
            "package_sha256": _sha("package"),
            "manifest_sha256": _sha("manifest"),
            "protocol_sha256": _sha("protocol"),
        })
        receipt["pilot_status"] = "AUTHORIZED_NOT_STARTED"
        self.assertEqual(validate_decision_receipt(receipt), [])
        self.assertTrue(pilot_start_allowed(receipt))

    def test_public_receipt_rejects_private_case_or_outcome_payloads(self):
        receipt = _receipt()
        receipt["private_outcomes"] = [{"case_id": "secret"}]
        errors = validate_decision_receipt(receipt)
        self.assertTrue(any("private" in error.lower() or "forbidden" in error.lower() for error in errors), errors)

    def test_errors_are_deterministic(self):
        receipt = _receipt()
        receipt["protocol_decision_status"] = "ALL_ITEMS_APPROVED"
        first = validate_decision_receipt(receipt)
        second = validate_decision_receipt(copy.deepcopy(receipt))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
