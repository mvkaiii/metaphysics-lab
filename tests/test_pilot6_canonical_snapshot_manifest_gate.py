import copy
import unittest
from tools.pilot4_structural_snapshot_enumerator import enumerate_structural_snapshot_segments,build_snapshot_manifest_from_enumeration
from tools.pilot6_canonical_snapshot_manifest_gate import build_canonical_pre_efa_manifest_gate,READY_STATUS
POLICY="1"*64
def periods():
 return [{"start_datetime":"2025-06-01T00:00:00+08:00","end_datetime":"2035-06-01T00:00:00+08:00"}]
class Pilot6CanonicalSnapshotManifestGateTests(unittest.TestCase):
 def setUp(self):
  self.e=enumerate_structural_snapshot_segments(window_start="2027-09-01T00:00:00+08:00",window_end="2027-10-31T23:59:59+08:00",timezone_name="Asia/Taipei",window_policy_digest=POLICY,bazi_decadal_periods=periods())
  self.d=[("%064x"%(i+1)) for i in range(self.e["segment_count"])]
  self.m=build_snapshot_manifest_from_enumeration(enumeration=self.e,structural_state_digests=self.d)
 def gate(self,manifest=None,started=False):
  return build_canonical_pre_efa_manifest_gate(enumeration=self.e,structural_state_digests=self.d,supplied_snapshot_manifest=self.m if manifest is None else manifest,efa_execution_started=started)
 def test_canonical_helper_output_is_ready_for_efa(self):
  r=self.gate();self.assertEqual(r["status"],READY_STATUS);self.assertEqual(r["snapshot_manifest_digest"],self.m["snapshot_manifest_digest"]);self.assertFalse(r["efa_execution_started"]);self.assertFalse(r["retrospective_repair_allowed"]);self.assertFalse(r["manual_override_allowed"]);self.assertFalse(r["promotion_allowed"])
 def test_missing_extra_or_wrong_digest_fails_closed(self):
  x=copy.deepcopy(self.m);x.pop("profile_version")
  with self.assertRaises(ValueError): self.gate(x)
  x=copy.deepcopy(self.m);x["unexpected"]=1
  with self.assertRaises(ValueError): self.gate(x)
  x=copy.deepcopy(self.m);x["snapshot_manifest_digest"]="0"*64
  with self.assertRaises(ValueError): self.gate(x)
 def test_snapshot_order_or_structural_digest_change_fails(self):
  x=copy.deepcopy(self.m);x["snapshots"]=list(reversed(x["snapshots"]))
  with self.assertRaises(ValueError): self.gate(x)
  x=copy.deepcopy(self.m);x["snapshots"][0]["structural_state_digest"]="f"*64
  with self.assertRaises(ValueError): self.gate(x)
 def test_efa_already_started_permanently_blocks_gate(self):
  with self.assertRaisesRegex(ValueError,"before any EFA"): self.gate(started=True)
 def test_claim_or_outcome_injection_fails(self):
  x=copy.deepcopy(self.m);x["claim_id"]="forbidden"
  with self.assertRaises(ValueError): self.gate(x)
if __name__=="__main__":unittest.main()
