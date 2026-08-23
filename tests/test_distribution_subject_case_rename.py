import unittest
from unittest import mock

from engine.distribution.runtime import dispatch


BIRTH = {"sex": "male", "birth_date": "1984-03-13", "birth_time": "19:20", "birth_place": "台北市"}
LOCATION = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "user-confirmed",
    "provider_reference": None,
}


class SubjectCaseRenameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        if not built.get("ok"):
            raise AssertionError(built)
        cls.normalized = built["data"]["normalized_natal"]

    def test_rename_updates_registry_all_materialized_files_and_manifest(self):
        with mock.patch("engine.distribution.subjects.secrets.token_hex", return_value="7f3a2c91d4e8"):
            created = dispatch("subject.create_identity", {"subject_display_name": "Kai"})
        identity = created["data"]["identity"]
        exported = dispatch(
            "export_case_markdown",
            {
                "normalized_natal": self.normalized,
                **identity,
                "generated_at": "2026-08-23T00:00:00+08:00",
                "last_modified_by": "ai",
            },
        )
        self.assertTrue(exported["ok"], exported)
        renamed = dispatch(
            "subject.rename",
            {
                "registry_markdown": created["data"]["registry_markdown"],
                "subject_id": identity["subject_id"],
                "new_subject_display_name": "Eric",
                "case_files": exported["data"]["files"],
                "updated_at": "2026-08-23T01:00:00+08:00",
                "last_modified_by": "ai",
            },
        )
        self.assertTrue(renamed["ok"], renamed)
        data = renamed["data"]
        self.assertEqual(data["identity"]["subject_id"], identity["subject_id"])
        self.assertEqual(data["identity"]["subject_short_id"], identity["subject_short_id"])
        self.assertEqual(
            set(data["changed_files"]),
            {
                "Eric_7F3A2C_00_專案索引.md",
                "Eric_7F3A2C_01_命盤核心摘要.md",
                "Eric_7F3A2C_02_命盤資料校驗紀錄.md",
                "Eric_7F3A2C_03_八字結構化資料包.md",
                "Eric_7F3A2C_04_紫微基礎資料包.md",
            },
        )
        self.assertEqual(len(data["removed_filenames"]), 5)
        index = data["changed_files"]["Eric_7F3A2C_00_專案索引.md"]
        self.assertIn("# Eric｜", index)
        self.assertIn("Eric_7F3A2C_01_命盤核心摘要.md", index)
        self.assertIn("subject_id: subj_7f3a2c91d4e8", index)
        for filename, text in data["changed_files"].items():
            self.assertEqual(
                text.count("<!-- Metaphysics Lab Case Template"),
                1,
                "%s duplicated the canonical template marker during rename" % filename,
            )
        validation = dispatch("validate_case", {"case_files": data["changed_files"]})
        self.assertTrue(validation["ok"], validation)
        self.assertEqual(validation["data"]["subject_display_name"], "Eric")


if __name__ == "__main__":
    unittest.main()
