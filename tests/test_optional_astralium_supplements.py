import unittest

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
    "provider_version": "user-confirmed",
    "provider_reference": None,
}
ASTRALIUM_SOURCE = {
    "source_type": "external",
    "source_name": "Astralium",
    "source_version": "synthetic-public",
    "rule_profile": "astralium-imported",
    "rule_version": "unknown",
    "maturity": "external",
    "validation_status": "provided",
}


class OptionalAstraliumSupplementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        if not built.get("ok"):
            raise AssertionError(built)
        project = built["data"]["project_natal"]
        external_chart = {
            "birth": {},
            "bazi": {"pillars": dict(project["bazi"]["pillars"])},
            "ziwei": {"ming_palace": project["ziwei"]["ming_palace"]},
        }
        reconciled = dispatch(
            "reconcile_natal",
            {
                "project_natal": project,
                "external_source": ASTRALIUM_SOURCE,
                "external_chart": external_chart,
            },
        )
        if not reconciled.get("ok"):
            raise AssertionError(reconciled)
        cls.normalized = reconciled["data"]["normalized_natal"]
        cls.payload = {
            "normalized_natal": cls.normalized,
            "subject_id": "subj_7f3a2c91d4e8",
            "subject_display_name": "Amy",
            "subject_short_id": "7F3A2C",
            "filename_label": "Amy",
            "generated_at": "2026-08-26T10:00:00+08:00",
            "last_modified_by": "ai",
        }

    def export(self, **extra):
        payload = dict(self.payload)
        payload.update(extra)
        return dispatch("export_case_markdown", payload)

    def test_astralium_external_view_materializes_optional_03_1_and_04_1_files(self):
        result = self.export(external_subject_display_name="Amy")
        self.assertTrue(result["ok"], result)
        files = result["data"]["files"]
        bazi_name = "Amy_7F3A2C_03-1_Astralium八字資料包.md"
        ziwei_name = "Amy_7F3A2C_04-1_Astralium紫微資料包.md"
        self.assertIn(bazi_name, files)
        self.assertIn(ziwei_name, files)
        self.assertIn("source_classification: External natal reference", files[bazi_name])
        self.assertIn("source_classification: External natal reference", files[ziwei_name])
        self.assertIn("# Amy｜Astralium八字資料包", files[bazi_name])
        self.assertIn("# Amy｜Astralium紫微資料包", files[ziwei_name])
        self.assertIn("甲子", files[bazi_name])

    def test_case_only_difference_is_normalized_to_canonical_subject_display_name(self):
        result = self.export(external_subject_display_name="amy")
        self.assertTrue(result["ok"], result)
        files = result["data"]["files"]
        self.assertIn("Amy_7F3A2C_03-1_Astralium八字資料包.md", files)
        self.assertNotIn("amy_7F3A2C_03-1_Astralium八字資料包.md", files)
        self.assertIn("# Amy｜Astralium八字資料包", files["Amy_7F3A2C_03-1_Astralium八字資料包.md"])

    def test_materially_different_external_subject_name_is_rejected(self):
        result = self.export(external_subject_display_name="Allie")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "external_subject_name_mismatch")

    def test_astralium_supplements_remain_optional(self):
        project_only = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        self.assertTrue(project_only["ok"], project_only)
        payload = dict(self.payload)
        payload["normalized_natal"] = project_only["data"]["normalized_natal"]
        result = dispatch("export_case_markdown", payload)
        self.assertTrue(result["ok"], result)
        names = set(result["data"]["files"])
        self.assertNotIn("Amy_7F3A2C_03-1_Astralium八字資料包.md", names)
        self.assertNotIn("Amy_7F3A2C_04-1_Astralium紫微資料包.md", names)


if __name__ == "__main__":
    unittest.main()
