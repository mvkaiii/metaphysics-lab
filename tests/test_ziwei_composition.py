import unittest

from engine.ziwei.models import AvailabilityRecord, NatalContext, ZiweiLayerStack


class ZiweiCompositionModelTests(unittest.TestCase):
    def test_availability_record_is_explicit(self):
        item = AvailabilityRecord("unavailable", "fine_cycle_stem_resolver_not_enabled")
        self.assertEqual(item.status, "unavailable")


if __name__ == "__main__":
    unittest.main()
