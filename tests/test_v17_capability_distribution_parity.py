import json
import subprocess
import sys
import unittest
from pathlib import Path

from engine.distribution.runtime import dispatch


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "dist" / "ai" / "metaphysics_lab.py"


class CapabilityDistributionParityTests(unittest.TestCase):
    def test_committed_distribution_is_current_after_manifest_changes(self):
        completed = subprocess.run(
            [sys.executable, "tools/build_ai_distribution.py", "--check"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_runtime_info_manifest_fields_match_modular_runtime(self):
        modular = dispatch("runtime_info", {})
        completed = subprocess.run(
            [sys.executable, str(BUNDLE), "runtime-info"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        bundled = json.loads(completed.stdout)
        self.assertTrue(modular["ok"], modular)
        self.assertTrue(bundled["ok"], bundled)
        for key in ("capability_manifest_version", "capabilities"):
            self.assertEqual(bundled["data"][key], modular["data"][key], key)


if __name__ == "__main__":
    unittest.main()
