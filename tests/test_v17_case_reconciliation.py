import unittest

from engine.distribution.case_doctor import diagnose_case, plan_case_reconciliation
from engine.distribution.errors import DistributionError
from engine.distribution.runtime import dispatch


BIRTH = {
    "sex": "female",
    "birth_date": "1991-02-03",
    "birth_time": "08:45",
    "birth_place": "台中市",
}
LOCATION = {
    "canonical_name": "Taichung City, Taiwan",
    "latitude": 24.1477,
    "longitude": 120.6736,
    "timezone": "Asia/Taipei",
    "provider_name": "synthetic_fixture",
    "provider_version": "1",
    "provider_reference": None,
}
SUBJECT = {
    "subject_id": "subj_b1c2d3e4f5a6",
    "subject_display_name": "Blair",
    "subject_short_id": "B1C2D3",
    "filename_label": "Blair",
}
ALLOWLISTED_ACTIONS = {
    "ignore_exact_duplicate",
    "import_missing_record_via_update_case_record",
    "migrate_formal_legacy_case",
    "request_subject_resolution",
    "request_semantic_duplicate_resolution",
    "retain_unrelated_file",
}


class CaseReconciliationPlannerTests(unittest.TestCase):
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
                "generated_at": "2026-09-08T13:00:00+08:00",
                "last_modified_by": "fixture",
            },
        )
        if not exported.get("ok"):
            raise AssertionError(exported)
        cls.base_files = dict(exported["data"]["files"])

    @staticmethod
    def _append_verified(files, entry, when):
        result = dispatch(
            "update_case_record",
            {
                "case_files": files,
                "filename": "05_驗證事件紀錄.md",
                "operation": "append",
                "updated_at": when,
                "last_modified_by": "fixture",
                "entry": entry,
            },
        )
        if not result.get("ok"):
            raise AssertionError(result)
        updated = dict(files)
        updated.update(result["data"]["changed_files"])
        return updated

    @staticmethod
    def _doctor_payload(files):
        return {
            "project_files": files,
            "subject_context": {
                "subject_id": SUBJECT["subject_id"],
                "subject_short_id": SUBJECT["subject_short_id"],
                "subject_display_name": SUBJECT["subject_display_name"],
            },
        }

    def _diagnostic(self, files):
        return diagnose_case(self._doctor_payload(files))

    def _missing_record_files(self):
        shared = {
            "record_id": "evt-shared-2024",
            "status": "verified",
            "year": 2024,
            "category": "work",
            "summary": "Fictional shared event.",
        }
        canonical = self._append_verified(
            dict(self.base_files), shared, "2026-09-08T13:10:00+08:00"
        )
        legacy = self._append_verified(
            dict(self.base_files), shared, "2026-09-08T13:10:00+08:00"
        )
        legacy = self._append_verified(
            legacy,
            {
                "record_id": "evt-missing-2026",
                "status": "verified",
                "year": 2026,
                "category": "finance",
                "summary": "Fictional legacy-only event.",
            },
            "2026-09-08T13:20:00+08:00",
        )
        tracking = next(name for name in legacy if name.endswith("05_驗證事件紀錄.md"))
        canonical["驗證事件紀錄.md"] = legacy[tracking]
        return canonical

    def _semantic_conflict_files(self):
        canonical = self._append_verified(
            dict(self.base_files),
            {
                "record_id": "evt-canonical-2025",
                "status": "verified",
                "year": 2025,
                "category": "work",
                "summary": "Fictional responsibility expansion.",
            },
            "2026-09-08T13:10:00+08:00",
        )
        tracking = next(name for name in canonical if name.endswith("05_驗證事件紀錄.md"))
        legacy = canonical[tracking]
        legacy = legacy.replace("evt-canonical-2025", "evt-legacy-2025")
        legacy = legacy.replace(
            "Fictional responsibility expansion.",
            "Fictional cross-team ownership change.",
        )
        canonical["驗證事件紀錄.md"] = legacy
        return canonical

    def _blocked_files(self):
        files = dict(self.base_files)
        target = next(name for name in files if name.endswith("04_紫微基礎資料包.md"))
        files[target] = files[target].replace(
            "subject_id: subj_b1c2d3e4f5a6",
            "subject_id: subj_deadbeefcafe",
            1,
        )
        return files

    def test_tampered_diagnostic_is_rejected(self):
        files = dict(self.base_files)
        diagnostic = self._diagnostic(files)
        tampered = dict(diagnostic)
        tampered["health"] = "WARN"
        with self.assertRaises(DistributionError) as caught:
            plan_case_reconciliation(
                {"project_files": files, "diagnostic": tampered}
            )
        self.assertEqual(caught.exception.code, "case_diagnostic_mismatch")

    def test_clean_case_returns_deterministic_no_change(self):
        files = dict(self.base_files)
        diagnostic = self._diagnostic(files)
        result = plan_case_reconciliation(
            {"project_files": files, "diagnostic": diagnostic}
        )
        self.assertEqual(result["status"], "no_change")
        self.assertEqual(result["actions"], [])
        self.assertFalse(result["requires_user_confirmation"])
        self.assertEqual(result["do_not_delete_yet"], [])
        self.assertEqual(len(result["plan_digest"]), 64)

    def test_missing_legacy_record_proposes_update_case_record_without_deletion(self):
        files = self._missing_record_files()
        diagnostic = self._diagnostic(files)
        result = plan_case_reconciliation(
            {"project_files": files, "diagnostic": diagnostic}
        )
        action_types = {action["type"] for action in result["actions"]}
        self.assertEqual(result["status"], "safe_plan")
        self.assertTrue(result["requires_user_confirmation"])
        self.assertTrue(action_types.issubset(ALLOWLISTED_ACTIONS))
        self.assertIn("import_missing_record_via_update_case_record", action_types)
        self.assertIn("ignore_exact_duplicate", action_types)
        self.assertIn("驗證事件紀錄.md", result["do_not_delete_yet"])
        imports = [
            action
            for action in result["actions"]
            if action["type"] == "import_missing_record_via_update_case_record"
        ]
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0]["target_slot"], "05_驗證事件紀錄.md")
        self.assertEqual(imports[0]["record"]["record_id"], "evt-missing-2026")
        self.assertNotIn("delete", action_types)

    def test_semantic_duplicate_becomes_user_choice_not_import(self):
        files = self._semantic_conflict_files()
        diagnostic = self._diagnostic(files)
        result = plan_case_reconciliation(
            {"project_files": files, "diagnostic": diagnostic}
        )
        action_types = {action["type"] for action in result["actions"]}
        self.assertEqual(result["status"], "safe_plan")
        self.assertIn("request_semantic_duplicate_resolution", action_types)
        self.assertNotIn("import_missing_record_via_update_case_record", action_types)
        self.assertEqual(len(result["conflicts_requiring_user_choice"]), 1)
        self.assertEqual(
            result["conflicts_requiring_user_choice"][0]["code"],
            "record_possible_semantic_duplicate",
        )

    def test_blocked_diagnostic_returns_blocked_plan(self):
        files = self._blocked_files()
        diagnostic = self._diagnostic(files)
        result = plan_case_reconciliation(
            {"project_files": files, "diagnostic": diagnostic}
        )
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["requires_user_confirmation"])
        self.assertIn(
            "request_subject_resolution",
            {action["type"] for action in result["actions"]},
        )

    def test_planner_is_deterministic_under_project_file_order_permutation(self):
        files = self._missing_record_files()
        diagnostic = self._diagnostic(files)
        first = plan_case_reconciliation(
            {"project_files": files, "diagnostic": diagnostic}
        )
        reversed_files = dict(reversed(list(files.items())))
        second = plan_case_reconciliation(
            {"project_files": reversed_files, "diagnostic": diagnostic}
        )
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
