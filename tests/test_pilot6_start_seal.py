import hashlib,json
from pathlib import Path
import unittest
from engine.distribution.manifest import capability_manifest_digest
from tools.validate_prospective_pilot_decision import pilot_start_allowed,validate_decision_receipt
from tools.validate_pilot6_pre_candidate_gate import candidate_case_processing_allowed,validate_pilot6_pre_candidate_gate
from tools.pilot4_structural_snapshot_enumerator import STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE,STRUCTURAL_SNAPSHOT_ENUMERATION_RULE
from tools.pilot3_yearly_claim_universe import MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE,MULTI_SEGMENT_YEARLY_UNIVERSE_RULE
from tools.pilot5_segment_aware_downstream_authority import SEGMENT_AWARE_WINDOW_AUTHORITY_PROFILE,SEGMENT_AWARE_WINDOW_AUTHORITY_RULE,PREDICTION_BRIDGE_RULE
from tools.pilot6_canonical_snapshot_manifest_gate import CANONICAL_PRE_EFA_MANIFEST_GATE_PROFILE,CANONICAL_PRE_EFA_MANIFEST_GATE_RULE
ROOT=Path(__file__).resolve().parents[1]
SEAL=ROOT/"docs/research/pilot6-start-seal.v1.json";RECEIPT=ROOT/"docs/research/pilot6-decision-receipt.template.json";GATE=ROOT/"docs/research/pilot6-pre-candidate-gate.template.json";PROTOCOL=ROOT/"docs/research/pilot6-protocol.md";WINDOW=ROOT/"docs/research/pilot6-window-policy.v1.json";ENUM=ROOT/"docs/research/pilot6-enumeration-decision.v1.json";MANIFEST=ROOT/"docs/research/pilot6-manifest-decision.v1.json";AGG=ROOT/"docs/research/pilot6-aggregation-decision.v1.json";AUTH=ROOT/"docs/research/pilot6-downstream-authority-decision.v1.json"
class Pilot6StartSealTests(unittest.TestCase):
 def setUp(self):
  self.seal=json.loads(SEAL.read_text(encoding="utf-8"));self.receipt=json.loads(RECEIPT.read_text(encoding="utf-8"));self.gate=json.loads(GATE.read_text(encoding="utf-8"))
 def test_exact_candidate_package_run_and_artifact_bound(self):
  f=self.seal["frozen_candidate"];self.assertEqual(f["candidate_commit"],"6cb37e8b6f1ef1c9638008e9a7757ec757d20161");self.assertEqual(f["hosted_validation_run_id"],36522750345);self.assertEqual(f["hosted_artifact_id"],11013319082);self.assertEqual(f["package_sha256"],"cb175e2d482fe9ca8e2d46d6c55c4b0237f1cbb9a631e0d3c50aef75f8e1e0c4")
 def test_capability_manifest_recomputes(self):
  self.assertEqual(capability_manifest_digest(),"d11a63ec5194fb49939f4b02583a8bddf7bcfb0e9e7bbd9f547af1047837e7b0");self.assertEqual(capability_manifest_digest(),self.seal["frozen_candidate"]["capability_manifest_sha256"])
 def test_protocol_window_and_decision_digests_recompute(self):
  f=self.seal["frozen_candidate"];self.assertEqual(hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),"a048f5e9e54ce95534bfb84b64250b0937962c0d8c9bda6c587608019b3a0450");self.assertEqual(hashlib.sha256(WINDOW.read_bytes()).hexdigest(),"179d011ab3cbb5c5e75cb10eff79cf4ca75b01eadcf84da090f211d93bed99fc");self.assertEqual(hashlib.sha256(ENUM.read_bytes()).hexdigest(),"fada410e701df5277e0367d6a2a364bc29ae7e75483cb1c62b93cd44121b0ecc");self.assertEqual(hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),"049c3a52db2541ca6f3ca18fa5602222c24c04b20c384881af6701249faaa0ff");self.assertEqual(hashlib.sha256(AGG.read_bytes()).hexdigest(),"1f0a2466b64fbfd1efbf136e4207d5c9d3ddbf40a28f2f27e533d14e28d6523c");self.assertEqual(hashlib.sha256(AUTH.read_bytes()).hexdigest(),"2fc6e043608795721737ff771c98e4313986678d4c0b003da3d39c579763a3e4")
 def test_frozen_rule_identities_are_bound(self):
  f=self.seal["frozen_candidate"];self.assertEqual(f["enumeration_profile"],STRUCTURAL_SNAPSHOT_ENUMERATION_PROFILE);self.assertEqual(f["enumeration_rule"],STRUCTURAL_SNAPSHOT_ENUMERATION_RULE);self.assertEqual(f["manifest_gate_profile"],CANONICAL_PRE_EFA_MANIFEST_GATE_PROFILE);self.assertEqual(f["manifest_gate_rule"],CANONICAL_PRE_EFA_MANIFEST_GATE_RULE);self.assertEqual(f["aggregation_profile"],MULTI_SEGMENT_YEARLY_UNIVERSE_PROFILE);self.assertEqual(f["aggregation_rule"],MULTI_SEGMENT_YEARLY_UNIVERSE_RULE);self.assertEqual(f["downstream_authority_profile"],SEGMENT_AWARE_WINDOW_AUTHORITY_PROFILE);self.assertEqual(f["downstream_authority_rule"],SEGMENT_AWARE_WINDOW_AUTHORITY_RULE);self.assertEqual(f["prediction_bridge_rule"],PREDICTION_BRIDGE_RULE)
 def test_start_receipt_authorized(self):
  self.assertEqual(validate_decision_receipt(self.receipt),[]);self.assertTrue(pilot_start_allowed(self.receipt));self.assertEqual(self.receipt["pilot_status"],"AUTHORIZED_NOT_STARTED");self.assertEqual(self.receipt["pilot_start_authorization"]["authorized_at"],"2026-09-29T14:21:43+08:00")
 def test_pcg_blocked_immediately_after_start(self):
  self.assertEqual(validate_pilot6_pre_candidate_gate(self.gate),[]);self.assertEqual(self.gate["gate_status"],"BLOCKED");self.assertFalse(candidate_case_processing_allowed(self.gate));self.assertTrue(all(self.gate["prerequisites"][k] for k in ("protocol_decisions_approved","enum01_approved","manifest01_approved","agg01_approved","auth01_approved","start_authorization_bound")));self.assertFalse(any(self.gate["prerequisites"][k] for k in ("source_census_frozen","intake_registry_valid","intake_eligible_for_s1","s1_source_manifest_frozen","s1_candidate_exposure_unexposed","s1_manifest_predates_candidate_processing")))
 def test_no_real_execution_fabricated(self):
  s=self.seal["execution_state"];self.assertEqual(s["source_census"],"NOT_FROZEN");self.assertEqual(s["candidate_processing"],"NOT_STARTED");self.assertEqual(s["manifest01_receipt"],"NOT_CREATED");self.assertEqual(s["prediction_lock"],"NOT_CREATED")
if __name__=="__main__": unittest.main()
