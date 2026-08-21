import json
import unittest
from pathlib import Path

PATH = Path('qualification/ziwei/phase2b/private-astralium-summary.json')


class ZiweiPhase2BPrivateQualificationTests(unittest.TestCase):
    def test_private_fine_cycle_state_is_explicit_pending(self):
        payload = json.loads(PATH.read_text(encoding='utf-8'))
        self.assertEqual(payload['source_name'], 'Astralium')
        self.assertEqual(payload['phase'], '2B')
        self.assertEqual(payload['scope'], 'fine_cycle_stems_transformations_flying')
        self.assertEqual(payload['status'], 'PENDING')
        self.assertEqual(payload['reason_code'], 'fine_cycle_source_not_available')
        self.assertFalse(payload['raw_private_payload_committed'])

    def test_private_summary_contains_no_raw_chart_payload(self):
        raw = PATH.read_text(encoding='utf-8')
        for forbidden in ('star_locations', 'palace_stems', 'expected_edges', 'birth_datetime', '出生年月', '姓名'):
            self.assertNotIn(forbidden, raw)
        payload = json.loads(raw)
        self.assertEqual(set(payload), {
            'source_name', 'phase', 'scope', 'status', 'reason_code',
            'reason', 'raw_private_payload_committed'
        })


if __name__ == '__main__':
    unittest.main()
