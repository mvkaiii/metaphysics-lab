import hashlib,json
from pathlib import Path
import unittest
from engine.distribution.manifest import capability_manifest_digest
from tools.validate_prospective_pilot_decision import pilot_start_allowed,validate_decision_receipt
from tools.validate_pilot4_pre_candidate_gate import candidate_case_processing_allowed,validate_pilot4_pre_candidate_gate
from tools.pilot4_structural_snapshot_enumerator import STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE,STRUCTURAL_SNAPSHOT_ENUMERATION_RULE
from tools.pilot3_yearly_claim_universe import MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE,MULTI_SEGMENT_YEARLY_UNIVERSE_RULE
ROOT=Path(__file__).resolve().parents[1]
SEAL=ROOT/"docs/research/pilot4-start-seal.v1.json";RECEIPT=ROOT/"docs/research/pilot4-decision-receipt.template.json";GATE=ROOT/"docs/research/pilot4-pre-candidate-gate.template.json";PROTOCOL=ROOT/"docs/research/pilot4-protocol.md";WINDOW=ROOT/"docs/research/pilot4-window-policy.v1.json";ENUM=ROOT/"docs/research/pilot4-enumeration-decision.v1.json";AGG=ROOT/"docs/research/pilot4-aggregation-decision.v1.json"
class Pilot4StartSealTests(unittest.TestCase):
 def setUp(self):
  self.seal=json.loads(SEAL.read_text(encoding="utf-8"));self.receipt=json.loads(RECEIPT.read_text(encoding="utf-8"));self.gate=json.loads(GATE.read_text(encoding="utf-8"))
 def test_exact_candidate_package_run_and_artifact_bound(self):
  f=self.seal["frozen_candidate"];self.assertEqual(f["candidate_commit"],"f94318651d065a3e677993fb6044518e31c7754c");self.assertEqual(f["hosted_validation_run_id"],36430731730);self.assertEqual(f["hosted_artifact_id"],10973427099);self.assertEqual(f["package_sha256"],"cb175e2d482fe9ca8e2d46d6c55c4b0237f1cbb9a631e0d3c50aef75f8e1e0c4")
 def test_capability_manifest_recomputes(self):
  self.assertEqual(capability_manifest_digest(),"d11a63ec5194fb49939f4b02583a8bddf7bcfb0e9e7bbd9f547af1047837e7b0");self.assertEqual(capability_manifest_digest(),self.seal["frozen_candidate"]["capability_manifest_sha256"])
 def test_final_protocol_and_window_digests_recompute(self):
  self.assertEqual(hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),"9b2b5aba437a5f0d707f91194acc9a495e14b287698453cc7b74b2dff910ca02");self.assertEqual(hashlib.sha256(WINDOW.read_bytes()).hexdigest(),"175bb93452a662df969f890a38d732e7eafb5722aa35914e7d780f38c9623212")
 def test_enum01_and_agg01_digests_and_identities_bound(self):
  f=self.seal["frozen_candidate"];self.assertEqual(hashlib.sha256(ENUM.read_bytes()).hexdigest(),"f178c1babd723c26cadbee5eaebb14005592d99847a8d24b208acdb3a0ab9096");self.assertEqual(hashlib.sha256(AGG.read_bytes()).hexdigest(),"68a79e4074f737f8e2546d9ee4b3e7fe850f296e729fb98eac9dd5b0eec7512f");self.assertEqual(f["enumeration_profile"],STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE);self.assertEqual(f["enumeration_rule"],STRUCTURAL_SNAPSHOT_ENUMERATION_RULE);self.assertEqual(f["aggregation_profile"],MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE);self.assertEqual(f["aggregation_rule"],MULTI_SEGMENT_YEARLY_UNIVERSE_RULE)
 def test_start_receipt_authorized(self):
  self.assertEqual(validate_decision_receipt(self.receipt),[]);self.assertTrue(pilot_start_allowed(self.receipt));self.assertEqual(self.receipt["pilot_status"],"AUTHORIZED_NOT_STARTED")
 def test_pcg_blocked_immediately_after_start(self):
  self.assertEqual(validate_pilot4_pre_candidate_gate(self.gate),[]);self.assertEqual(self.gate["gate_status"],"BLOCKED");self.assertFalse(candidate_case_processing_allowed(self.gate));self.assertTrue(all(self.gate["prerequisites"][k] for k in ("protocol_decisions_approved","enum01_approved","agg01_approved","start_authorization_bound")));self.assertFalse(any(self.gate["prerequisites"][k] for k in ("source_census_frozen","intake_registry_valid","intake_eligible_for_s1","s1_source_manifest_frozen","s1_candidate_exposure_unexposed","s1_manifest_predates_candidate_processing")))
 def test_no_real_execution_fabricated(self):
  s=self.seal["execution_state"];self.assertEqual(s["source_census"],"NOT_FROZEN");self.assertEqual(s["candidate_processing"],"NOT_STARTED");self.assertEqual(s["structural_snapshot_enumeration"],"NOT_CREATED");self.assertEqual(s["prediction_lock"],"NOT_CREATED")
if __name__=="__main__":unittest.main()
