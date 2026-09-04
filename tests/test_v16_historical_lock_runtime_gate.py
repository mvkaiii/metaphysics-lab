import unittest

from engine.distribution.runtime import dispatch
from tests.test_postmerge_audit_regressions import (
    _historical_lock_payload,
    _subject_aware_base5,
)


class V16HistoricalLockRuntimeGateTests(unittest.TestCase):
    def test_runtime_lock_rejects_non_persistent_historical_lock(self):
        result = dispatch("lock_historical_calibration", _historical_lock_payload())

        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "lock_authority_required")

    def test_runtime_lock_returns_persisted_authority_when_case_is_supplied(self):
        files = _subject_aware_base5("subj_7f3a2c91d4e8", "7F3A2C")
        result = dispatch(
            "lock_historical_calibration",
            _historical_lock_payload(files),
        )

        self.assertTrue(result["ok"], result)
        self.assertTrue(result["data"]["lock_record_id"])
        self.assertTrue(result["data"]["changed_files"])


if __name__ == "__main__":
    unittest.main()
