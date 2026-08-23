import copy
import unittest
from unittest import mock

from engine.distribution.runtime import dispatch
from engine.natal.candidates import classify_candidate_facts
from tests.test_distribution_partial_case import ENVELOPE, IDENTITY


LOCATION = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "user-confirmed",
    "provider_reference": None,
}

BIRTH = {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time": "19:20",
    "birth_place": "台北市",
}


class ThirdRoundPartialCaseTests(unittest.TestCase):
    def export(self, envelope, **extra):
        payload = {
            "candidate_envelope": envelope,
            "resolved_location": LOCATION,
            **IDENTITY,
            "generated_at": "2026-08-23T00:00:00+08:00",
            "last_modified_by": "ai",
        }
        payload.update(extra)
        return dispatch("export_case_markdown", payload)

    @staticmethod
    def _minimal_envelope(candidates):
        envelope = copy.deepcopy(ENVELOPE)
        envelope["candidate_count"] = len(candidates)
        envelope["candidates"] = candidates
        envelope.update(classify_candidate_facts(candidates))
        return envelope

    def test_partial_case_rejects_json_type_confusion_in_bazi_invariant(self):
        candidates = [
            {"candidate_id": "candidate-01", "bazi": {"_attack": 1}, "ziwei": {}},
            {"candidate_id": "candidate-02", "bazi": {"_attack": 1}, "ziwei": {}},
        ]
        envelope = self._minimal_envelope(candidates)
        envelope["invariant_bazi_facts"]["_attack"] = True
        result = self.export(envelope)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_partial_case_rejects_json_type_confusion_in_nested_ziwei_invariant(self):
        candidates = [
            {"candidate_id": "candidate-01", "bazi": {}, "ziwei": {"nested": {"_attack": 1}}},
            {"candidate_id": "candidate-02", "bazi": {}, "ziwei": {"nested": {"_attack": 1}}},
        ]
        envelope = self._minimal_envelope(candidates)
        envelope["invariant_ziwei_facts"]["nested"]["_attack"] = True
        result = self.export(envelope)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_unknown_time_single_arbitrary_candidate_is_not_accepted_as_builder_authority(self):
        arbitrary = self._minimal_envelope([
            {
                "candidate_id": "candidate-01",
                "reported_time_start": "00:00",
                "reported_time_end": "23:59",
                "bazi": {"forged": "single-chart"},
                "ziwei": {"forged": "single-chart"},
            }
        ])
        canonical = copy.deepcopy(ENVELOPE)
        with mock.patch(
            "engine.distribution.natal.build_candidate_natal",
            return_value={"resolved_location": LOCATION, "candidate_envelope": canonical},
        ) as builder:
            result = self.export(arbitrary)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")
        builder.assert_called_once()

    def test_partial_export_requires_resolved_location_authority(self):
        payload = {
            "candidate_envelope": copy.deepcopy(ENVELOPE),
            **IDENTITY,
            "generated_at": "2026-08-23T00:00:00+08:00",
            "last_modified_by": "ai",
        }
        result = dispatch("export_case_markdown", payload)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_bounded_single_material_state_from_canonical_builder_still_exports(self):
        built = dispatch(
            "natal.candidate_envelope",
            {
                "birth": {
                    "sex": "male",
                    "birth_date": "1984-03-13",
                    "birth_time_range": ["19:20", "19:21"],
                    "birth_place": "台北市",
                },
                "resolved_location": LOCATION,
            },
        )
        self.assertTrue(built["ok"], built)
        envelope = built["data"]["candidate_envelope"]
        self.assertEqual(envelope["candidate_count"], 1)
        result = self.export(envelope)
        self.assertTrue(result["ok"], result)

    def test_known_facts_reject_control_characters_and_invalid_date(self):
        attacks = (
            ("birth_place", "Taipei\nFORGED"),
            ("timezone", "Asia/Taipei\x01"),
            ("birth_date", "not-a-date"),
        )
        for field, value in attacks:
            with self.subTest(field=field):
                envelope = copy.deepcopy(ENVELOPE)
                envelope["known_facts"][field] = value
                result = self.export(envelope)
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_known_timezone_must_match_resolved_location_authority(self):
        envelope = copy.deepcopy(ENVELOPE)
        envelope["known_facts"]["timezone"] = "Asia/Tokyo"
        result = self.export(envelope)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_blank_birth_time_is_normalized_to_null_in_candidate_envelope(self):
        fake_row = {
            "minute": 0,
            "signature": "sig",
            "bazi": {},
            "ziwei": {},
            "decadal_start": None,
            "time_basis": {},
        }
        with mock.patch("engine.natal.candidates._uncertainty_minutes", return_value=("unknown_time", range(0, 1))), mock.patch(
            "engine.natal.candidates._build_minute_candidate", return_value=fake_row
        ):
            result = dispatch(
                "natal.candidate_envelope",
                {
                    "birth": {
                        "sex": "male",
                        "birth_date": "1984-03-13",
                        "birth_time": "",
                        "birth_place": "台北市",
                    },
                    "resolved_location": LOCATION,
                },
            )
        self.assertTrue(result["ok"], result)
        self.assertIsNone(result["data"]["candidate_envelope"]["known_facts"]["reported_birth_time"])


class ThirdRoundCaseRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        built = dispatch("build_natal", {"birth": BIRTH, "resolved_location": LOCATION})
        if not built.get("ok"):
            raise AssertionError(built)
        exported = dispatch(
            "export_case_markdown",
            {
                "normalized_natal": built["data"]["normalized_natal"],
                **IDENTITY,
                "generated_at": "2026-08-23T00:00:00+08:00",
                "last_modified_by": "ai",
            },
        )
        if not exported.get("ok"):
            raise AssertionError(exported)
        cls.base_files = exported["data"]["files"]

    def append(self, files, slot, entry, when="2026-08-23T01:00:00+08:00"):
        return dispatch(
            "update_case_record",
            {
                "case_files": files,
                "filename": slot,
                "operation": "append",
                "updated_at": when,
                "last_modified_by": "ai",
                "entry": entry,
            },
        )

    def test_tracking_entry_subject_id_must_match_case_owner(self):
        samples = {
            "05_驗證事件紀錄.md": {"record_id": "cross-05", "status": "verified", "summary": "event"},
            "06_流年追蹤紀錄.md": {"record_id": "cross-06", "blind_forecast": "forecast"},
            "07_問事追蹤紀錄.md": {"record_id": "cross-07", "question": "question"},
            "08_重大決策紀錄.md": {"record_id": "cross-08", "decision": "decision"},
        }
        for slot, base_entry in samples.items():
            with self.subTest(slot=slot):
                entry = dict(base_entry)
                entry["subject_id"] = "subj_aaaaaaaaaaaa"
                result = self.append(self.base_files, slot, entry)
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["error"]["code"], "case_subject_mismatch")

    def test_tracking_entry_matching_owner_subject_is_allowed(self):
        result = self.append(
            self.base_files,
            "07_問事追蹤紀錄.md",
            {"record_id": "owner-ok", "subject_id": IDENTITY["subject_id"], "question": "question"},
        )
        self.assertTrue(result["ok"], result)

    def test_nested_related_subject_is_not_mistaken_for_record_owner(self):
        result = self.append(
            self.base_files,
            "07_問事追蹤紀錄.md",
            {
                "record_id": "related-ok",
                "subject_id": IDENTITY["subject_id"],
                "question": "relationship",
                "related_subject": {"subject_id": "subj_aaaaaaaaaaaa", "role": "counterparty"},
            },
        )
        self.assertTrue(result["ok"], result)

    def test_retry_distinguishes_json_bool_from_int(self):
        first = self.append(self.base_files, "07_問事追蹤紀錄.md", {"record_id": "evt-type-bool", "value": 1})
        self.assertTrue(first["ok"], first)
        files = dict(self.base_files)
        files.update(first["data"]["changed_files"])
        retry = self.append(files, "07_問事追蹤紀錄.md", {"record_id": "evt-type-bool", "value": True}, "2026-08-23T02:00:00+08:00")
        self.assertFalse(retry["ok"], retry)
        self.assertEqual(retry["error"]["code"], "duplicate_record_id")

    def test_retry_distinguishes_json_int_from_float(self):
        first = self.append(self.base_files, "07_問事追蹤紀錄.md", {"record_id": "evt-type-float", "value": 1})
        self.assertTrue(first["ok"], first)
        files = dict(self.base_files)
        files.update(first["data"]["changed_files"])
        retry = self.append(files, "07_問事追蹤紀錄.md", {"record_id": "evt-type-float", "value": 1.0}, "2026-08-23T02:00:00+08:00")
        self.assertFalse(retry["ok"], retry)
        self.assertEqual(retry["error"]["code"], "duplicate_record_id")

    def test_retry_still_ignores_json_key_order(self):
        first_entry = {"record_id": "evt-order", "nested": {"a": 1, "b": 2}}
        first = self.append(self.base_files, "07_問事追蹤紀錄.md", first_entry)
        self.assertTrue(first["ok"], first)
        files = dict(self.base_files)
        files.update(first["data"]["changed_files"])
        retry_entry = {"nested": {"b": 2, "a": 1}, "record_id": "evt-order"}
        retry = self.append(files, "07_問事追蹤紀錄.md", retry_entry, "2026-08-23T02:00:00+08:00")
        self.assertTrue(retry["ok"], retry)
        self.assertEqual(retry["data"]["changed_files"], {})


if __name__ == "__main__":
    unittest.main()
