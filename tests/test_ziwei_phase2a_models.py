import unittest
from dataclasses import FrozenInstanceError

from engine.ziwei.errors import ZiweiPhase2AError
from engine.ziwei.models import ChartIdentity, GeometricRelation, Transformation, TransformationType


class ZiweiPhase2AModelTests(unittest.TestCase):
    def test_error_exposes_stable_code_and_details(self):
        err = ZiweiPhase2AError("invalid_palace", "bad palace", {"palace": "X"})
        self.assertEqual(err.code, "invalid_palace")
        self.assertEqual(err.details, {"palace": "X"})

    def test_transformation_values_are_stable(self):
        self.assertEqual([item.value for item in TransformationType], ["祿", "權", "科", "忌"])

    def test_transformation_is_immutable(self):
        item = Transformation(TransformationType.LU, "廉貞", 0)
        with self.assertRaises(FrozenInstanceError):
            item.star = "破軍"

    def test_geometric_relation_is_neutral(self):
        self.assertEqual(
            {item.value for item in GeometricRelation},
            {"same_palace", "opposite_palace_incoming", "normal"},
        )

    def test_chart_identity_is_opaque(self):
        chart = ChartIdentity("chart-fixture-A", "natal", "synthetic-v1")
        self.assertEqual(chart.chart_id, "chart-fixture-A")


if __name__ == "__main__":
    unittest.main()
