import unittest

from tools.benchmark_bazi_solar_terms_hko import START_YEAR, END_YEAR


class BaziSolarTermHkoBenchmarkContractTests(unittest.TestCase):
    def test_general_range_is_continuous_and_predeclared(self):
        self.assertEqual(START_YEAR, 2013)
        self.assertEqual(END_YEAR, 2019)
        self.assertEqual(END_YEAR - START_YEAR + 1, 7)


if __name__ == "__main__":
    unittest.main()
