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

TRACKING_SLOTS = (
    "05_驗證事件紀錄.md",
    "06_流年追蹤紀錄.md",
    "07_問事追蹤紀錄.md",
    "08_重大決策紀錄.md",
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

    def export_full(self, which="old", contract=None):
        payload = {
            "normalized_natal": self.normalized[which],
            **IDENTITY,
            "generated_at": "2026-10-02T10:00:00+08:00",
            "last_modified_by": "test",
        }
        if contract is not None:
            payload["project_contract_version"] = contract
        result = dispatch("export_case_markdown", payload)
        self.assertTrue(result["ok"], result)
        return result["data"]

    def append_tracking(self, files):
        merged = dict(files)
        samples = {
            "05_驗證事件紀錄.md": {
                "record_id": "evt-revision-001",
                "status": "verified",
                "summary": "synthetic verified event",
            },
            "06_流年追蹤紀錄.md": {
                "record_id": "prospective-lock-revision-001",
                "immutable": True,
                "prospective_forecast_lock": {
                    "method_version": "lin_tianji_v1.5-exp",
                    "payload_digest": "frozen-prospective-digest",
                },
            },
            "07_問事追蹤紀錄.md": {
                "record_id": "historical-lock-revision-001",
                "immutable": True,
                "historical_calibration_lock": {
                    "selector_profile_id": "historical-activation-bazi-v1",
                    "payload_digest": "frozen-historical-digest",
                },
            },
            "08_重大決策紀錄.md": {
                "record_id": "decision-revision-001",
                "decision": "synthetic decision",
            },
        }
        for index, slot in enumerate(TRACKING_SLOTS, start=1):
            updated = dispatch(
                "update_case_record",
                {
                    "case_files": merged,
                    "filename": slot,
                    "operation": "append",
                    "updated_at": "2026-10-02T10:%02d:00+08:00" % index,
                    "last_modified_by": "test",
                    "entry": samples[slot],
                },
            )
            self.assertTrue(updated["ok"], updated)
            merged.update(updated["data"]["changed_files"])
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
        exported = self.export_full(contract="1.3")
        self.assertEqual(exported["project_contract_version"], "1.3")
        revision = exported["natal_revision_id"]
        self.assertTrue(revision.startswith("nrev_"))
        self.assertTrue(exported["base_case_digest"].startswith("bcase_"))

        for slot in BASE_SLOTS:
            metadata, _ = parse_front_matter(exported["files"][actual(slot)])
            self.assertEqual(metadata["case_schema_version"], "1.1")
            self.assertEqual(metadata["project_contract_version"], "1.3")
            self.assertEqual(metadata["subject_id"], IDENTITY["subject_id"])
            self.assertEqual(metadata["natal_revision_profile"], "natal-revision-v1")
            self.assertEqual(metadata["natal_revision_id"], revision)

        validated = dispatch("validate_case", {"case_files": exported["files"]})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(validated["data"]["project_contract_version"], "1.3")
        self.assertEqual(validated["data"]["natal_revision_id"], revision)
        self.assertEqual(validated["data"]["base_case_digest"], exported["base_case_digest"])

    def test_contract_1_3_candidate_envelope_v2_persistence_is_revision_bound(self):
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
        self.assertEqual(data["project_contract_version"], "1.3")
        self.assertTrue(data["natal_revision_id"].startswith("nrev_"))
        validated = dispatch("validate_case", {"case_files": data["files"]})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(validated["data"]["natal_revision_id"], data["natal_revision_id"])

    def test_mixed_revision_case_is_rejected_even_when_subject_matches(self):
        old = self.export_full("old", contract="1.3")
        new = self.export_full("new", contract="1.3")
        mixed = dict(new["files"])
        mixed[actual("00_專案索引.md")] = old["files"][actual("00_專案索引.md")]
        result = dispatch("validate_case", {"case_files": mixed})
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "case_natal_revision_mismatch")

    def test_base_digest_is_deterministic_and_binds_exact_00_04_bytes(self):
        exported = self.export_full(contract="1.3")
        first = dispatch("case.base_digest", {"case_files": exported["files"]})
        second = dispatch("case.base_digest", {"case_files": exported["files"]})
        self.assertTrue(first["ok"], first)
        self.assertEqual(first, second)
        self.assertEqual(first["data"]["base_case_digest"], exported["base_case_digest"])

        tampered = dict(exported["files"])
        target = actual("01_命盤核心摘要.md")
        tampered[target] = tampered[target] + "\n"
        changed = dispatch("case.base_digest", {"case_files": tampered})
        self.assertTrue(changed["ok"], changed)
        self.assertNotEqual(
            changed["data"]["base_case_digest"],
            first["data"]["base_case_digest"],
        )

        with_tracking = self.append_tracking(exported["files"])
        tracked_digest = dispatch("case.base_digest", {"case_files": with_tracking})
        self.assertTrue(tracked_digest["ok"], tracked_digest)
        # First materialization of 05-08 updates 00's manifest. Since the digest
        # binds exact 00-04 bytes, that manifest change must change the digest.
        self.assertNotEqual(
            tracked_digest["data"]["base_case_digest"],
            first["data"]["base_case_digest"],
        )

        # Once the slot is already materialized, a pure append to 05 changes no
        # 00-04 byte and therefore must not change the Base Case digest.
        second_event = dispatch(
            "update_case_record",
            {
                "case_files": with_tracking,
                "filename": "05_驗證事件紀錄.md",
                "operation": "append",
                "updated_at": "2026-10-02T10:30:00+08:00",
                "last_modified_by": "test",
                "entry": {
                    "record_id": "evt-revision-002",
                    "status": "verified",
                    "summary": "second synthetic verified event",
                },
            },
        )
        self.assertTrue(second_event["ok"], second_event)
        after_append = dict(with_tracking)
        after_append.update(second_event["data"]["changed_files"])
        after_append_digest = dispatch("case.base_digest", {"case_files": after_append})
        self.assertTrue(after_append_digest["ok"], after_append_digest)
        self.assertEqual(
            after_append_digest["data"]["base_case_digest"],
            tracked_digest["data"]["base_case_digest"],
        )

    def test_safe_replacement_upgrades_legacy_1_2_and_preserves_05_08_exact_bytes(self):
        legacy = self.export_full("old", contract="1.2")
        self.assertEqual(legacy["project_contract_version"], "1.2")
        files = self.append_tracking(legacy["files"])
        tracking_before = {actual(slot): files[actual(slot)] for slot in TRACKING_SLOTS}

        replaced = self.replace(files, "new")
        self.assertTrue(replaced["ok"], replaced)
        data = replaced["data"]
        self.assertEqual(data["status"], "replacement_ready")
        self.assertEqual(data["project_contract_version"], "1.3")
        self.assertEqual(data["previous_revision_authority"], "legacy_unbound")
        self.assertIsNone(data["previous_natal_revision_id"])
        self.assertNotEqual(data["previous_base_case_digest"], data["base_case_digest"])
        self.assertEqual(set(data["preserved_tracking_files"]), set(tracking_before))

        for filename, before in tracking_before.items():
            self.assertEqual(data["case_files"][filename], before, filename)

        self.assertIn("Historical Calibration: `uncalibrated`", data["case_files"][actual("00_專案索引.md")])
        self.assertIn("Natal Revision Lineage", data["case_files"][actual("02_命盤資料校驗紀錄.md")])
        self.assertEqual(data["revision_lineage"][-1]["previous_revision_authority"], "legacy_unbound")
        self.assertEqual(data["validation"]["status"], "compatible")

    def test_replaced_1_3_base_remains_appendable_with_preserved_1_2_tracking(self):
        legacy = self.append_tracking(self.export_full("old", contract="1.2")["files"])
        replaced = self.replace(legacy, "new")
        self.assertTrue(replaced["ok"], replaced)

        before_digest = dispatch(
            "case.base_digest",
            {"case_files": replaced["data"]["case_files"]},
        )
        self.assertTrue(before_digest["ok"], before_digest)

        appended = dispatch(
            "update_case_record",
            {
                "case_files": replaced["data"]["case_files"],
                "filename": "05_驗證事件紀錄.md",
                "operation": "append",
                "updated_at": "2026-10-02T12:30:00+08:00",
                "last_modified_by": "test",
                "entry": {
                    "record_id": "evt-revision-post-upgrade-001",
                    "status": "verified",
                    "summary": "post-upgrade synthetic verified event",
                },
            },
        )
        self.assertTrue(appended["ok"], appended)

        merged = dict(replaced["data"]["case_files"])
        merged.update(appended["data"]["changed_files"])
        validated = dispatch("validate_case", {"case_files": merged})
        self.assertTrue(validated["ok"], validated)
        self.assertEqual(validated["data"]["project_contract_version"], "1.3")

        after_digest = dispatch("case.base_digest", {"case_files": merged})
        self.assertTrue(after_digest["ok"], after_digest)
        self.assertEqual(
            after_digest["data"]["base_case_digest"],
            before_digest["data"]["base_case_digest"],
        )

    def test_second_material_revision_accumulates_lineage_and_same_revision_is_idempotent(self):
        files = self.append_tracking(self.export_full("old", contract="1.3")["files"])
        first = self.replace(files, "new")
        self.assertTrue(first["ok"], first)
        tracking_after_first = {
            actual(slot): first["data"]["case_files"][actual(slot)]
            for slot in TRACKING_SLOTS
        }

        same = self.replace(
            first["data"]["case_files"],
            "new",
            updated_at="2026-10-02T12:00:00+08:00",
        )
        self.assertTrue(same["ok"], same)
        self.assertEqual(same["data"]["status"], "no_change")
        self.assertEqual(same["data"]["changed_files"], {})

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
        for filename, before in tracking_after_first.items():
            self.assertEqual(second["data"]["case_files"][filename], before, filename)

    def test_legacy_contract_1_1_and_1_2_remain_readable_without_forced_migration(self):
        current = self.export_full("old", contract="1.2")
        self.assertEqual(current["project_contract_version"], "1.2")
        self.assertNotIn("natal_revision_id", current)
        validated_12 = dispatch("validate_case", {"case_files": current["files"]})
        self.assertTrue(validated_12["ok"], validated_12)
        self.assertEqual(validated_12["data"]["project_contract_version"], "1.2")
        self.assertNotIn("natal_revision_id", validated_12["data"])

        legacy_11 = {
            name: text.replace("project_contract_version: 1.2", "project_contract_version: 1.1", 1)
            for name, text in current["files"].items()
        }
        validated_11 = dispatch("validate_case", {"case_files": legacy_11})
        self.assertTrue(validated_11["ok"], validated_11)
        self.assertEqual(validated_11["data"]["project_contract_version"], "1.1")

    def test_contract_1_3_manifest_still_matches_materialized_slots(self):
        exported = self.export_full(contract="1.3")
        files = dict(exported["files"])
        index = actual("00_專案索引.md")
        files[index] = files[index].replace("- ○ 05 ", "- ✓ 05 ", 1)
        result = dispatch("validate_case", {"case_files": files})
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "case_manifest_mismatch")


if __name__ == "__main__":
    unittest.main()
