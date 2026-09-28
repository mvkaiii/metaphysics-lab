import json
from pathlib import Path
import unittest
from tools.validate_prospective_pilot_decision import pilot_start_allowed,validate_decision_receipt
ROOT=Path(__file__).resolve().parents[1];RECEIPT=ROOT/"docs/research/pilot4-decision-receipt.template.json";WINDOW=ROOT/"docs/research/pilot4-window-policy.v1.json"
class Pilot4ApprovalStateTests(unittest.TestCase):
 def test_decisions_and_start_authorized_with_separate_timestamps(self):
  r=json.loads(RECEIPT.read_text(encoding="utf-8"));w=json.loads(WINDOW.read_text(encoding="utf-8"));self.assertEqual(validate_decision_receipt(r),[]);self.assertEqual(r["protocol_decision_status"],"ALL_ITEMS_APPROVED");self.assertEqual(r["pilot_status"],"AUTHORIZED_NOT_STARTED");self.assertTrue(pilot_start_allowed(r));self.assertEqual({x["approved_at"] for x in r["decisions"]},{"2026-09-28T21:41:06+08:00"});self.assertEqual(r["pilot_start_authorization"]["authorized_at"],"2026-09-28T22:02:42+08:00");self.assertEqual(w["status"],"APPROVED_START_AUTHORIZED");self.assertTrue(w["start_authorized"]);self.assertEqual(w["start_authorized_at"],"2026-09-28T22:02:42+08:00");self.assertFalse(w["promotion_allowed"])
if __name__=="__main__":unittest.main()
