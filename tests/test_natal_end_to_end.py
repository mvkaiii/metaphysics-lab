import unittest

from engine.birth.models import GeocodeCandidate
from engine.natal.models import NatalSource
from engine.natal.orchestration import (
    build_bazi_imported_view,
    build_normalized_natal,
    build_project_natal,
    resolve_mode_a_input,
)


class FakeLocationProvider:
    name = "public-fixture-location"
    version = "1"

    def geocode(self, query):
        return (
            GeocodeCandidate(
                name="Taipei City, Taiwan",
                latitude=25.0375,
                longitude=121.5637,
                country_code="tw",
                raw_id="public:taipei",
            ),
        )


class NatalEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.provider = FakeLocationProvider()
        self.external_source = NatalSource(
            source_type="external",
            source_name="Astralium",
            source_version="synthetic-public",
            rule_profile="astralium-imported",
            rule_version="unknown",
            maturity="external",
            validation_status="provided",
        )

    def full_mode_a_payload(self):
        return {
            "sex": "male",
            "birth_date": "2000-01-01",
            "birth_time": "12:00",
            "birth_place": "Taipei City",
            "calendar_kind": "gregorian",
        }

    def project_view(self):
        resolution = resolve_mode_a_input(self.full_mode_a_payload())
        self.assertTrue(resolution.ok)
        self.assertIsNotNone(resolution.input)
        return build_project_natal(resolution.input, self.provider)

    def test_mode_a_builds_project_bazi_and_ziwei_without_live_network(self):
        view = self.project_view()
        self.assertEqual(view.source.source_type, "project")
        self.assertEqual(view.source.source_name, "Metaphysics Lab")
        self.assertEqual(view.source.maturity, "experimental")
        self.assertEqual(set(view.bazi["pillars"]), {"year", "month", "day", "hour"})
        self.assertEqual(len(view.ziwei["palaces"]), 12)
        self.assertGreaterEqual(len(view.ziwei["stars"]), 14)
        self.assertEqual(view.birth["place_label"], "Taipei City")
        self.assertEqual(view.birth["resolved_place_label"], "Taipei City, Taiwan")
        self.assertIn("bazi_effective_time", view.time_basis)
        self.assertIn("ziwei_effective_time", view.time_basis)

    def test_mode_b_four_pillars_only_builds_external_bazi_without_guessing_ziwei(self):
        view = build_bazi_imported_view(
            {
                "year": "甲子",
                "month": "丁卯",
                "day": "丙辰",
                "hour": "戊戌",
            },
            self.external_source,
        )
        self.assertEqual(view.bazi["pillars"]["day"], "丙辰")
        self.assertEqual(dict(view.ziwei), {})
        self.assertEqual(dict(view.birth), {})

    def test_mode_c_keeps_external_and_project_views_and_reconciles_fields(self):
        project = self.project_view()
        external = build_bazi_imported_view(project.bazi["pillars"], self.external_source)
        external_payload = {
            "birth": {},
            "bazi": {"pillars": dict(external.bazi["pillars"])},
            "ziwei": {"ming_palace": project.ziwei["ming_palace"]},
        }
        from engine.natal.external import import_external_natal
        external = import_external_natal(external_payload, self.external_source)

        normalized = build_normalized_natal(project=project, external=external)
        self.assertIs(normalized.project, project)
        self.assertIs(normalized.external, external)
        by_path = {field.path: field for field in normalized.resolved.fields}
        self.assertEqual(by_path["ziwei.ming_palace"].status, "MATCH")
        self.assertEqual(by_path["ziwei.ming_palace"].selected_source, "external")
        self.assertEqual(by_path["bazi.pillars.year"].status, "MATCH")
        self.assertTrue(normalized.identity.startswith("natal-"))

    def test_normalized_identity_is_deterministic_for_same_views(self):
        project = self.project_view()
        first = build_normalized_natal(project=project)
        second = build_normalized_natal(project=project)
        self.assertEqual(first.identity, second.identity)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_missing_field_contract_is_machine_readable_not_prompt_text(self):
        result = resolve_mode_a_input({
            "birth_date": "2000-01-01",
            "birth_place": "Taipei City",
        })
        self.assertFalse(result.ok)
        self.assertEqual(result.missing_fields, ("sex", "birth_time"))
        self.assertEqual(result.allowed_actions, ("ask", "keep_candidates", "downgrade"))
        payload = result.to_dict()
        self.assertEqual(payload["error_code"], "missing_required_birth_field")
        self.assertNotIn("prompt", payload)
        self.assertNotIn("message", payload)


if __name__ == "__main__":
    unittest.main()
