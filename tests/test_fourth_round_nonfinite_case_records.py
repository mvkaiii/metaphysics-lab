import copy
import unittest

from engine.distribution.runtime import dispatch
from tests.test_third_round_adversarial_regressions import ThirdRoundCaseRecordTests
from tests.test_third_round_bundle_parity import _bundled_request


class FourthRoundNonFiniteCaseRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ThirdRoundCaseRecordTests.setUpClass()
        cls.base_files = ThirdRoundCaseRecordTests.base_files

    @staticmethod
    def append(files, entry, when="2026-08-23T03:00:00+08:00"):
        return dispatch(
            "update_case_record",
            {
                "case_files": files,
                "filename": "07_問事追蹤紀錄.md",
                "operation": "append",
                "updated_at": when,
                "last_modified_by": "test",
                "entry": entry,
            },
        )

    def test_public_write_rejects_nonfinite_values_at_any_nested_position(self):
        attacks = (
            ("top_nan", {"value": float("nan")}),
            ("top_pos_inf", {"value": float("inf")}),
            ("top_neg_inf", {"value": float("-inf")}),
            ("nested_mapping_nan", {"nested": {"value": float("nan")}}),
            ("list_pos_inf", {"value": [1, float("inf"), 2]}),
            ("list_mapping_neg_inf", {"value": [{"nested": float("-inf")}]}),
        )
        for label, attack in attacks:
            with self.subTest(label=label):
                files = copy.deepcopy(self.base_files)
                entry = {"record_id": "nonfinite-" + label}
                entry.update(attack)
                result = self.append(files, entry)
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["error"]["code"], "invalid_case_payload")
                self.assertNotIn("changed_files", result.get("data", {}))
                self.assertEqual(files, self.base_files)

    def test_validate_case_rejects_persisted_nonstandard_json_constants(self):
        constants = ("NaN", "Infinity", "-Infinity")
        for index, constant in enumerate(constants, start=1):
            with self.subTest(constant=constant):
                record_id = "persisted-nonfinite-%d" % index
                first = self.append(self.base_files, {"record_id": record_id, "value": 1})
                self.assertTrue(first["ok"], first)
                files = dict(self.base_files)
                files.update(first["data"]["changed_files"])
                target = next(name for name in files if name.endswith("07_問事追蹤紀錄.md"))
                files[target] = files[target].replace('"value": 1', '"value": %s' % constant, 1)
                result = dispatch("validate_case", {"case_files": files})
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["error"]["code"], "invalid_case_markdown")

    def test_retry_distinguishes_missing_field_from_explicit_null(self):
        first = self.append(self.base_files, {"record_id": "missing-vs-null", "question": "same"})
        self.assertTrue(first["ok"], first)
        files = dict(self.base_files)
        files.update(first["data"]["changed_files"])
        retry = self.append(
            files,
            {"record_id": "missing-vs-null", "question": "same", "value": None},
            "2026-08-23T04:00:00+08:00",
        )
        self.assertFalse(retry["ok"], retry)
        self.assertEqual(retry["error"]["code"], "duplicate_record_id")

    def test_bundle_matches_modular_nonfinite_write_rejection(self):
        attacks = (float("nan"), float("inf"), float("-inf"))
        for index, value in enumerate(attacks, start=1):
            with self.subTest(index=index):
                payload = {
                    "case_files": self.base_files,
                    "filename": "07_問事追蹤紀錄.md",
                    "operation": "append",
                    "updated_at": "2026-08-23T05:00:00+08:00",
                    "last_modified_by": "test",
                    "entry": {"record_id": "bundle-nonfinite-%d" % index, "value": value},
                }
                modular = dispatch("update_case_record", payload)
                bundled = _bundled_request("update_case_record", payload)
                self.assertEqual(bundled, modular)
                self.assertFalse(modular["ok"], modular)
                self.assertEqual(modular["error"]["code"], "invalid_case_payload")


if __name__ == "__main__":
    unittest.main()
