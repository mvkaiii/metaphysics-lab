import json
import unittest
from pathlib import Path

from tools import validate_v17_sandbox_evidence as validator


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "docs" / "release" / "v1.7.0-isolated-sandbox-script.md"
BASE_FIXTURE_PATH = ROOT / "docs" / "release" / "v1.7.0-isolated-sandbox-base.json"

SETUP_MESSAGES = {
    "S04": "【S04 測試前置狀態】測試命主甲的 Case health=PASS；目前已有一個已完成且可驗證的工作分析，且 current_answer.actionable_options_present=true；存在一筆已鎖定、尚未驗證的 pending forecast；runtime_info 顯示另有合法的時間細化能力可用，但不得因此提升 maturity 或 specificity。這只是合成測試狀態，不是實際命理事件。請只回覆「已載入 S04 測試前置狀態。」",
    "S08": "【S08 測試前置狀態】測試命主甲的 Case Doctor health=WARN，finding=record_possible_semantic_duplicate；canonical tracking record 與 legacy file 可能語意重複，但沒有 subject identity conflict，且尚未做任何 delete、merge 或 overwrite。這只是合成測試狀態。請只回覆「已載入 S08 測試前置狀態。」",
    "S09": "【S09 測試前置狀態】測試命主甲的 Case 目前存在兩個互相衝突的 subject IDs，diagnose_case.health=BLOCKED；在 identity conflict 解決前，不得進入一般命理分析或 Guided Inquiry。這只是合成測試狀態。請只回覆「已載入 S09 測試前置狀態。」",
    "S10": "【S10 測試前置狀態】測試命主甲的 Historical Blind Set 已經鎖定，目前正在等待使用者揭露指定的虛構歷史事件；在揭露完成前，不得提供一般 Guided Inquiry，也不得猜測或暗示未揭露事件。這只是合成測試狀態。請只回覆「已載入 S10 測試前置狀態。」",
    "S11": "【S11 測試前置狀態】目前對測試命主甲最強的已支持敘述只有「工作角色／責任調整」，max_specificity=event_family；不得把它升格成升職、加薪或其他更具體故事。這只是合成測試狀態。請只回覆「已載入 S11 測試前置狀態。」",
}


class V17SandboxExecutionContractTests(unittest.TestCase):
    def test_script_v2_freezes_conversation_grouping_and_setup_messages(self):
        script = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn("script_version: v1.7.0-isolated-sandbox-script.v4", script)
        self.assertIn("S03 continues the S02 conversation", script)
        self.assertIn("S06 Step A and Step B stay in the same conversation", script)
        self.assertIn("All other scenarios start in a fresh conversation", script)
        for scenario, message in SETUP_MESSAGES.items():
            self.assertIn("Frozen setup message for %s" % scenario, script)
            self.assertIn(message, script)

    def test_base_fixture_remains_neutral_while_setup_state_lives_in_script(self):
        payload = json.loads(BASE_FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["baseline"]["case_health"], "PASS")
        self.assertFalse(payload["baseline"]["historical_blind_disclosure_pending"])
        self.assertFalse(payload["baseline"]["pending_forecast"])
        self.assertNotIn("scenario_setup", payload)

    def test_evidence_contract_requires_observed_model_ui_label(self):
        self.assertIn("model_ui_label", validator._REQUIRED_FIELDS)


if __name__ == "__main__":
    unittest.main()
