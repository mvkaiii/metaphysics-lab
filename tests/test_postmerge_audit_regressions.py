import copy
import unittest

from engine.distribution.calibration import lock_blind_forecast
from engine.distribution.case_pack import (
    BASE_CASE_FILES,
    CASE_FILES,
    _manifest_expected_line,
    _metadata,
    _render_case_file,
    canonical_case_filename,
)
from engine.distribution.runtime import dispatch
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


def _partial_export(envelope: dict) -> dict:
    payload = {
        "candidate_envelope": envelope,
        **IDENTITY,
        "generated_at": _CREATED_AT,
        "last_modified_by": "test",
    }
    return dispatch("export_case_markdown", payload)


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


if __name__ == "__main__":
    unittest.main()
