import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools" / "build_ziwei_month_boundary_qualification.py"
REPORT = ROOT / "qualification" / "ziwei" / "month_boundary" / "public-lunar-python-1.4.8.json"
README = ROOT / "qualification" / "ziwei" / "month_boundary" / "README.md"


class ZiweiMonthBoundaryQualificationTests(unittest.TestCase):
    def test_reproducible_month_boundary_qualification_deliverables_exist(self):
        self.assertTrue(BUILDER.is_file(), "missing reproducible Ziwei month-boundary qualification builder")
        self.assertTrue(REPORT.is_file(), "missing committed Ziwei month-boundary qualification evidence")
        self.assertTrue(README.is_file(), "missing Ziwei month-boundary qualification scope document")


if __name__ == "__main__":
    unittest.main()
