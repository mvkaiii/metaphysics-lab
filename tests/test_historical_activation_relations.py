import unittest

from engine.historical import relations


class HistoricalActivationRelationTests(unittest.TestCase):
    def test_frozen_relation_tables_match_profile(self):
        self.assertEqual(
            relations.CLASH_PAIRS,
            frozenset(frozenset(pair) for pair in (("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥"))),
        )
        self.assertIn(frozenset(("子", "丑")), relations.COMBINATION_PAIRS)
        self.assertIn(frozenset(("申", "子", "辰")), relations.THREE_HARMONY_SETS)
        self.assertIn(frozenset(("亥", "子", "丑")), relations.THREE_MEETING_SETS)
        self.assertEqual(
            relations.FULL_PUNISHMENT_SETS,
            frozenset((frozenset(("寅", "巳", "申")), frozenset(("丑", "戌", "未")))),
        )
        self.assertEqual(relations.SELF_PUNISHMENTS, frozenset(("辰", "午", "酉", "亥")))
        self.assertIn(frozenset(("子", "未")), relations.HARM_PAIRS)
        self.assertIn(frozenset(("子", "酉")), relations.BREAK_PAIRS)
        self.assertIn(frozenset(("甲", "己")), relations.STEM_COMBINATION_PAIRS)

    def test_pairs_are_unordered_and_unsupported_relations_are_absent(self):
        self.assertIn(frozenset(("午", "子")), relations.CLASH_PAIRS)
        self.assertNotIn(frozenset(("甲", "庚")), relations.STEM_COMBINATION_PAIRS)
        self.assertNotIn(frozenset(("子", "寅")), relations.CLASH_PAIRS)


if __name__ == "__main__":
    unittest.main()
