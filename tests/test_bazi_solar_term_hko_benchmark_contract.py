import unittest

from tools.benchmark_bazi_solar_terms_hko import START_YEAR, END_YEAR


class BaziSolarTermHkoBenchmarkContractTests(unittest.TestCase):
    def test_general_range_is_continuous_and_predeclared(self):
        self.assertEqual(START_YEAR, 2010)
        self.assertEqual(END_YEAR, 2026)
        self.assertEqual(END_YEAR - START_YEAR + 1, 17)


if __name__ == "__main__":
    unittest.main()
