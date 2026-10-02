import copy
import unittest

from engine.distribution.case_pack import parse_front_matter
from engine.distribution.runtime import dispatch


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

BASE_SLOTS = (
    "00_專案索引.md",
    "01_命盤核心摘要.md",
    "02_命盤資料校驗紀錄.md",
    "03_八字結構化資料包.md",
    "04_紫微基礎資料包.md",
)


def actual(slot, label="Kai"):
    return "%s_7F3A2C_%s" % (label, slot)


class V19CaseRevisionIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.normalized = {}
        for label, birth_time in (("old", "19:20"), ("new", "21:20"), ("third", "23:20")):
            built = dispatch(
                "build_natal",
                {
                    "birth": {
                        "sex": "male",
                        "birth_date": "1984-03-13",
                        "birth_time": birth_time,
                        "birth_place": "台北市",
                    },
                    "resolved_location": LOCATION,
                },
            )
            if not built.get("ok"):
                raise AssertionError(built)
            cls.normalized[label] = built["data"]["normalized_natal"]

    def export_full(self, which="old", **extra):
        payload = {
            "normalized_natal": self.normalized[which],
            **IDENTITY,
            "generated_at": "2026-10-02T10:00:00+08:00",
            "last_modified_by": "test",
            "project_contract_version": "1.3",
        }
        payload.update(extra)
        result = dispatch("export_case_markdown", payload)
        self.assertTrue(result["ok"], result)
        return result["data"]

    def append_event(self, files, record_id="evt-revision-001"):
        result = dispatch(
            "update_case_record",
            {
                "case_files": files,
                "filename": "05_驗證事件紀錄.md",
                "operation": "append",
                "updated_at": "2026-10-02T10:05:00+08:00",
                "last_modified_by": "test",
                "entry": {
                    "record_id": record_id,
                    "status": "verified",
                    "summary": "synthetic verified event",
                },
            },
        )
        self.assertTrue(result["ok"], result)
        merged = dict(files)
        merged.update(result["data"]["changed_files"])
        return merged

    def replace(self, files, which="new", **extra):
        payload = {
            "case_files": files,
            "normalized_natal": self.normalized[which],
            "updated_at": "2026-10-02T11:00:00+08:00",
            "last_modified_by": "test",
            "correction_class": "birth_basis_change",
            "correction_reason": "synthetic birth-time correction",
        }
        payload.update(extra)
        return dispatch("case.replace_natal_base", payload)

    def test_contract_1_3_full_case_binds_one_revision_across_00_04(self):
        exported = self.export_full()
        revision = exported["natal_revision_id"]
        self.assertTrue(revision.startswith("nrev_"))
        self.assertTrue(exported["base_case_digest"].startswith("bcase_"))
        for slot in BASE_SLOTS:
            metadata, _ = parse_front_matter(exported["files"][actual(slot)])
            self.assertEqual(metadata["project_contract_version"], "1.3")
            self.assertEqual(metadata["natal_revision_profile"], "natal-revision-v1")
            self.assertEqual(metadata["natal_revision_id"], revision)

        validated = dispatch("validate_case", {"case_files": exported["files"]})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(validated["data"]["project_contract_version"], "1.3")
        self.assertEqual(validated["data"]["natal_revision_id"], revision)
        self.assertEqual(
            validated["data"]["base_case_digest"],
            exported["base_case_digest"],
        )

    def test_contract_1_3_partial_case_binds_candidate_revision(self):
        built = dispatch(
            "natal.candidate_envelope",
            {
                "birth": {
                    "sex": "male",
                    "birth_date": "1984-03-13",
                    "birth_time_precision": "bounded",
                    "birth_time_range": ["19:20", "19:21"],
                    "birth_place": "台北市",
                },
                "resolved_location": LOCATION,
            },
        )
        self.assertTrue(built["ok"], built)
        exported = dispatch(
            "export_case_markdown",
            {
                "candidate_envelope": built["data"]["candidate_envelope"],
                "resolved_location": LOCATION,
                **IDENTITY,
                "generated_at": "2026-10-02T10:00:00+08:00",
                "last_modified_by": "test",
                "project_contract_version": "1.3",
            },
        )
        self.assertTrue(exported["ok"], exported)
        data = exported["data"]
        self.assertTrue(data["natal_revision_id"].startswith("nrev_"))
        validated = dispatch("validate_case", {"case_files": data["files"]})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(
            validated["data"]["natal_revision_id"],
            data["natal_revision_id"],
        )

    def test_mixed_revision_case_is_rejected(self):
        old = self.export_full("old")
        new = self.export_full("new")
        mixed = dict(new["files"])
        mixed[actual("00_專案索引.md")] = old["files"][actual("00_專案索引.md")]
        result = dispatch("validate_case", {"case_files": mixed})
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "case_natal_revision_mismatch")

    def test_base_digest_is_deterministic_and_binds_exact_bytes(self):
        exported = self.export_full()
        first = dispatch("case.base_digest", {"case_files": exported["files"]})
        second = dispatch("case.base_digest", {"case_files": exported["files"]})
        self.assertTrue(first["ok"], first)
        self.assertEqual(first, second)
        self.assertEqual(
            first["data"]["base_case_digest"],
            exported["base_case_digest"],
        )

        tampered = dict(exported["files"])
        target = actual("01_命盤核心摘要.md")
        tampered[target] = tampered[target] + "\n"
        changed = dispatch("case.base_digest", {"case_files": tampered})
        self.assertTrue(changed["ok"], changed)
        self.assertNotEqual(
            changed["data"]["base_case_digest"],
            first["data"]["base_case_digest"],
        )

    def test_display_rename_keeps_natal_revision_but_changes_base_digest(self):
        exported = self.export_full()
        renamed = dispatch(
            "subject.rename",
            {
                "subject_id": IDENTITY["subject_id"],
                "new_subject_display_name": "Kai Chen",
                "registry_markdown": (
                    "---\nregistry_schema_version: 1.0\n---\n# 命主索引\n\n"
                    "<!-- subjects:start -->\n```json\n"
                    '{"subjects":[{"filename_label":"Kai","status":"active",'
                    '"subject_display_name":"Kai","subject_id":"subj_7f3a2c91d4e8",'
                    '"subject_short_id":"7F3A2C"}]}'
                    "\n```\n<!-- subjects:end -->\n"
                ),
                "case_files": exported["files"],
                "updated_at": "2026-10-02T10:30:00+08:00",
            },
        )
        self.assertTrue(renamed["ok"], renamed)
        files = renamed["data"]["changed_files"]
        validated = dispatch("validate_case", {"case_files": files})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(
            validated["data"]["natal_revision_id"],
            exported["natal_revision_id"],
        )
        self.assertNotEqual(
            validated["data"]["base_case_digest"],
            exported["base_case_digest"],
        )

    def test_replacement_upgrades_legacy_1_2_case_preserves_tracking_and_resets_calibration(self):
        old = dispatch(
            "export_case_markdown",
            {
                "normalized_natal": self.normalized["old"],
                **IDENTITY,
                "generated_at": "2026-10-01T09:00:00+08:00",
                "last_modified_by": "test",
            },
        )
        self.assertTrue(old["ok"], old)
        files = self.append_event(old["data"]["files"])
        tracking_before = files[actual("05_驗證事件紀錄.md")]
        _, body_before = parse_front_matter(tracking_before)

        replaced = self.replace(files)
        self.assertTrue(replaced["ok"], replaced)
        data = replaced["data"]
        self.assertEqual(data["status"], "replacement_ready")
        self.assertEqual(data["project_contract_version"], "1.3")
        self.assertIsNone(data["previous_natal_revision_id"])
        self.assertEqual(
            data["revision_lineage"][-1]["previous_revision_authority"],
            "legacy_unbound",
        )
        self.assertIn(actual("05_驗證事件紀錄.md"), data["preserved_tracking_files"])
        self.assertIn("evt-revision-001", data["case_files"][actual("05_驗證事件紀錄.md")])
        _, body_after = parse_front_matter(data["case_files"][actual("05_驗證事件紀錄.md")])
        self.assertEqual(body_after, body_before)
        self.assertIn(
            "Historical Calibration: `uncalibrated`",
            data["case_files"][actual("00_專案索引.md")],
        )
        self.assertIn(
            "Natal Revision Lineage",
            data["case_files"][actual("02_命盤資料校驗紀錄.md")],
        )
        self.assertTrue(data["validation"]["status"] == "compatible")
        self.assertNotEqual(
            data["previous_base_case_digest"],
            data["base_case_digest"],
        )

    def test_replacement_from_1_3_preserves_tracking_bytes_and_is_idempotent(self):
        files = self.append_event(self.export_full("old")["files"], "evt-stable-001")
        tracking_before = files[actual("05_驗證事件紀錄.md")]

        first = self.replace(files, "new")
        self.assertTrue(first["ok"], first)
        data = first["data"]
        self.assertEqual(
            data["case_files"][actual("05_驗證事件紀錄.md")],
            tracking_before,
        )

        second = self.replace(
            data["case_files"],
            "new",
            updated_at="2026-10-02T12:00:00+08:00",
        )
        self.assertTrue(second["ok"], second)
        self.assertEqual(second["data"]["status"], "no_change")
        self.assertEqual(second["data"]["changed_files"], {})
        self.assertEqual(
            second["data"]["natal_revision_id"],
            data["natal_revision_id"],
        )

    def test_second_material_revision_accumulates_lineage_without_rewriting_event_body(self):
        files = self.append_event(self.export_full("old")["files"], "evt-lineage-001")
        first = self.replace(files, "new")
        self.assertTrue(first["ok"], first)
        event_body = parse_front_matter(
            first["data"]["case_files"][actual("05_驗證事件紀錄.md")]
        )[1]

        second = self.replace(
            first["data"]["case_files"],
            "third",
            updated_at="2026-10-02T13:00:00+08:00",
            correction_reason="second synthetic correction",
        )
        self.assertTrue(second["ok"], second)
        self.assertEqual(len(second["data"]["revision_lineage"]), 2)
        self.assertEqual(
            second["data"]["revision_lineage"][-1]["previous_natal_revision_id"],
            first["data"]["natal_revision_id"],
        )
        self.assertEqual(
            parse_front_matter(
                second["data"]["case_files"][actual("05_驗證事件紀錄.md")]
            )[1],
            event_body,
        )

    def test_contract_1_2_remains_readable_and_default_export_unchanged(self):
        old = dispatch(
            "export_case_markdown",
            {
                "normalized_natal": self.normalized["old"],
                **IDENTITY,
                "generated_at": "2026-10-01T09:00:00+08:00",
                "last_modified_by": "test",
            },
        )
        self.assertTrue(old["ok"], old)
        self.assertEqual(old["data"]["project_contract_version"], "1.2")
        self.assertNotIn("natal_revision_id", old["data"])
        validated = dispatch("validate_case", {"case_files": old["data"]["files"]})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(validated["data"]["project_contract_version"], "1.2")
        self.assertNotIn("natal_revision_id", validated["data"])


if __name__ == "__main__":
    unittest.main()
