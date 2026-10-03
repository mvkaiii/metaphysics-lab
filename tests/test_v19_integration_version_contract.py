import unittest

from engine.distribution.blind_sources import validate_blind_source_case
from engine.distribution.constants import (
    CASE_SCHEMA_VERSION,
    DISTRIBUTION_RUNTIME_VERSION,
    PROJECT_CONTRACT_VERSION,
    RELEASE_VERSION,
    RUNTIME_SCHEMA_VERSION,
)
from engine.distribution.runtime import dispatch
from tools import build_release_package


LOCATION = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "v1.9-test",
    "provider_reference": None,
}

IDENTITY = {
    "subject_id": "subj_7f3a2c91d4e8",
    "subject_display_name": "Kai",
    "subject_short_id": "7F3A2C",
    "filename_label": "Kai",
}

EXACT_BIRTH = {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time_precision": "exact",
    "birth_time": "19:20",
    "birth_place": "台北市",
}

BOUNDED_BIRTH = {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time_precision": "bounded",
    "birth_time_range": ["19:20", "19:21"],
    "birth_place": "台北市",
}


class V19IntegrationVersionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        natal = dispatch(
            "build_natal",
            {"birth": EXACT_BIRTH, "resolved_location": LOCATION},
        )
        if not natal.get("ok"):
            raise AssertionError(natal)
        cls.normalized = natal["data"]["normalized_natal"]

        candidate = dispatch(
            "natal.candidate_envelope",
            {"birth": BOUNDED_BIRTH, "resolved_location": LOCATION},
        )
        if not candidate.get("ok"):
            raise AssertionError(candidate)
        cls.candidate = candidate["data"]["candidate_envelope"]

    def export_full(self, **extra):
        payload = {
            "normalized_natal": self.normalized,
            **IDENTITY,
            "generated_at": "2026-10-02T21:00:00+08:00",
            "last_modified_by": "test",
        }
        payload.update(extra)
        return dispatch("export_case_markdown", payload)

    def test_v19_candidate_version_contract_is_explicit(self):
        self.assertEqual(RELEASE_VERSION, "1.9.0")
        self.assertEqual(DISTRIBUTION_RUNTIME_VERSION, "1.5-exp")
        self.assertEqual(PROJECT_CONTRACT_VERSION, "1.3")
        self.assertEqual(RUNTIME_SCHEMA_VERSION, "1.1")
        self.assertEqual(CASE_SCHEMA_VERSION, "1.1")

        info = dispatch("runtime_info", {})
        self.assertTrue(info["ok"], info)
        data = info["data"]
        self.assertEqual(data["release_version"], "1.9.0")
        self.assertEqual(data["distribution_runtime_version"], "1.5-exp")
        self.assertEqual(data["project_contract_version"], "1.3")
        self.assertEqual(data["runtime_schema_version"], "1.1")
        self.assertEqual(data["case_schema_version"], "1.1")

    def test_release_package_builder_uses_v19_candidate_identity(self):
        self.assertEqual(build_release_package.RELEASE_VERSION, "1.9.0")
        self.assertEqual(
            build_release_package.USER_PACKAGE_NAME,
            "Metaphysics-Lab-v1.9.0-User-Package.zip",
        )

    def test_default_full_case_export_is_revision_bound_contract_1_3(self):
        result = self.export_full()
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["project_contract_version"], "1.3")
        self.assertTrue(data["natal_revision_id"].startswith("nrev_"))
        self.assertTrue(data["base_case_digest"].startswith("bcase_"))

        validated = dispatch("validate_case", {"case_files": data["files"]})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(validated["data"]["project_contract_version"], "1.3")
        self.assertEqual(
            validated["data"]["natal_revision_id"],
            data["natal_revision_id"],
        )

    def test_default_partial_case_export_is_revision_bound_contract_1_3(self):
        result = dispatch(
            "export_case_markdown",
            {
                "candidate_envelope": self.candidate,
                "resolved_location": LOCATION,
                **IDENTITY,
                "generated_at": "2026-10-02T21:00:00+08:00",
                "last_modified_by": "test",
            },
        )
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["project_contract_version"], "1.3")
        self.assertTrue(data["natal_revision_id"].startswith("nrev_"))
        self.assertTrue(data["base_case_digest"].startswith("bcase_"))

        validated = dispatch("validate_case", {"case_files": data["files"]})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(validated["data"]["project_contract_version"], "1.3")
        self.assertEqual(
            validated["data"]["natal_revision_id"],
            data["natal_revision_id"],
        )

    def test_guided_build_default_export_round_trip_reaches_complete(self):
        before = dispatch(
            "natal.guided_build_state",
            {
                "birth": EXACT_BIRTH,
                "resolved_location": LOCATION,
                "normalized_natal": self.normalized,
                "subject": {**IDENTITY, "status": "active"},
            },
        )
        self.assertTrue(before["ok"], before)
        self.assertEqual(before["data"]["stage"], "ready_case_export")

        exported = self.export_full()
        self.assertTrue(exported["ok"], exported)

        after = dispatch(
            "natal.guided_build_state",
            {
                "birth": EXACT_BIRTH,
                "resolved_location": LOCATION,
                "normalized_natal": self.normalized,
                "subject": {**IDENTITY, "status": "active"},
                "case_files": exported["data"]["files"],
            },
        )
        self.assertTrue(after["ok"], after)
        self.assertEqual(after["data"]["stage"], "complete")
        self.assertEqual(
            after["data"]["authority"]["natal_revision_id"],
            exported["data"]["natal_revision_id"],
        )

    def test_explicit_legacy_1_2_export_remains_readable(self):
        result = self.export_full(project_contract_version="1.2")
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertEqual(data["project_contract_version"], "1.2")
        self.assertNotIn("natal_revision_id", data)
        self.assertNotIn("base_case_digest", data)

        validated = dispatch("validate_case", {"case_files": data["files"]})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(validated["data"]["project_contract_version"], "1.2")
        self.assertIsNone(validated["data"].get("natal_revision_id"))

    def test_legacy_1_2_base_remains_valid_blind_source_after_default_switch(self):
        legacy = self.export_full(project_contract_version="1.2")
        self.assertTrue(legacy["ok"], legacy)
        validated = validate_blind_source_case(
            legacy["data"]["files"],
            IDENTITY["subject_id"],
        )
        self.assertEqual(validated["status"], "compatible")
        self.assertEqual(validated["project_contract_version"], "1.2")
        self.assertNotIn("natal_revision_id", validated)

    def test_capability_maturity_and_routing_do_not_change_with_version_switch(self):
        info = dispatch("runtime_info", {})
        self.assertTrue(info["ok"], info)
        caps = info["data"]["capabilities"]
        self.assertEqual(caps["bazi.natal_chart"]["maturity"], "experimental")
        self.assertEqual(caps["bazi.natal_chart"]["routing"], "on_demand")
        self.assertEqual(caps["ziwei.natal_chart"]["maturity"], "experimental")
        self.assertEqual(caps["ziwei.natal_chart"]["routing"], "on_demand")
        self.assertEqual(caps["distribution.guided_natal_build"]["maturity"], "experimental")
        self.assertEqual(caps["distribution.guided_natal_build"]["routing"], "on_demand")


if __name__ == "__main__":
    unittest.main()
