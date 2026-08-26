import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools" / "build_bazi_flow_time_qualification.py"
REPORT = ROOT / "qualification" / "bazi" / "flow_time" / "public-lunar-python-1.4.8.json"


class BaziFlowTimeQualificationTests(unittest.TestCase):
    def test_reproducible_public_qualification_deliverables_exist(self):
        self.assertTrue(BUILDER.is_file(), "missing reproducible flow-time qualification builder")
        self.assertTrue(REPORT.is_file(), "missing committed public flow-time qualification evidence")


if __name__ == "__main__":
    unittest.main()
