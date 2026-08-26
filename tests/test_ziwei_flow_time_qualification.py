import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ZiweiFlowTimeQualificationTests(unittest.TestCase):
    def test_reproducible_public_qualification_deliverables_exist(self):
        builder = ROOT / "tools" / "build_ziwei_flow_time_qualification.py"
        report = ROOT / "qualification" / "ziwei" / "flow_time" / "public-lunar-python-1.4.8.json"
        self.assertTrue(builder.is_file(), "missing reproducible Ziwei flow-time qualification builder")
        self.assertTrue(report.is_file(), "missing committed Ziwei flow-time qualification evidence")


if __name__ == "__main__":
    unittest.main()
