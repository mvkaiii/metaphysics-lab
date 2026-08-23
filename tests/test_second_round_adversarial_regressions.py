import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from engine.distribution.runtime import dispatch
from tests.test_distribution_partial_case import ENVELOPE, IDENTITY
from tests.test_postmerge_audit_regressions import _CREATED_AT, _apply_changed, _subject_aware_base5


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "dist" / "ai" / "metaphysics_lab.py"


def _partial_export(envelope):
    return dispatch("export_case_markdown", {
        "candidate_envelope": envelope,
        **IDENTITY,
        "generated_at": _CREATED_AT,
        "last_modified_by": "test",
    })


def _replace_candidate_id(envelope, index, new_id):
    old_id = envelope["candidates"][index]["candidate_id"]
    envelope["candidates"][index]["candidate_id"] = new_id
    hour_map = envelope["variant_bazi_facts"]["pillars"]["hour"]
    hour_map[new_id] = hour_map.pop(old_id)
    ming_map = envelope["variant_ziwei_facts"]["ming_palace"]
    ming_map[new_id] = ming_map.pop(old_id)


def _record_update(files, record_id, *, summary="event"):
    return dispatch("update_case_record", {
        "case_files": files,
        "filename": "05_驗證事件紀錄.md",
        "operation": "append",
        "updated_at": _CREATED_AT,
        "last_modified_by": "test",
        "entry": {"record_id": record_id, "status": "verified", "summary": summary},
    })


def _bundled_request(action, payload):
    request = json.dumps({"action": action, "payload": payload}, ensure_ascii=False)
    completed = subprocess.run(
        [sys.executable, str(BUNDLE), "request", "--input", "-"],
        cwd=str(ROOT), input=request, text=True, capture_output=True,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stdout + completed.stderr)
    return json.loads(completed.stdout)


class SecondRoundAdversarialRegressionTests(unittest.TestCase):
    def test_known_facts_birth_place_nested_mapping_is_rejected(self):
        tampered = copy.deepcopy(ENVELOPE)
        tampered["known_facts"]["birth_place"] = {"label": "Taipei", "hour_pillar": "FORGED"}
        result = _partial_export(tampered)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_known_text_facts_reject_mapping_or_list_values(self):
        cases = (
            ("sex", {"value": "male"}),
            ("birth_date", ["1984-03-13"]),
            ("resolved_place_label", {"label": "Taipei City, Taiwan"}),
            ("timezone", ["Asia/Taipei"]),
        )
        for field, value in cases:
            with self.subTest(field=field):
                tampered = copy.deepcopy(ENVELOPE)
                tampered["known_facts"][field] = value
                result = _partial_export(tampered)
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_invalid_reported_birth_time_range_text_is_rejected(self):
        tampered = copy.deepcopy(ENVELOPE)
        tampered["natal_precision_state"] = "bounded"
        tampered["known_facts"]["reported_birth_time_range"] = ["09:00", "25:00"]
        result = _partial_export(tampered)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_mandatory_blocked_scope_cannot_also_be_allowed(self):
        tampered = copy.deepcopy(ENVELOPE)
        tampered["allowed_analysis"].append("unique_birth_time_claim")
        result = _partial_export(tampered)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_allowed_and_blocked_scopes_reject_empty_or_nontext_entries(self):
        cases = (
            ("allowed_analysis", ["invariant_natal_structure", ""]),
            ("allowed_analysis", ["invariant_natal_structure", 7]),
            ("blocked_analysis", list(ENVELOPE["blocked_analysis"]) + [""]),
        )
        for field, value in cases:
            with self.subTest(field=field, value=value[-1]):
                tampered = copy.deepcopy(ENVELOPE)
                tampered[field] = value
                result = _partial_export(tampered)
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_candidate_id_with_surrounding_whitespace_is_rejected(self):
        tampered = copy.deepcopy(ENVELOPE)
        _replace_candidate_id(tampered, 1, " candidate-01 ")
        result = _partial_export(tampered)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_candidate_id_with_newline_control_or_internal_space_is_rejected(self):
        for candidate_id in ("candidate-02\ninjected", "candidate-02\x01", "candidate 02"):
            with self.subTest(candidate_id=repr(candidate_id)):
                tampered = copy.deepcopy(ENVELOPE)
                _replace_candidate_id(tampered, 1, candidate_id)
                result = _partial_export(tampered)
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_candidate_count_bool_is_rejected_even_for_one_candidate(self):
        tampered = copy.deepcopy(ENVELOPE)
        only = copy.deepcopy(tampered["candidates"][0])
        tampered["candidates"] = [only]
        tampered["candidate_count"] = True
        tampered["invariant_bazi_facts"] = copy.deepcopy(only["bazi"])
        tampered["variant_bazi_facts"] = {}
        tampered["invariant_ziwei_facts"] = copy.deepcopy(only["ziwei"])
        tampered["variant_ziwei_facts"] = {}
        result = _partial_export(tampered)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_record_id_with_surrounding_whitespace_is_rejected(self):
        files = _subject_aware_base5("subj_7f3a2c91d4e8", "7F3A2C")
        result = _record_update(files, " evt-001 ")
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_case_payload")

    def test_record_id_with_single_or_double_newline_is_rejected(self):
        for record_id in ("evt-001\ninjected", "evt-001\n\n### injected"):
            with self.subTest(record_id=repr(record_id)):
                files = _subject_aware_base5("subj_7f3a2c91d4e8", "7F3A2C")
                result = _record_update(files, record_id)
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["error"]["code"], "invalid_case_payload")

    def test_record_id_with_control_character_is_rejected(self):
        files = _subject_aware_base5("subj_7f3a2c91d4e8", "7F3A2C")
        result = _record_update(files, "evt-001\x01")
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_case_payload")

    def test_legal_record_same_payload_retry_remains_noop(self):
        files = _subject_aware_base5("subj_7f3a2c91d4e8", "7F3A2C")
        first = _record_update(files, "evt-001")
        self.assertTrue(first["ok"], first)
        updated = _apply_changed(files, first)
        second = dispatch("update_case_record", {
            "case_files": updated,
            "filename": "05_驗證事件紀錄.md",
            "operation": "append",
            "updated_at": "2026-08-23T18:01:00+08:00",
            "last_modified_by": "test",
            "entry": {"record_id": "evt-001", "status": "verified", "summary": "event"},
        })
        self.assertTrue(second["ok"], second)
        self.assertEqual(second["data"]["changed_files"], {})

    def test_generated_bundle_matches_modular_nested_known_fact_rejection(self):
        tampered = copy.deepcopy(ENVELOPE)
        tampered["known_facts"]["birth_place"] = {"label": "Taipei", "hour_pillar": "FORGED"}
        payload = {
            "candidate_envelope": tampered,
            **IDENTITY,
            "generated_at": _CREATED_AT,
            "last_modified_by": "test",
        }
        modular = dispatch("export_case_markdown", payload)
        bundled = _bundled_request("export_case_markdown", payload)
        self.assertEqual(bundled, modular)
        self.assertFalse(modular["ok"], modular)
        self.assertEqual(modular["error"]["code"], "invalid_candidate_envelope")


if __name__ == "__main__":
    unittest.main()
