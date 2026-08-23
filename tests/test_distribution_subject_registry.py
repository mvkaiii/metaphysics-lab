import json
import re
import unittest
from unittest import mock

from engine.distribution.runtime import dispatch


class SubjectRegistryTests(unittest.TestCase):
    def create(self, name, registry_markdown=None):
        payload = {"subject_display_name": name}
        if registry_markdown is not None:
            payload["registry_markdown"] = registry_markdown
        return dispatch("subject.create_identity", payload)

    def test_create_identity_uses_opaque_non_pii_subject_id(self):
        with mock.patch("engine.distribution.subjects.secrets.token_hex", return_value="7f3a2c91d4e8"):
            result = self.create("Kai")
        self.assertTrue(result["ok"], result)
        identity = result["data"]["identity"]
        self.assertEqual(identity["subject_id"], "subj_7f3a2c91d4e8")
        self.assertEqual(identity["subject_short_id"], "7F3A2C")
        self.assertEqual(identity["subject_display_name"], "Kai")
        self.assertNotRegex(identity["subject_id"], r"1984|Kai|kai")
        self.assertIn("命主索引", result["data"]["registry_markdown"])

    def test_same_display_name_can_coexist_as_distinct_subjects(self):
        with mock.patch("engine.distribution.subjects.secrets.token_hex", side_effect=["111111aaaaaa", "222222bbbbbb"]):
            first = self.create("Amy")
            second = self.create("Amy", first["data"]["registry_markdown"])
        self.assertTrue(first["ok"], first)
        self.assertTrue(second["ok"], second)
        self.assertNotEqual(first["data"]["identity"]["subject_id"], second["data"]["identity"]["subject_id"])
        validation = dispatch("subject.registry_validate", {"registry_markdown": second["data"]["registry_markdown"]})
        self.assertTrue(validation["ok"], validation)
        self.assertEqual(validation["data"]["subject_count"], 2)

    def test_filename_label_normalization_is_deterministic(self):
        with mock.patch("engine.distribution.subjects.secrets.token_hex", return_value="7f3a2c91d4e8"):
            result = self.create("  Amy / Marketing  ")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["data"]["identity"]["filename_label"], "Amy-Marketing")

    def test_short_id_collision_extends_without_overwriting_existing_subject(self):
        with mock.patch("engine.distribution.subjects.secrets.token_hex", side_effect=["abcdef111111", "abcdef222222"]):
            first = self.create("Kai")
            second = self.create("Amy", first["data"]["registry_markdown"])
        self.assertTrue(second["ok"], second)
        self.assertEqual(first["data"]["identity"]["subject_short_id"], "ABCDEF")
        self.assertEqual(second["data"]["identity"]["subject_short_id"], "ABCDEF22")

    def test_rename_preserves_subject_id_and_updates_registry_display(self):
        with mock.patch("engine.distribution.subjects.secrets.token_hex", return_value="7f3a2c91d4e8"):
            created = self.create("小明")
        renamed = dispatch(
            "subject.rename",
            {
                "registry_markdown": created["data"]["registry_markdown"],
                "subject_id": created["data"]["identity"]["subject_id"],
                "new_subject_display_name": "Eric",
            },
        )
        self.assertTrue(renamed["ok"], renamed)
        self.assertEqual(renamed["data"]["identity"]["subject_id"], created["data"]["identity"]["subject_id"])
        self.assertEqual(renamed["data"]["identity"]["subject_display_name"], "Eric")
        self.assertEqual(renamed["data"]["identity"]["filename_label"], "Eric")
        self.assertIn("Eric", renamed["data"]["registry_markdown"])
        self.assertNotIn('"subject_display_name": "小明"', renamed["data"]["registry_markdown"])

    def test_registry_rejects_duplicate_subject_id_or_short_id(self):
        bad = """---\nregistry_schema_version: 1.0\n---\n# 命主索引\n\n<!-- subjects:start -->\n```json\n{\"subjects\":[{\"subject_id\":\"subj_aaaaaaaaaaaa\",\"subject_short_id\":\"AAAAAA\",\"subject_display_name\":\"A\",\"filename_label\":\"A\",\"status\":\"active\"},{\"subject_id\":\"subj_aaaaaaaaaaaa\",\"subject_short_id\":\"BBBBBB\",\"subject_display_name\":\"B\",\"filename_label\":\"B\",\"status\":\"active\"}]}\n```\n<!-- subjects:end -->\n"""
        result = dispatch("subject.registry_validate", {"registry_markdown": bad})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "subject_registry_mismatch")


if __name__ == "__main__":
    unittest.main()
