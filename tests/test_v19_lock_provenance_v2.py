import copy
import unittest

from engine.distribution.prospective import METHOD_VERSION, resolve_query_anchor
from engine.distribution.runtime import dispatch
from tests.test_distribution_historical_calibration import SELECTOR_RESULT, point


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

PROFILE_ID = "lock-provenance-v2"
RULE_VERSION = "2.0-exp"
FROZEN_V15_DIGEST = "b9b465c43fe1e903601cb9b726ef0c691810a674b2c074146a1b30c7ee9d1524"


def actual(slot):
    return "Kai_7F3A2C_%s" % slot


class V19LockProvenanceV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.normalized = {}
        for label, birth_time in (("old", "19:20"), ("new", "21:20")):
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

    def export(self, which="old", contract="1.3"):
        result = dispatch(
            "export_case_markdown",
            {
                "normalized_natal": self.normalized[which],
                **IDENTITY,
                "generated_at": "2026-10-02T14:00:00+08:00",
                "last_modified_by": "test",
                "project_contract_version": contract,
            },
        )
        self.assertTrue(result["ok"], result)
        return result["data"]

    @staticmethod
    def source_files(case_data):
        files = case_data["files"]
        return {actual(slot): files[actual(slot)] for slot in BASE_SLOTS}

    @staticmethod
    def source_names():
        return [actual(slot) for slot in BASE_SLOTS]

    @staticmethod
    def anchor():
        result = dispatch(
            "resolve_query_anchor",
            {
                "query_anchor_at": "2026-10-02T14:10:00+08:00",
                "query_timezone": "Asia/Taipei",
                "target_start": "2026-11-01T00:00:00+08:00",
                "target_end": "2026-12-31T23:59:59+08:00",
                "question_reference": "synthetic-lock-provenance-v2",
            },
        )
        if not result.get("ok"):
            raise AssertionError(result)
        return result["data"]

    @classmethod
    def claim(cls):
        anchor = cls.anchor()
        return {
            "claim_id": "C1",
            "priority": "primary",
            "forecast_window": {
                "start": "2026-11-01T00:00:00+08:00",
                "end": "2026-11-30T23:59:59+08:00",
            },
            "primary_domain": "career",
            "event_family": "role_change",
            "prediction": "synthetic bounded event-family forecast",
            "matched_if": "formal responsibility or role changes inside the window",
            "partial_if": "responsibility changes materially without formal title change",
            "not_matched_if": "no material responsibility or role change occurs inside the window",
            "evidence_layers": ["bazi"],
            "evidence_time_scales": ["yearly", "monthly"],
            "capability_maturity": "experimental",
            "confidence": "medium",
            "knowledge_cutoff_at": anchor["knowledge_cutoff_at"],
            "evaluation_eligibility": "clean_scorable",
            "contamination_state": "clean_prospective",
            "method_version": METHOD_VERSION,
        }

    def prospective_v2(self, case_data):
        return dispatch(
            "lock_prospective_forecast",
            {
                "anchor": self.anchor(),
                "claims": [self.claim()],
                "case_provenance": {
                    "subject_id": IDENTITY["subject_id"],
                    "source_files_used": list(reversed(self.source_names())),
                    "source_case_files": self.source_files(case_data),
                },
            },
        )

    def blind_lock(self, case_data):
        return dispatch(
            "lock_blind_forecast",
            {
                "blind_forecast_id": "bf-v19-lock-provenance",
                "subject_id": IDENTITY["subject_id"],
                "question_type": "flow-year",
                "question_reference": "2027-work",
                "locked_at": "2026-10-02T14:15:00+08:00",
                "source_files_used": list(reversed(self.source_names())),
                "source_case_files": self.source_files(case_data),
                "blind_forecast_payload": {"summary": "synthetic blind forecast"},
            },
        )

    def test_prospective_v2_binds_revision_digest_sources_and_method(self):
        case_data = self.export("old", "1.3")
        result = self.prospective_v2(case_data)
        self.assertTrue(result["ok"], result)
        data = result["data"]

        self.assertEqual(data["method_version"], METHOD_VERSION)
        provenance = data["lock_provenance"]
        self.assertEqual(provenance["profile_id"], PROFILE_ID)
        self.assertEqual(provenance["rule_version"], RULE_VERSION)
        self.assertEqual(provenance["subject_id"], IDENTITY["subject_id"])
        self.assertEqual(provenance["natal_revision_id"], case_data["natal_revision_id"])
        self.assertEqual(provenance["base_case_digest"], case_data["base_case_digest"])
        self.assertEqual(provenance["source_slots_used"], list(BASE_SLOTS))
        self.assertEqual(provenance["source_files_used"], self.source_names())

        digest = dispatch("case.base_digest", {"case_files": self.source_files(case_data)})
        self.assertTrue(digest["ok"], digest)
        self.assertEqual(provenance["base_case_digest"], digest["data"]["base_case_digest"])

    def test_same_forecast_on_new_natal_revision_produces_new_lock_without_rewriting_old(self):
        old_case = self.export("old", "1.3")
        first = self.prospective_v2(old_case)
        self.assertTrue(first["ok"], first)
        frozen_first = copy.deepcopy(first)

        replacement = dispatch(
            "case.replace_natal_base",
            {
                "case_files": old_case["files"],
                "normalized_natal": self.normalized["new"],
                "updated_at": "2026-10-02T15:00:00+08:00",
                "last_modified_by": "test",
                "correction_class": "birth_basis_change",
                "correction_reason": "synthetic revision change",
            },
        )
        self.assertTrue(replacement["ok"], replacement)
        new_case = {
            "files": replacement["data"]["case_files"],
            "natal_revision_id": replacement["data"]["natal_revision_id"],
            "base_case_digest": replacement["data"]["base_case_digest"],
        }

        second = self.prospective_v2(new_case)
        self.assertTrue(second["ok"], second)
        self.assertEqual(first, frozen_first)
        self.assertNotEqual(
            first["data"]["lock_provenance"]["natal_revision_id"],
            second["data"]["lock_provenance"]["natal_revision_id"],
        )
        self.assertNotEqual(
            first["data"]["lock_provenance"]["base_case_digest"],
            second["data"]["lock_provenance"]["base_case_digest"],
        )
        self.assertNotEqual(first["data"]["canonical_digest"], second["data"]["canonical_digest"])

    def test_prospective_v2_requires_revision_bound_project_contract_1_3(self):
        legacy = self.export("old", "1.2")
        result = self.prospective_v2(legacy)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "lock_provenance_requires_revision_bound_case")

    def test_prospective_v2_rejects_mixed_revision_source_files(self):
        old = self.export("old", "1.3")
        new = self.export("new", "1.3")
        mixed = self.source_files(old)
        mixed[actual("00_專案索引.md")] = self.source_files(new)[actual("00_專案索引.md")]
        result = dispatch(
            "lock_prospective_forecast",
            {
                "anchor": self.anchor(),
                "claims": [self.claim()],
                "case_provenance": {
                    "subject_id": IDENTITY["subject_id"],
                    "source_files_used": self.source_names(),
                    "source_case_files": mixed,
                },
            },
        )
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "case_natal_revision_mismatch")

    def test_legacy_prospective_lock_stays_unbound(self):
        result = dispatch(
            "lock_prospective_forecast",
            {"anchor": self.anchor(), "claims": [self.claim()]},
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["data"]["method_version"], METHOD_VERSION)
        self.assertNotIn("lock_provenance", result["data"])

    def historical_calibration_lock(self, case_data):
        return dispatch(
            "lock_historical_calibration",
            {
                "calibration_id": "HC-v19-lock-provenance",
                "subject_id": IDENTITY["subject_id"],
                "selector_result": SELECTOR_RESULT,
                "canonical_test_points": [
                    point(2016),
                    point(2018),
                    point(2020),
                    point(2023),
                    point(2019, "control"),
                ],
                "supplemental_blind_points": [],
                "locked_at": "2026-10-02T14:20:00+08:00",
                "case_files": case_data["files"],
                "updated_at": "2026-10-02T14:20:00+08:00",
                "last_modified_by": "test",
            },
        )

    def test_historical_calibration_blind_lock_on_1_3_binds_revision_provenance(self):
        case_data = self.export("old", "1.3")
        result = self.historical_calibration_lock(case_data)
        self.assertTrue(result["ok"], result)
        locked = result["data"]["locked_payload"]
        provenance = locked["lock_provenance"]
        self.assertEqual(provenance["profile_id"], PROFILE_ID)
        self.assertEqual(provenance["rule_version"], RULE_VERSION)
        self.assertEqual(provenance["subject_id"], IDENTITY["subject_id"])
        self.assertEqual(provenance["natal_revision_id"], case_data["natal_revision_id"])
        self.assertEqual(provenance["base_case_digest"], case_data["base_case_digest"])
        self.assertEqual(provenance["source_slots_used"], list(BASE_SLOTS))
        self.assertEqual(provenance["source_files_used"], self.source_names())
        self.assertEqual(provenance["method_version"], SELECTOR_RESULT["rule_version"])

    def test_historical_calibration_legacy_1_2_lock_is_not_backfilled(self):
        legacy = self.export("old", "1.2")
        result = self.historical_calibration_lock(legacy)
        self.assertTrue(result["ok"], result)
        self.assertNotIn("lock_provenance", result["data"]["locked_payload"])

    def test_historical_stage1_blind_lock_on_1_3_uses_same_revision_binding(self):
        case_data = self.export("old", "1.3")
        result = self.blind_lock(case_data)
        self.assertTrue(result["ok"], result)
        locked = result["data"]["locked_payload"]
        self.assertEqual(locked["method_version"], METHOD_VERSION)
        provenance = locked["lock_provenance"]
        self.assertEqual(provenance["profile_id"], PROFILE_ID)
        self.assertEqual(provenance["rule_version"], RULE_VERSION)
        self.assertEqual(provenance["subject_id"], IDENTITY["subject_id"])
        self.assertEqual(provenance["natal_revision_id"], case_data["natal_revision_id"])
        self.assertEqual(provenance["base_case_digest"], case_data["base_case_digest"])
        self.assertEqual(provenance["source_slots_used"], list(BASE_SLOTS))
        self.assertEqual(provenance["source_files_used"], self.source_names())

    def test_historical_stage1_legacy_1_2_lock_is_not_rewritten_as_v2(self):
        legacy = self.export("old", "1.2")
        result = self.blind_lock(legacy)
        self.assertTrue(result["ok"], result)
        locked = result["data"]["locked_payload"]
        self.assertNotIn("lock_provenance", locked)
        self.assertNotIn("method_version", locked)

    def test_historical_stage1_new_revision_changes_provenance_not_old_lock(self):
        old_case = self.export("old", "1.3")
        first = self.blind_lock(old_case)
        self.assertTrue(first["ok"], first)
        frozen_first = copy.deepcopy(first)

        replacement = dispatch(
            "case.replace_natal_base",
            {
                "case_files": old_case["files"],
                "normalized_natal": self.normalized["new"],
                "updated_at": "2026-10-02T15:30:00+08:00",
                "last_modified_by": "test",
                "correction_class": "birth_basis_change",
                "correction_reason": "synthetic second lock revision",
            },
        )
        self.assertTrue(replacement["ok"], replacement)
        new_case = {
            "files": replacement["data"]["case_files"],
            "natal_revision_id": replacement["data"]["natal_revision_id"],
            "base_case_digest": replacement["data"]["base_case_digest"],
        }
        second = self.blind_lock(new_case)
        self.assertTrue(second["ok"], second)

        self.assertEqual(first, frozen_first)
        self.assertNotEqual(
            first["data"]["locked_payload"]["lock_provenance"]["natal_revision_id"],
            second["data"]["locked_payload"]["lock_provenance"]["natal_revision_id"],
        )
        self.assertNotEqual(first["data"]["payload_digest"], second["data"]["payload_digest"])


if __name__ == "__main__":
    unittest.main()
