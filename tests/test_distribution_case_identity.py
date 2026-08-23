import unittest

from engine.distribution.case_identity import build_case_filename, parse_case_filename


CANONICAL = (
    "00_專案索引.md",
    "01_命盤核心摘要.md",
    "02_命盤資料校驗紀錄.md",
    "03_八字結構化資料包.md",
    "04_紫微基礎資料包.md",
    "05_驗證事件紀錄.md",
    "06_流年追蹤紀錄.md",
    "07_問事追蹤紀錄.md",
    "08_重大決策紀錄.md",
)


class CaseIdentityFilenameTests(unittest.TestCase):
    def test_builds_single_underscore_canonical_filename(self):
        self.assertEqual(
            build_case_filename("Kai", "7F3A2C", "01_命盤核心摘要.md"),
            "Kai_7F3A2C_01_命盤核心摘要.md",
        )

    def test_parser_resolves_from_right_when_label_contains_underscore(self):
        parsed = parse_case_filename("Kai_Chen_7F3A2C_01_命盤核心摘要.md", CANONICAL)
        self.assertEqual(parsed["filename_label"], "Kai_Chen")
        self.assertEqual(parsed["subject_short_id"], "7F3A2C")
        self.assertEqual(parsed["canonical_filename"], "01_命盤核心摘要.md")
        self.assertFalse(parsed["legacy"])

    def test_parser_recognizes_legacy_bare_filename(self):
        parsed = parse_case_filename("01_命盤核心摘要.md", CANONICAL)
        self.assertTrue(parsed["legacy"])
        self.assertEqual(parsed["canonical_filename"], "01_命盤核心摘要.md")

    def test_parser_rejects_noncanonical_title_or_short_id(self):
        with self.assertRaises(ValueError):
            parse_case_filename("Kai_7f3a2c_01_錯誤標題.md", CANONICAL)
        with self.assertRaises(ValueError):
            parse_case_filename("Kai_NOTHEX_01_命盤核心摘要.md", CANONICAL)


if __name__ == "__main__":
    unittest.main()
