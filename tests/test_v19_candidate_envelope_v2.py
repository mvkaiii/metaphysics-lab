import copy
import unittest
from unittest import mock

from engine.birth.models import ResolvedBirthPlace
from engine.distribution.runtime import dispatch
from engine.natal.candidates import (
    _candidate_domain,
    build_candidate_envelope,
    build_candidate_envelope_v1_legacy,
)
from engine.natal.errors import NatalFoundationError
from tests.test_distribution_partial_case import IDENTITY


NY = ResolvedBirthPlace(
    canonical_name="New York City, USA",
    latitude=40.7128,
    longitude=-74.0060,
    timezone="America/New_York",
    provider_name="fixture",
    provider_version="1",
    resolution_status="resolved",
    provider_reference="fixture:nyc",
)

LORD_HOWE = ResolvedBirthPlace(
    canonical_name="Lord Howe Island, Australia",
    latitude=-31.55,
    longitude=159.08,
    timezone="Australia/Lord_Howe",
    provider_name="fixture",
    provider_version="1",
    resolution_status="resolved",
    provider_reference="fixture:lord-howe",
)

TAIPEI = ResolvedBirthPlace(
    canonical_name="Taipei City, Taiwan",
    latitude=25.033,
    longitude=121.5654,
    timezone="Asia/Taipei",
    provider_name="fixture",
    provider_version="1",
    resolution_status="resolved",
    provider_reference="fixture:taipei",
)


def _birth(day, **extra):
    result = {
        "sex": "male",
        "birth_date": day,
        "birth_place": "fixture",
    }
    result.update(extra)
    return result


def _fake_row(occurrence, signature="same", value="same"):
    return {
        "minute": occurrence["minute"],
        "utc_datetime": occurrence["utc_datetime"],
        "signature": signature,
        "bazi": {"day_master": "丙", "x": value},
        "ziwei": {"life_master": "祿存", "x": value},
        "decadal_start": "2000-01-01T00:00:00+08:00",
        "occurrence": {
            key: occurrence[key]
            for key in (
                "occurrence_id", "reported_time", "civil_datetime",
                "local_datetime", "utc_datetime", "utc_offset",
                "timezone", "fold",
            )
        },
        "time_basis": {},
    }


class CandidateDomainV2Tests(unittest.TestCase):
    def test_fall_back_unknown_day_has_1500_legal_occurrences(self):
        birth = _birth("2026-11-01", birth_time_precision="unknown_time")
        precision, minutes = ("unknown_time", range(0, 1440))
        domain = _candidate_domain(birth, NY, precision, minutes)
        occurrences = domain["_occurrences"]
        self.assertEqual(domain["status"], "ready")
        self.assertEqual(domain["declared_label_count"], 1440)
        self.assertEqual(domain["legal_occurrence_count"], 1500)
        self.assertEqual(domain["excluded_label_count"], 0)
        fold_occurrences = [
            item for item in occurrences if item["reported_time"] == "01:30"
        ]
        self.assertEqual(len(fold_occurrences), 2)
        self.assertEqual(
            [item["utc_offset"] for item in fold_occurrences],
            ["-04:00", "-05:00"],
        )
        self.assertEqual([item["fold"] for item in fold_occurrences], [0, 1])

    def test_spring_gap_unknown_day_has_1380_legal_occurrences_and_60_exclusions(self):
        birth = _birth("2026-03-08", birth_time_precision="unknown_time")
        domain = _candidate_domain(
            birth,
            NY,
            "unknown_time",
            range(0, 1440),
        )
        self.assertEqual(domain["status"], "ready")
        self.assertEqual(domain["declared_label_count"], 1440)
        self.assertEqual(domain["legal_occurrence_count"], 1380)
        self.assertEqual(domain["excluded_label_count"], 60)
        self.assertEqual(
            {item["error_code"] for item in domain["deterministic_exclusions"]},
            {"nonexistent_local_time"},
        )

    def test_lord_howe_fold_is_30_minutes_not_hardcoded_one_hour(self):
        birth = _birth("2026-04-05", birth_time_precision="unknown_time")
        domain = _candidate_domain(
            birth,
            LORD_HOWE,
            "unknown_time",
            range(0, 1440),
        )
        self.assertEqual(domain["legal_occurrence_count"], 1470)
        self.assertEqual(domain["excluded_label_count"], 0)


class CandidateEnvelopeV2CoverageTests(unittest.TestCase):
    def test_spring_gap_exclusions_do_not_lower_complete_coverage(self):
        birth = _birth("2026-03-08", birth_time_precision="unknown_time")
        with mock.patch(
            "engine.natal.candidates._build_occurrence_candidate",
            side_effect=lambda birth_payload, location, occurrence: _fake_row(occurrence),
        ):
            envelope = build_candidate_envelope(birth, NY)

        self.assertEqual(envelope["profile_id"], "natal-candidate-envelope-v2")
        self.assertEqual(envelope["rule_version"], "2.0-exp")
        self.assertEqual(envelope["candidate_domain"]["legal_occurrence_count"], 1380)
        self.assertEqual(envelope["candidate_domain"]["excluded_label_count"], 60)
        self.assertEqual(envelope["candidate_coverage"]["status"], "complete")
        self.assertEqual(envelope["candidate_coverage"]["materialized_occurrence_count"], 1380)
        self.assertEqual(envelope["candidate_coverage"]["unresolved_occurrence_count"], 0)
        self.assertEqual(envelope["candidate_count"], 1)
        self.assertEqual(envelope["candidate_coverage"]["material_state_count"], 1)
        self.assertEqual(len(envelope["boundary_ambiguities"]), 60)

    def test_fall_back_candidate_count_remains_material_state_count(self):
        birth = _birth("2026-11-01", birth_time_precision="unknown_time")
        with mock.patch(
            "engine.natal.candidates._build_occurrence_candidate",
            side_effect=lambda birth_payload, location, occurrence: _fake_row(occurrence),
        ):
            envelope = build_candidate_envelope(birth, NY)

        self.assertEqual(envelope["candidate_domain"]["legal_occurrence_count"], 1500)
        self.assertEqual(envelope["candidate_coverage"]["materialized_occurrence_count"], 1500)
        self.assertEqual(envelope["candidate_count"], 1)
        state = envelope["candidates"][0]
        self.assertEqual(state["occurrence_count"], 1500)
        self.assertEqual(
            state["occurrence_start"]["utc_datetime"],
            "2026-11-01T04:00:00+00:00",
        )
        self.assertEqual(
            state["occurrence_end"]["utc_datetime"],
            "2026-11-02T04:59:00+00:00",
        )

    def test_partial_coverage_moves_observed_equal_fact_to_undetermined(self):
        birth = _birth(
            "1984-03-13",
            birth_time_precision="bounded",
            birth_time_range=["19:20", "19:21"],
        )
        calls = {"count": 0}

        def evaluator(birth_payload, location, occurrence):
            calls["count"] += 1
            if calls["count"] == 2:
                raise NatalFoundationError("fixture_failure", "injected")
            return _fake_row(occurrence)

        with mock.patch(
            "engine.natal.candidates._build_occurrence_candidate",
            side_effect=evaluator,
        ):
            envelope = build_candidate_envelope(birth, TAIPEI)

        self.assertEqual(envelope["candidate_coverage"]["status"], "partial")
        self.assertEqual(envelope["candidate_coverage"]["legal_occurrence_count"], 2)
        self.assertEqual(envelope["candidate_coverage"]["materialized_occurrence_count"], 1)
        self.assertEqual(envelope["candidate_coverage"]["unresolved_occurrence_count"], 1)
        self.assertEqual(envelope["invariant_bazi_facts"], {})
        self.assertEqual(envelope["undetermined_bazi_facts"]["day_master"], "丙")
        self.assertEqual(envelope["invariant_ziwei_facts"], {})
        self.assertEqual(envelope["undetermined_ziwei_facts"]["life_master"], "祿存")
        self.assertIn("unique_birth_time_claim", envelope["blocked_analysis"])

    def test_partial_coverage_can_still_confirm_observed_variant(self):
        birth = _birth(
            "1984-03-13",
            birth_time_precision="bounded",
            birth_time_range=["19:20", "19:22"],
        )
        calls = {"count": 0}

        def evaluator(birth_payload, location, occurrence):
            calls["count"] += 1
            if calls["count"] == 3:
                raise NatalFoundationError("fixture_failure", "injected")
            value = "A" if calls["count"] == 1 else "B"
            return _fake_row(occurrence, signature=value, value=value)

        with mock.patch(
            "engine.natal.candidates._build_occurrence_candidate",
            side_effect=evaluator,
        ):
            envelope = build_candidate_envelope(birth, TAIPEI)

        self.assertEqual(envelope["candidate_coverage"]["status"], "partial")
        self.assertEqual(
            envelope["variant_bazi_facts"]["x"],
            {"candidate-01": "A", "candidate-02": "B"},
        )
        self.assertEqual(
            envelope["variant_ziwei_facts"]["x"],
            {"candidate-01": "A", "candidate-02": "B"},
        )

    def test_exact_fold_routes_to_two_legal_occurrences_without_auto_selection(self):
        result = dispatch(
            "natal.candidate_envelope",
            {
                "birth": {
                    "sex": "male",
                    "birth_date": "2026-11-01",
                    "birth_time_precision": "exact",
                    "birth_time": "01:30",
                    "birth_place": "New York City",
                },
                "resolved_location": NY.to_dict(),
            },
        )
        self.assertTrue(result["ok"], result)
        envelope = result["data"]["candidate_envelope"]
        self.assertEqual(envelope["natal_precision_state"], "exact")
        self.assertEqual(envelope["local_time_resolution"], "ambiguous_fold")
        self.assertEqual(envelope["candidate_domain"]["legal_occurrence_count"], 2)
        self.assertEqual(envelope["candidate_coverage"]["status"], "complete")
        self.assertEqual(envelope["candidate_coverage"]["materialized_occurrence_count"], 2)
        self.assertIn("unique_birth_time_claim", envelope["blocked_analysis"])

    def test_exact_gap_returns_unsupported_domain_without_fabricating_candidate(self):
        result = dispatch(
            "natal.candidate_envelope",
            {
                "birth": {
                    "sex": "male",
                    "birth_date": "2026-03-08",
                    "birth_time_precision": "exact",
                    "birth_time": "02:30",
                    "birth_place": "New York City",
                },
                "resolved_location": NY.to_dict(),
            },
        )
        self.assertTrue(result["ok"], result)
        envelope = result["data"]["candidate_envelope"]
        self.assertEqual(envelope["local_time_resolution"], "nonexistent")
        self.assertEqual(envelope["candidate_domain"]["status"], "unsupported")
        self.assertEqual(envelope["candidate_domain"]["legal_occurrence_count"], 0)
        self.assertEqual(envelope["candidate_coverage"]["status"], "unsupported")
        self.assertEqual(envelope["candidate_count"], 0)
        self.assertEqual(envelope["candidates"], [])


class CandidateEnvelopeV2CaseCompatibilityTests(unittest.TestCase):
    def test_incomplete_v2_coverage_cannot_persist_as_canonical_partial_case(self):
        built = dispatch(
            "natal.candidate_envelope",
            {
                "birth": {
                    "sex": "male",
                    "birth_date": "1984-03-13",
                    "birth_time_range": ["19:20", "19:21"],
                    "birth_place": "台北市",
                },
                "resolved_location": TAIPEI.to_dict(),
            },
        )
        self.assertTrue(built["ok"], built)
        envelope = copy.deepcopy(built["data"]["candidate_envelope"])
        envelope["candidate_coverage"]["status"] = "partial"
        envelope["candidate_coverage"]["unresolved_occurrence_count"] = 1
        envelope["candidate_coverage"]["materialized_occurrence_count"] -= 1
        result = dispatch(
            "export_case_markdown",
            {
                "candidate_envelope": envelope,
                "resolved_location": TAIPEI.to_dict(),
                **IDENTITY,
                "generated_at": "2026-10-02T00:00:00+08:00",
                "last_modified_by": "test",
            },
        )
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "invalid_candidate_envelope")

    def test_legacy_v1_builder_remains_available_for_old_case_authority(self):
        birth = {
            "sex": "male",
            "birth_date": "1984-03-13",
            "birth_time_range": ["19:20", "19:21"],
            "birth_place": "台北市",
        }
        envelope = build_candidate_envelope_v1_legacy(birth, TAIPEI)
        self.assertEqual(envelope["profile_id"], "natal-candidate-envelope-v1")
        self.assertEqual(envelope["rule_version"], "1.0-exp")
        result = dispatch(
            "export_case_markdown",
            {
                "candidate_envelope": envelope,
                "resolved_location": TAIPEI.to_dict(),
                **IDENTITY,
                "generated_at": "2026-10-02T00:00:00+08:00",
                "last_modified_by": "test",
            },
        )
        self.assertTrue(result["ok"], result)


if __name__ == "__main__":
    unittest.main()
