import unittest

from engine.distribution.runtime import dispatch


BIRTH = {
    "sex": "male",
    "birth_date": "1992-07-21",
    "birth_time": "14:10",
    "birth_place": "高雄市",
}
LOCATION = {
    "canonical_name": "Kaohsiung City, Taiwan",
    "latitude": 22.6273,
    "longitude": 120.3014,
    "timezone": "Asia/Taipei",
    "provider_name": "synthetic_fixture",
    "provider_version": "1",
    "provider_reference": None,
}
SUBJECT = {
    "subject_id": "subj_c1d2e3f4a5b6",
    "subject_display_name": "Casey",
    "subject_short_id": "C1D2E3",
    "filename_label": "Casey",
}


class CaseDoctorRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        if not built.get("ok"):
            raise AssertionError(built)
        exported = dispatch(
            "export_case_markdown",
            {
                "normalized_natal": built["data"]["normalized_natal"],
                **SUBJECT,
                "generated_at": "2026-09-08T14:00:00+08:00",
                "last_modified_by": "fixture",
            },
        )
        if not exported.get("ok"):
            raise AssertionError(exported)
        cls.files = dict(exported["data"]["files"])
        cls.doctor_payload = {
            "project_files": cls.files,
            "subject_context": {
                "subject_id": SUBJECT["subject_id"],
                "subject_short_id": SUBJECT["subject_short_id"],
                "subject_display_name": SUBJECT["subject_display_name"],
            },
        }

    def test_diagnose_case_dispatches_successfully(self):
        result = dispatch("diagnose_case", self.doctor_payload)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["action"], "diagnose_case")
        self.assertEqual(result["data"]["health"], "PASS")

    def test_planner_dispatches_successfully(self):
        diagnostic = dispatch("diagnose_case", self.doctor_payload)
        self.assertTrue(diagnostic["ok"], diagnostic)
        result = dispatch(
            "plan_case_reconciliation",
            {
                "project_files": self.files,
                "diagnostic": diagnostic["data"],
            },
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["action"], "plan_case_reconciliation")
        self.assertEqual(result["data"]["status"], "no_change")

    def test_planner_malformed_diagnostic_returns_structured_error(self):
        result = dispatch(
            "plan_case_reconciliation",
            {"project_files": self.files, "diagnostic": {"health": "PASS"}},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["action"], "plan_case_reconciliation")
        self.assertEqual(result["error"]["code"], "case_diagnostic_mismatch")
        self.assertIsInstance(result["error"]["details"], dict)

    def test_runtime_info_advertises_both_case_doctor_actions(self):
        result = dispatch("runtime_info")
        self.assertTrue(result["ok"], result)
        actions = result["data"]["supported_actions"]
        self.assertIn("diagnose_case", actions)
        self.assertIn("plan_case_reconciliation", actions)


if __name__ == "__main__":
    unittest.main()
