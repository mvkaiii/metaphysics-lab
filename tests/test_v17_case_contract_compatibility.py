import unittest

from engine.distribution.constants import (
    CASE_SCHEMA_VERSION,
    DISTRIBUTION_RUNTIME_VERSION,
    PROJECT_CONTRACT_VERSION,
)
from engine.distribution.runtime import dispatch


BIRTH = {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time": "19:20",
    "birth_place": "台北市",
}
LOCATION = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "synthetic-test",
    "provider_reference": None,
}


class V17CaseContractCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        if not built.get("ok"):
            raise AssertionError(built)
        cls.payload = {
            "normalized_natal": built["data"]["normalized_natal"],
            "subject_id": "subj_a1b2c3d4e5f6",
            "subject_display_name": "Example",
            "subject_short_id": "A1B2C3",
            "filename_label": "Example",
            "generated_at": "2026-09-10T12:00:00+08:00",
            "last_modified_by": "ai",
        }

    def _export(self):
        exported = dispatch("export_case_markdown", self.payload)
        self.assertTrue(exported["ok"], exported)
        return exported["data"]["files"]

    def _v16_case(self):
        return {
            name: text.replace(
                "project_contract_version: 1.2",
                "project_contract_version: 1.1",
                1,
            ).replace(
                "runtime_version_if_applicable: 1.2-exp",
                "runtime_version_if_applicable: 1.1-exp",
                1,
            )
            for name, text in self._export().items()
        }

    def test_new_case_uses_v17_contract_without_case_schema_bump(self):
        self.assertEqual(PROJECT_CONTRACT_VERSION, "1.2")
        self.assertEqual(CASE_SCHEMA_VERSION, "1.1")
        self.assertEqual(DISTRIBUTION_RUNTIME_VERSION, "1.2-exp")
        files = self._export()
        for text in files.values():
            self.assertIn("case_schema_version: 1.1", text)
            self.assertIn("project_contract_version: 1.2", text)
            self.assertIn("runtime_version_if_applicable: 1.2-exp", text)

    def test_v16_case_schema_1_1_contract_1_1_remains_readable(self):
        validated = dispatch("validate_case", {"case_files": self._v16_case()})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(validated["data"]["case_schema_version"], "1.1")
        self.assertEqual(validated["data"]["project_contract_version"], "1.1")

    def test_v16_case_can_materialize_tracking_without_contract_mixing(self):
        files = self._v16_case()
        updated = dispatch(
            "update_case_record",
            {
                "case_files": files,
                "filename": "05_驗證事件紀錄.md",
                "operation": "append",
                "updated_at": "2026-09-10T12:05:00+08:00",
                "last_modified_by": "ai",
                "entry": {
                    "record_id": "evt-compat-001",
                    "status": "verified",
                    "summary": "synthetic compatibility event",
                },
            },
        )
        self.assertTrue(updated["ok"], updated)
        merged = dict(files)
        merged.update(updated["data"]["changed_files"])
        validated = dispatch("validate_case", {"case_files": merged})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(validated["data"]["project_contract_version"], "1.1")
        tracking = next(text for name, text in merged.items() if name.endswith("05_驗證事件紀錄.md"))
        self.assertIn("project_contract_version: 1.1", tracking)
        self.assertIn("runtime_version_if_applicable: 1.1-exp", tracking)


if __name__ == "__main__":
    unittest.main()
