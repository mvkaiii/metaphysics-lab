import unittest

from tools.run_bazi_decadal_nonindependent_dryrun import (
    direction_from_sealed_coverage_tags,
)


class BaziDecadalNonIndependentDryRunTests(unittest.TestCase):
    def test_direction_tag_is_explicitly_tainted_metadata(self):
        self.assertEqual(
            direction_from_sealed_coverage_tags(
                ["common_year", "forward_direction_expected_from_contract"]
            ),
            "forward",
        )
        self.assertEqual(
            direction_from_sealed_coverage_tags(
                ["leap_year", "reverse_direction_expected_from_contract"]
            ),
            "reverse",
        )

    def test_missing_or_ambiguous_direction_tag_fails_closed(self):
        with self.assertRaises(ValueError):
            direction_from_sealed_coverage_tags(["common_year"])
        with self.assertRaises(ValueError):
            direction_from_sealed_coverage_tags([
                "forward_direction_expected_from_contract",
                "reverse_direction_expected_from_contract",
            ])


if __name__ == "__main__":
    unittest.main()
