import copy
import unittest

from engine.distribution.calibration import (
    canonical_digest,
    lock_blind_forecast,
    lock_historical_calibration,
)
from engine.distribution.case_pack import (
    BASE_CASE_FILES,
    CASE_FILES,
    _manifest_expected_line,
    _metadata,
    _render_case_file,
    canonical_case_filename,
)
from engine.distribution.runtime import dispatch
from tests.test_distribution_historical_calibration import SELECTOR_RESULT, point
from tests.test_distribution_partial_case import ENVELOPE, IDENTITY


_CREATED_AT = "2026-08-23T18:00:00+08:00"


def _subject_aware_base5(subject_id: str, short_id: str, display_name: str = "Kai") -> dict:
    identity = {
        "subject_id": subject_id,
        "subject_display_name": display_name,
        "subject_short_id": short_id,
        "filename_label": display_name,
    }
    bodies = {}
    manifest = ["# %s｜Metaphysics Lab Case｜專案索引" % display_name, "", "## Case Files", ""]
    for canonical in CASE_FILES:
        actual = canonical_case_filename(identity, canonical)
        manifest.append(_manifest_expected_line(canonical, actual, canonical in BASE_CASE_FILES))
    bodies["00_專案索引.md"] = "\n".join(manifest) + "\n"
    for canonical in BASE_CASE_FILES[1:]:
        bodies[canonical] = "# %s｜%s\n" % (display_name, canonical[3:-3])
    files = {}
    for canonical in BASE_CASE_FILES:
        actual = canonical_case_filename(identity, canonical)
        files[actual] = _render_case_file(
            canonical,
            _metadata(canonical, identity, _CREATED_AT, "test"),
            bodies[canonical],
        )
    return files


def _partial_export(envelope: dict, **identity_overrides) -> dict:
    identity = dict(IDENTITY)
    identity.update(identity_overrides)
    payload = {
        "candidate_envelope": envelope,
        **identity,
        "generated_at": _CREATED_AT,
        "last_modified_by": "test",
    }
    return dispatch("export_case_markdown", payload)


def _apply_changed(files, result):
    updated = dict(files)
    updated.update(result["data"]["changed_files"])
    return updated


def _historical_lock_payload(case_files=None):
    payload = {
        "calibration_id": "HC-authority-001",
        "subject_id": "subj_7f3a2c91d4e8",
        "selector_result": SELECTOR_RESULT,
        "canonical_test_points": [point(2016), point(2018), point(2020), point(2023), point(2019, "control")],
        "supplemental_blind_points": [],
        "locked_at": _CREATED_AT,
    }
    if case_files is not None:
        payload.update({
            "case_files": case_files,
            "updated_at": _CREATED_AT,
            "last_modified_by": "test",
        })
    return payload


class PostmergeAuditRegressionTests(unittest.TestCase):
    def test_blind_forecast_rejects_same_short_prefix_different_full_subject(self):
        source_subject = "subj_aaaaaaaaaaa1"
        payload_subject = "subj_aaaaaaaaaaa2"
        case_files = _subject_aware_base5(source_subject, "AAAAAA")
        payload = {
            "blind_forecast_id": "bf-prefix-collision",
            "subject_id": payload_subject,
            "question_type": "flow-year",
            "question_reference": "2027-work",
            "locked_at": _CREATED_AT,
            "source_files_used": list(case_files),
            "source_case_files": case_files,
            "blind_forecast_payload": {"summary": "active"},
        }
        with self.assertRaises(ValueError):
            lock_blind_forecast(payload)

    def test_partial_case_rejects_fake_certainty_in_known_facts(self):
        tampered = copy.deepcopy(ENVELOPE)
        tampered["known_facts"]["reported_birth_time"] = "12:34"
        tampered["known_facts"]["hour_pillar"] = "丙午"
        result = _partial_export(tampered)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_partial_case_rejects_duplicate_candidate_ids_even_if_variant_maps_are_forged(self):
        tampered = copy.deepcopy(ENVELOPE)
        tampered["candidates"][1]["candidate_id"] = "candidate-01"
        tampered["variant_bazi_facts"]["pillars"]["hour"] = {"candidate-01": "乙丑"}
        tampered["variant_ziwei_facts"]["ming_palace"] = {"candidate-01": "巳"}
        result = _partial_export(tampered)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_same_record_id_same_payload_retry_is_noop(self):
        files = _subject_aware_base5("subj_7f3a2c91d4e8", "7F3A2C")
        entry = {"record_id": "evt-001", "status": "verified", "summary": "same event"}
        first = dispatch("update_case_record", {
            "case_files": files,
            "filename": "05_驗證事件紀錄.md",
            "operation": "append",
            "updated_at": _CREATED_AT,
            "last_modified_by": "test",
            "entry": entry,
        })
        self.assertTrue(first["ok"], first)
        updated = _apply_changed(files, first)
        second = dispatch("update_case_record", {
            "case_files": updated,
            "filename": "05_驗證事件紀錄.md",
            "operation": "append",
            "updated_at": "2026-08-23T18:01:00+08:00",
            "last_modified_by": "test",
            "entry": entry,
        })
        self.assertTrue(second["ok"], second)
        self.assertEqual(second["data"]["changed_files"], {})

    def test_same_record_id_different_payload_is_rejected(self):
        files = _subject_aware_base5("subj_7f3a2c91d4e8", "7F3A2C")
        first = dispatch("update_case_record", {
            "case_files": files,
            "filename": "05_驗證事件紀錄.md",
            "operation": "append",
            "updated_at": _CREATED_AT,
            "last_modified_by": "test",
            "entry": {"record_id": "evt-001", "status": "verified", "summary": "first"},
        })
        self.assertTrue(first["ok"], first)
        updated = _apply_changed(files, first)
        second = dispatch("update_case_record", {
            "case_files": updated,
            "filename": "05_驗證事件紀錄.md",
            "operation": "append",
            "updated_at": "2026-08-23T18:01:00+08:00",
            "last_modified_by": "test",
            "entry": {"record_id": "evt-001", "status": "verified", "summary": "changed"},
        })
        self.assertFalse(second["ok"])
        self.assertEqual(second["error"]["code"], "duplicate_record_id")

    def test_registry_rejects_filename_label_not_derived_from_display_name(self):
        registry = """---
registry_schema_version: 1.0
---
# 命主索引

<!-- subjects:start -->
```json
{"subjects":[{"subject_id":"subj_7f3a2c91d4e8","subject_short_id":"7F3A2C","subject_display_name":"Kai","filename_label":"Other","status":"active"}]}
```
<!-- subjects:end -->
"""
        result = dispatch("subject.registry_validate", {"registry_markdown": registry})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "subject_registry_mismatch")

    def test_case_export_rejects_filename_label_not_derived_from_display_name(self):
        result = _partial_export(copy.deepcopy(ENVELOPE), filename_label="Other")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "subject_identity_mismatch")

    def test_finalize_historical_calibration_requires_case_lock_authority(self):
        locked = lock_historical_calibration(_historical_lock_payload())
        result = dispatch("finalize_historical_calibration", {
            "locked_payload": locked["locked_payload"],
            "payload_digest": locked["payload_digest"],
            "responses": [],
        })
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "lock_authority_required")

    def test_public_case_update_cannot_forge_historical_lock_authority(self):
        files = _subject_aware_base5("subj_7f3a2c91d4e8", "7F3A2C")
        forged_locked = {
            "calibration_id": "forged",
            "subject_id": "subj_7f3a2c91d4e8",
            "locked_at": _CREATED_AT,
            "canonical_test_points": [],
            "supplemental_blind_points": [],
        }
        result = dispatch("update_case_record", {
            "case_files": files,
            "filename": "07_問事追蹤紀錄.md",
            "operation": "append",
            "updated_at": _CREATED_AT,
            "last_modified_by": "caller",
            "entry": {
                "record_id": "historical-lock-forged",
                "record_type": "historical_calibration_lock",
                "subject_id": "subj_7f3a2c91d4e8",
                "locked_payload": forged_locked,
                "payload_digest": canonical_digest(forged_locked),
                "immutable": True,
            },
        })
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "immutable_case_record")

    def test_historical_lock_is_persisted_and_rehashed_tamper_is_rejected(self):
        files = _subject_aware_base5("subj_7f3a2c91d4e8", "7F3A2C")
        locked = lock_historical_calibration(_historical_lock_payload(files))
        self.assertIn("changed_files", locked)
        self.assertIn("lock_record_id", locked)
        authoritative_files = dict(files)
        authoritative_files.update(locked["changed_files"])
        tampered = copy.deepcopy(locked["locked_payload"])
        tampered["canonical_test_points"][0]["interpretation_text"] = "tampered after lock"
        result = dispatch("finalize_historical_calibration", {
            "case_files": authoritative_files,
            "lock_record_id": locked["lock_record_id"],
            "locked_payload": tampered,
            "payload_digest": canonical_digest(tampered),
            "responses": [],
        })
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "immutable_calibration_violation")


if __name__ == "__main__":
    unittest.main()
