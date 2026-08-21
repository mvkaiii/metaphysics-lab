import unittest

from geopy.exc import GeocoderServiceError

from engine.birth.errors import BirthFoundationError
from engine.birth.location import NominatimLocationProvider, resolve_birth_place
from engine.birth.models import BirthPlaceInput, GeocodeCandidate


class FakeProvider:
    name = "fake"
    version = "1"

    def geocode(self, query):
        return (
            GeocodeCandidate(
                "Taipei City, Taiwan",
                25.0375,
                121.5637,
                "tw",
                "fake:1",
            ),
        )


class EmptyProvider:
    name = "empty"
    version = "1"

    def geocode(self, query):
        return ()


class AmbiguousProvider:
    name = "ambiguous"
    version = "1"

    def geocode(self, query):
        return (
            GeocodeCandidate("Springfield A", 39.78, -89.64, "us", "a"),
            GeocodeCandidate("Springfield B", 44.05, -123.02, "us", "b"),
        )


class OfflineProvider:
    name = "offline"
    version = "1"

    def geocode(self, query):
        raise GeocoderServiceError("provider offline")


class RecordingGeocoder:
    def __init__(self):
        self.kwargs = None

    def geocode(self, query, **kwargs):
        self.kwargs = kwargs
        return []


class BirthLocationTests(unittest.TestCase):
    def test_unique_place_resolves_coordinates_and_iana_timezone(self):
        result = resolve_birth_place(BirthPlaceInput("台北市"), FakeProvider())
        self.assertEqual(result.timezone, "Asia/Taipei")
        self.assertEqual(result.provider_name, "fake")
        self.assertEqual(result.provider_version, "1")
        self.assertEqual(result.resolution_status, "resolved")
        self.assertEqual(result.provider_reference, "fake:1")

    def test_zero_candidates_fail_closed(self):
        with self.assertRaises(BirthFoundationError) as caught:
            resolve_birth_place(BirthPlaceInput("不存在"), EmptyProvider())
        self.assertEqual(caught.exception.code, "location_not_resolved")

    def test_multiple_material_candidates_fail_closed(self):
        with self.assertRaises(BirthFoundationError) as caught:
            resolve_birth_place(BirthPlaceInput("Springfield"), AmbiguousProvider())
        self.assertEqual(caught.exception.code, "ambiguous_birth_place")

    def test_provider_outage_is_not_reported_as_no_result(self):
        with self.assertRaises(BirthFoundationError) as caught:
            resolve_birth_place(BirthPlaceInput("台北市"), OfflineProvider())
        self.assertEqual(caught.exception.code, "location_provider_unavailable")

    def test_nominatim_default_adapter_requests_city_level_features(self):
        provider = NominatimLocationProvider("test-agent")
        recorder = RecordingGeocoder()
        provider._geocoder = recorder
        self.assertEqual(provider.geocode("London, UK"), ())
        self.assertEqual(recorder.kwargs["featuretype"], "city")
        self.assertFalse(recorder.kwargs["exactly_one"])
        self.assertEqual(recorder.kwargs["limit"], 5)


if __name__ == "__main__":
    unittest.main()
