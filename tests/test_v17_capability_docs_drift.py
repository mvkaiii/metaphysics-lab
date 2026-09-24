from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CapabilityDocumentationDriftTests(unittest.TestCase):
    def _read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_readme_points_current_capability_truth_to_runtime_info(self):
        readme = self._read("README.md")
        self.assertIn("`runtime_info`", readme)
        self.assertIn("技術權威來源", readme)

    def test_ai_workflow_declares_runtime_manifest_execution_truth(self):
        workflow = self._read("core/AI工作流程.md")
        self.assertIn("以當次 runtime manifest 為執行真相", workflow)
        self.assertIn("不得以記憶、舊對話或固定 Markdown 猜測目前 runtime capability 狀態", workflow)

    def test_version_keeps_v1_selector_and_interpretation_as_defaults(self):
        version = self._read("VERSION.md")
        self.assertIn("Historical Activation Selector 正式 default 仍是 v1", version)
        self.assertIn("Interpretation Contract 正式 default 仍是 v1", version)
        self.assertNotRegex(version, re.compile(r"Selector[^\n]*v2[^\n]*正式 default"))
        self.assertNotRegex(version, re.compile(r"Interpretation[^\n]*v2[^\n]*正式 default"))

    def test_version_does_not_promote_ziwei_daily_or_hourly_palaces_to_stable(self):
        version = self._read("VERSION.md")
        for capability_id in ("ziwei.flow_day_palaces", "ziwei.flow_hour_palaces"):
            rows = [line for line in version.splitlines() if capability_id in line]
            self.assertTrue(rows, capability_id)
            for row in rows:
                self.assertNotRegex(row.lower(), r"\|\s*stable\s*\|")
                self.assertIn("experimental", row.lower())


if __name__ == "__main__":
    unittest.main()
