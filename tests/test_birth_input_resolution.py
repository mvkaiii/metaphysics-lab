import unittest

from engine.birth.input_resolution import resolve_birth_input


class BirthInputResolutionTests(unittest.TestCase):
    def test_complete_mode_a_input_resolves(self):
        result = resolve_birth_input(
            {
                "sex": "male",
                "birth_date": "1984-03-13",
                "birth_time": "19:20",
                "birth_place": "台北市",
            },
            target="ziwei_natal",
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.input.birth_place.label, "台北市")
        self.assertEqual(result.input.sex.value, "male")

    def test_missing_sex_blocks_full_natal(self):
        result = resolve_birth_input(
            {
                "birth_date": "1984-03-13",
                "birth_time": "19:20",
                "birth_place": "台北市",
            },
            target="ziwei_natal",
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.missing_fields, ("sex",))
        self.assertEqual(result.allowed_actions, ("ask", "keep_candidates", "downgrade"))

    def test_bazi_static_can_resolve_without_sex(self):
        result = resolve_birth_input(
            {
                "birth_date": "1984-03-13",
                "birth_time": "19:20",
                "birth_place": "台北市",
            },
            target="bazi_static",
        )
        self.assertTrue(result.ok)
        self.assertIsNone(result.input.sex)

    def test_time_range_is_not_collapsed_to_midpoint(self):
        result = resolve_birth_input(
            {
                "sex": "female",
                "birth_date": "1990-05-06",
                "birth_time_range": ["20:00", "22:00"],
                "birth_place": "高雄市",
            },
            target="ziwei_natal",
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "ambiguous_birth_time")
        self.assertEqual(result.allowed_actions, ("ask", "keep_candidates", "downgrade"))

    def test_invalid_target_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_birth_input(
                {
                    "sex": "female",
                    "birth_date": "1990-05-06",
                    "birth_time": "15:20",
                    "birth_place": "高雄市",
                },
                target="unknown",
            )


if __name__ == "__main__":
    unittest.main()
