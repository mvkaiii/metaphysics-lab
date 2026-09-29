import hashlib,json
from pathlib import Path
import unittest
from engine.distribution.manifest import capability_manifest_digest
from tools.validate_prospective_pilot_decision import pilot_start_allowed,validate_decision_receipt
from tools.validate_pilot5_pre_candidate_gate import candidate_case_processing_allowed,validate_pilot5_pre_candidate_gate
from tools.pilot5_segment_aware_downstream_authority import SEGMENT_AWARE_WINDOW_AUTHORITY_PROFILE,SEGMENT_AWARE_WINDOW_AUTHORITY_RULE,PREDICTION_BRIDGE_RULE
ROOT=Path(__file__).resolve().parents[1]
SEAL=ROOT/"docs/research/pilot5-start-seal.v1.json";RECEIPT=ROOT/"docs/research/pilot5-decision-receipt.template.json";GATE=ROOT/"docs/research/pilot5-pre-candidate-gate.template.json";PROTOCOL=ROOT/"docs/research/pilot5-protocol.md";WINDOW=ROOT/"docs/research/pilot5-window-policy.v1.json";ENUM=ROOT/"docs/research/pilot5-enumeration-decision.v1.json";AGG=ROOT/"docs/research/pilot5-aggregation-decision.v1.json";AUTH=ROOT/"docs/research/pilot5-downstream-authority-decision.v1.json"
class Pilot5StartSealTests(unittest.TestCase):
 def setUp(self):
  self.seal=json.loads(SEAL.read_text(encoding="utf-8"));self.receipt=json.loads(RECEIPT.read_text(encoding="utf-8"));self.gate=json.loads(GATE.read_text(encoding="utf-8"))
 def test_exact_candidate_package_run_and_artifact_bound(self):
  f=self.seal["frozen_candidate"];self.assertEqual(f["candidate_commit"],"fe6975f0dc223a27a1e885f50c9f111ee24d68d4");self.assertEqual(f["hosted_validation_run_id"],36518507992);self.assertEqual(f["hosted_artifact_id"],11011902436);self.assertEqual(f["package_sha256"],"cb175e2d482fe9ca8e2d46d6c55c4b0237f1cbb9a631e0d3c50aef75f8e1e0c4")
 def test_capability_manifest_recomputes(self):
  self.assertEqual(capability_manifest_digest(),"d11a63ec5194fb49939f4b02583a8bddf7bcfb0e9e7bbd9f547af1047837e7b0");self.assertEqual(capability_manifest_digest(),self.seal["frozen_candidate"]["capability_manifest_sha256"])
 def test_protocol_window_and_decision_digests_recompute(self):
  f=self.seal["frozen_candidate"];self.assertEqual(hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),"9e3ba5604cf5d10efb7dc0c85a411100d847a6ca3d631bf96c307da4fea631f2");self.assertEqual(hashlib.sha256(WINDOW.read_bytes()).hexdigest(),"8db18934706ebea7554207eb98177ffe99214a235cdb2d0b15ceb3360ea87847");self.assertEqual(hashlib.sha256(ENUM.read_bytes()).hexdigest(),"356be2be3fad9e2d87d88f71372f365a4573219a9e56c81dc1f26e4c67bed6e6");self.assertEqual(hashlib.sha256(AGG.read_bytes()).hexdigest(),"07b9e8eac94a0bcebb3bca0ecdbbf36a88badc00f25e48f90b0f08be8bccf5e0");self.assertEqual(hashlib.sha256(AUTH.read_bytes()).hexdigest(),"1c3e42d00c4c2b86149457364d3e2280679d8a4a683d92349926b8a2d9c8423c")
 def test_auth01_identity_is_bound(self):
  f=self.seal["frozen_candidate"];self.assertEqual(f["downstream_authority_profile"],SEGMENT_AWARE_WINDOW_AUTHORITY_PROFILE);self.assertEqual(f["downstream_authority_rule"],SEGMENT_AWARE_WINDOW_AUTHORITY_RULE);self.assertEqual(f["prediction_bridge_rule"],PREDICTION_BRIDGE_RULE)
 def test_start_receipt_authorized(self):
  self.assertEqual(validate_decision_receipt(self.receipt),[]);self.assertTrue(pilot_start_allowed(self.receipt));self.assertEqual(self.receipt["pilot_status"],"AUTHORIZED_NOT_STARTED")
 def test_pcg_blocked_immediately_after_start(self):
  self.assertEqual(validate_pilot5_pre_candidate_gate(self.gate),[]);self.assertEqual(self.gate["gate_status"],"BLOCKED");self.assertFalse(candidate_case_processing_allowed(self.gate));self.assertTrue(all(self.gate["prerequisites"][k] for k in ("protocol_decisions_approved","enum01_approved","agg01_approved","auth01_approved","start_authorization_bound")));self.assertFalse(any(self.gate["prerequisites"][k] for k in ("source_census_frozen","intake_registry_valid","intake_eligible_for_s1","s1_source_manifest_frozen","s1_candidate_exposure_unexposed","s1_manifest_predates_candidate_processing")))
 def test_no_real_execution_fabricated(self):
  s=self.seal["execution_state"];self.assertEqual(s["source_census"],"NOT_FROZEN");self.assertEqual(s["candidate_processing"],"NOT_STARTED");self.assertEqual(s["segment_aware_window_authority"],"NOT_CREATED");self.assertEqual(s["prediction_lock"],"NOT_CREATED")
if __name__=="__main__":unittest.main()
