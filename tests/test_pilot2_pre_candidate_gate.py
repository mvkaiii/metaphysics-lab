import copy
import hashlib
import unittest

from tools.validate_pilot2_pre_candidate_gate import (
    candidate_case_processing_allowed,
    validate_pilot2_pre_candidate_gate,
)


def _sha(label):
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _blocked():
    return {
        "schema_version": "1.0",
        "pilot_id": "Pilot-2",
        "gate_profile": "pilot2_pre_candidate_gate_v1",
        "gate_status": "BLOCKED",
        "prerequisites": {
            "protocol_decisions_approved": False,
            "start_authorization_bound": False,
            "source_census_frozen": False,
            "intake_registry_valid": False,
            "intake_eligible_for_s1": False,
            "s1_source_manifest_frozen": False,
            "s1_candidate_exposure_unexposed": False,
            "s1_manifest_predates_candidate_processing": False,
        },
        "public_bindings": {
            "candidate_commit": None,
            "package_sha256": None,
            "manifest_sha256": None,
            "protocol_sha256": None,
            "window_policy_digest": None,
        },
        "candidate_case_processing_allowed": False,
        "private_material_disclosed": False,
        "manual_override_allowed": False,
    }


def _ready():
    value = _blocked()
    value["gate_status"] = "READY"
    for key in value["prerequisites"]:
        value["prerequisites"][key] = True
    value["public_bindings"] = {
        "candidate_commit": "a" * 40,
        "package_sha256": _sha("package"),
        "manifest_sha256": _sha("manifest"),
        "protocol_sha256": _sha("protocol"),
        "window_policy_digest": _sha("window"),
    }
    value["candidate_case_processing_allowed"] = True
    return value


class Pilot2PreCandidateGateTests(unittest.TestCase):
    def test_all_false_template_is_valid_and_blocked(self):
        value = _blocked()
        self.assertEqual(validate_pilot2_pre_candidate_gate(value), [])
        self.assertFalse(candidate_case_processing_allowed(value))

    def test_ready_gate_requires_every_prerequisite(self):
        for key in _ready()["prerequisites"]:
            with self.subTest(key=key):
                value = _ready()
                value["prerequisites"][key] = False
                errors = validate_pilot2_pre_candidate_gate(value)
                self.assertTrue(errors)
                self.assertFalse(candidate_case_processing_allowed(value))

    def test_pilot1_failure_shape_cannot_open_gate(self):
        value = _ready()
        value["prerequisites"]["source_census_frozen"] = True
        value["prerequisites"]["s1_source_manifest_frozen"] = False
        value["prerequisites"]["s1_manifest_predates_candidate_processing"] = False
        self.assertFalse(candidate_case_processing_allowed(value))

    def test_ready_gate_requires_unexposed_candidate_status(self):
        value = _ready()
        value["prerequisites"]["s1_candidate_exposure_unexposed"] = False
        self.assertFalse(candidate_case_processing_allowed(value))

    def test_ready_gate_requires_exact_public_bindings(self):
        value = _ready()
        value["public_bindings"]["candidate_commit"] = None
        errors = validate_pilot2_pre_candidate_gate(value)
        self.assertTrue(any("candidate_commit" in item for item in errors), errors)
        self.assertFalse(candidate_case_processing_allowed(value))

    def test_manual_override_is_never_allowed(self):
        value = _ready()
        value["manual_override_allowed"] = True
        errors = validate_pilot2_pre_candidate_gate(value)
        self.assertTrue(any("manual_override" in item for item in errors), errors)
        self.assertFalse(candidate_case_processing_allowed(value))

    def test_private_material_disclosure_is_rejected(self):
        value = _ready()
        value["private_material_disclosed"] = True
        errors = validate_pilot2_pre_candidate_gate(value)
        self.assertTrue(any("private_material" in item for item in errors), errors)
        self.assertFalse(candidate_case_processing_allowed(value))

    def test_errors_are_deterministic(self):
        value = _ready()
        value["pilot_id"] = "Pilot-1"
        first = validate_pilot2_pre_candidate_gate(value)
        second = validate_pilot2_pre_candidate_gate(copy.deepcopy(value))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
