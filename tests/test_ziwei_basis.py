import unittest

from engine.ziwei.basis import build_palace_stem_index, build_star_location_index
from engine.ziwei.errors import ZiweiPhase2AError
from engine.ziwei.models import PalaceStemRecord, StarLocationRecord
from tests.ziwei_phase2a_fixtures import CHART, PROVENANCE, SYNTHETIC_PALACE_STEM_RECORDS, SYNTHETIC_STAR_RECORDS


class ZiweiBasisTests(unittest.TestCase):
    def test_duplicate_star_same_palace_is_rejected(self):
        records = (StarLocationRecord("天機", "夫妻宮"), StarLocationRecord("天機", "夫妻宮"))
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_star_location_index(records, CHART, PROVENANCE)
        self.assertEqual(cm.exception.code, "duplicate_star_location")

    def test_duplicate_star_conflicting_palace_is_rejected(self):
        records = (StarLocationRecord("天機", "夫妻宮"), StarLocationRecord("天機", "官祿宮"))
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_star_location_index(records, CHART, PROVENANCE)
        self.assertEqual(cm.exception.code, "duplicate_star_location")

    def test_palace_stems_require_all_twelve_unique_palaces(self):
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_palace_stem_index(SYNTHETIC_PALACE_STEM_RECORDS[:-1], CHART, PROVENANCE)
        self.assertEqual(cm.exception.code, "invalid_palace_stem_index")

    def test_duplicate_palace_is_rejected_before_mapping(self):
        records = SYNTHETIC_PALACE_STEM_RECORDS + (PalaceStemRecord("命宮", "甲"),)
        with self.assertRaises(ZiweiPhase2AError) as cm:
            build_palace_stem_index(records, CHART, PROVENANCE)
        self.assertEqual(cm.exception.code, "duplicate_palace_stem")

    def test_valid_indexes_materialize(self):
        stars = build_star_location_index(SYNTHETIC_STAR_RECORDS, CHART, PROVENANCE)
        stems = build_palace_stem_index(SYNTHETIC_PALACE_STEM_RECORDS, CHART, PROVENANCE)
        self.assertEqual(len(stars.locations), 15)
        self.assertEqual(len(stems.stems), 12)


if __name__ == "__main__":
    unittest.main()
