import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "docs" / "release" / "v1.7.0-isolated-sandbox-script.md"


class V17SandboxV4ContractTests(unittest.TestCase):
    def test_s04_precondition_explicitly_authorizes_four_runtime_suggestions(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("script_version: v1.7.0-isolated-sandbox-script.v4", text)
        s04 = text.split("### S04", 1)[1].split("### S05", 1)[0]
        self.assertIn("actionable_options_present=true", s04)
        self.assertIn("pending forecast", s04)
        self.assertIn("時間細化能力", s04)
        self.assertIn("exactly 4 non-duplicative suggestions", s04)


if __name__ == "__main__":
    unittest.main()
