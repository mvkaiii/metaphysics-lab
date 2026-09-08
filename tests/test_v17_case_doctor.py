import json
import unittest
from pathlib import Path

from engine.distribution.case_doctor import diagnose_case
from engine.distribution.runtime import dispatch


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v1.7-case-doctor.synthetic.json"

BIRTH = {
    "sex": "female",
    "birth_date": "1990-06-15",
    "birth_time": "10:30",
    "birth_place": "台北市",
}
LOCATION = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "synthetic_fixture",
    "provider_version": "1",
    "provider_reference": None,
}
SUBJECT = {
    "subject_id": "subj_a1b2c3d4e5f6",
    "subject_display_name": "Alex",
    "subject_short_id": "A1B2C3",
    "filename_label": "Alex",
}


class CaseDoctorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenarios = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        if not built.get("ok"):
            raise AssertionError(built)
        payload = {
            "normalized_natal": built["data"]["normalized_natal"],
            **SUBJECT,
            "generated_at": "2026-09-08T12:00:00+08:00",
            "last_modified_by": "fixture",
        }
        exported = dispatch("export_case_markdown", payload)
        if not exported.get("ok"):
            raise AssertionError(exported)
        cls.base_files = dict(exported["data"]["files"])

    def fixture(self, scenario_id):
        scenario = self.scenarios[scenario_id]
        files = dict(self.base_files)
        kind = scenario["kind"]
        if kind == "subject_id_conflict":
            target = next(name for name in files if name.endswith("04_紫微基礎資料包.md"))
            files[target] = files[target].replace(
                "subject_id: subj_a1b2c3d4e5f6",
                "subject_id: subj_deadbeefcafe",
                1,
            )
        elif kind == "clean_with_unrelated":
            files["reading-notes.md"] = "# Fictional reference notes\n"
        elif kind != "clean_base":
            raise AssertionError("scenario helper not implemented yet: %s" % scenario_id)
        return {
            "project_files": files,
            "subject_context": {
                "subject_id": SUBJECT["subject_id"],
                "subject_short_id": SUBJECT["subject_short_id"],
                "subject_display_name": SUBJECT["subject_display_name"],
            },
        }

    def test_clean_base_has_exact_output_shape_and_passes(self):
        result = diagnose_case(self.fixture("CD-01"))
        self.assertEqual(
            set(result),
            {
                "health",
                "canonical_subject",
                "authoritative_files",
                "legacy_files",
                "findings",
                "safe_analysis_scopes",
                "recommended_next_action",
                "diagnostic_digest",
            },
        )
        self.assertEqual(result["health"], "PASS")
        self.assertEqual(result["legacy_files"], [])
        self.assertEqual(result["recommended_next_action"], "none")
        self.assertEqual(len(result["diagnostic_digest"]), 64)
        self.assertEqual(result["canonical_subject"]["subject_id"], SUBJECT["subject_id"])
        self.assertEqual(result["authoritative_files"], sorted(self.base_files))

    def test_subject_identity_conflict_is_blocked(self):
        result = diagnose_case(self.fixture("CD-07"))
        self.assertEqual(result["health"], "BLOCKED")
        codes = {finding["code"] for finding in result["findings"]}
        self.assertIn("subject_id_conflict", codes)
        self.assertEqual(result["recommended_next_action"], "user_resolution_required")

    def test_unrelated_markdown_is_not_mislabeled_legacy(self):
        result = diagnose_case(self.fixture("CD-10"))
        self.assertEqual(result["health"], "PASS")
        self.assertNotIn("reading-notes.md", result["legacy_files"])
        self.assertNotIn("reading-notes.md", result["authoritative_files"])

    def test_project_file_insertion_order_does_not_change_result(self):
        payload = self.fixture("CD-01")
        reversed_payload = dict(payload)
        reversed_payload["project_files"] = dict(reversed(list(payload["project_files"].items())))
        self.assertEqual(diagnose_case(payload), diagnose_case(reversed_payload))


if __name__ == "__main__":
    unittest.main()
