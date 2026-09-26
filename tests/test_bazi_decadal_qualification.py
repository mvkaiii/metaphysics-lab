import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from engine.bazi.natal import build_bazi_natal
from engine.birth.models import ResolvedBirthPlace, Sex
from engine.birth.time_views import build_birth_time_views
from engine.calendar import resolve_calendar
from engine.natal.orchestration import _serialize_bazi
from tools.build_bazi_decadal_qualification import (
    BASELINE_SHA,
    BIRTH_VECTOR,
    ENGINE_SOURCE_BINDING,
    FIXTURE_PATH,
    GENERATION_METHOD,
    build_report,
    canonical_json,
    validate_fixture,
)


def _period(index, start_age, start_at, end_at, pillar):
    return {
        "index": index,
        "pillar": pillar,
        "start_age_years": start_age,
        "end_age_years": start_age + 10.0,
        "start_datetime": start_at,
        "end_datetime": end_at,
    }


def _fixture():
    return {
        "schema_version": "1.0",
        "classification": "synthetic_bazi_decadal_engine_view",
        "source_commit": BASELINE_SHA,
        "source_type": "synthetic_engine_output",
        "engine_source": copy.deepcopy(ENGINE_SOURCE_BINDING),
        "generation": copy.deepcopy(GENERATION_METHOD),
        "birth_vector": copy.deepcopy(BIRTH_VECTOR),
        "profile": {
            "profile_id": "bazi-natal-project-v1",
            "rule_version": "1.0-exp",
            "decadal_rule": "three-days-one-year-v1",
            "age_basis": "continuous_years_from_jie_interval",
            "interval_semantics": "needs_confirmation",
        },
        "effective_datetime": "1984-03-13T19:20:00+08:00",
        "timezone": "Asia/Taipei",
        "decadal_direction": "forward",
        "periods": [
            _period(1, 7.376851851851852, "1991-07-30T03:29:19.800000+08:00", "2001-07-29T13:41:19.800000+08:00", "\u620a\u8fb0"),
            _period(2, 17.376851851851853, "2001-07-29T13:41:19.800000+08:00", "2011-07-29T23:53:19.800000+08:00", "\u5df1\u5df3"),
        ],
    }


class BaziDecadalQualificationTests(unittest.TestCase):
    def test_valid_fixture_is_structural_only_and_needs_evidence(self):
        fixture = _fixture()

        self.assertEqual(validate_fixture(fixture), [])
        report = build_report(
            fixture,
            fixture_path=Path("qualification/bazi/decadal/synthetic-engine-view.v1.json"),
            fixture_sha256="a" * 64,
        )

        self.assertEqual(report["result"], "NEEDS_EVIDENCE")
        self.assertFalse(report["maturity_promotion"])
        self.assertEqual(report["boundary_semantics"]["status"], "needs_confirmation")
        self.assertEqual(report["independent_reference"]["status"], "not_available")
        self.assertEqual(
            report["fixture"]["path"],
            "qualification/bazi/decadal/synthetic-engine-view.v1.json",
        )

    def test_non_contiguous_periods_fail_closed(self):
        fixture = _fixture()
        fixture["periods"][1]["start_datetime"] = "2001-07-29T13:41:20.800000+08:00"

        errors = validate_fixture(fixture)

        self.assertTrue(any("contiguous" in error for error in errors))

    def test_non_sexagenary_stem_branch_pair_is_rejected(self):
        fixture = _fixture()
        fixture["periods"][0]["pillar"] = "甲丑"

        errors = validate_fixture(fixture)

        self.assertTrue(any("sexagenary" in error for error in errors))

    def test_malformed_pillar_type_returns_validation_error(self):
        fixture = _fixture()
        fixture["periods"][0]["pillar"] = ["甲", "子"]

        errors = validate_fixture(fixture)

        self.assertTrue(any("sexagenary" in error for error in errors))

    def test_period_index_must_start_at_one_and_remain_sequential(self):
        fixture = _fixture()
        fixture["periods"][0]["index"] = 0

        errors = validate_fixture(fixture)

        self.assertTrue(any("index must start at 1" in error for error in errors))

    def test_boolean_age_is_not_accepted_as_a_number(self):
        fixture = _fixture()
        fixture["periods"][0]["start_age_years"] = True

        errors = validate_fixture(fixture)

        self.assertTrue(any("start_age_years" in error for error in errors))

    def test_nonfinite_age_is_rejected(self):
        fixture = _fixture()
        fixture["periods"][0]["start_age_years"] = float("nan")

        errors = validate_fixture(fixture)

        self.assertTrue(any("finite" in error for error in errors))

    def test_age_integer_outside_finite_float_range_returns_validation_error(self):
        fixture = _fixture()
        fixture["periods"][0]["start_age_years"] = 10**1000

        errors = validate_fixture(fixture)

        self.assertTrue(any("start_age_years" in error and "finite" in error for error in errors))

    def test_age_intervals_must_be_contiguous(self):
        fixture = _fixture()
        fixture["periods"][1]["start_age_years"] += 0.01
        fixture["periods"][1]["end_age_years"] += 0.01

        errors = validate_fixture(fixture)

        self.assertTrue(any("age" in error and "contiguous" in error for error in errors))

    def test_unknown_timezone_is_rejected(self):
        fixture = _fixture()
        fixture["timezone"] = "Mars/Olympus_Mons"

        errors = validate_fixture(fixture)

        self.assertTrue(any("timezone" in error for error in errors))

    def test_datetime_offset_must_match_iana_timezone(self):
        fixture = _fixture()
        fixture["effective_datetime"] = "1984-03-13T19:20:00+09:00"

        errors = validate_fixture(fixture)

        self.assertTrue(any("UTC offset does not match timezone" in error for error in errors))

    def test_datetime_timezone_conversion_overflow_returns_validation_error(self):
        fixture = _fixture()
        fixture["effective_datetime"] = "0001-01-01T00:00:00+23:00"

        errors = validate_fixture(fixture)

        self.assertTrue(any("timezone conversion is out of range" in error for error in errors))

    def test_source_file_binding_mismatch_is_rejected(self):
        fixture = _fixture()
        fixture["engine_source"]["files"][0]["sha256"] = "0" * 64

        errors = validate_fixture(fixture)

        self.assertTrue(any("engine_source" in error for error in errors))

    def test_wrong_source_commit_fails_closed(self):
        fixture = _fixture()
        fixture["source_commit"] = "f" * 40

        errors = validate_fixture(fixture)

        self.assertTrue(any("source_commit" in error for error in errors))

    def test_malformed_periods_return_validation_errors(self):
        fixture = _fixture()
        fixture["periods"] = None

        errors = validate_fixture(fixture)

        self.assertTrue(errors)
        self.assertTrue(any("periods" in error for error in errors))

    def test_report_bytes_are_deterministic(self):
        fixture = _fixture()
        first = build_report(fixture, Path("fixture.json"), "b" * 64)
        reordered = copy.deepcopy(fixture)
        reordered["profile"] = {
            "interval_semantics": "needs_confirmation",
            "age_basis": "continuous_years_from_jie_interval",
            "decadal_rule": "three-days-one-year-v1",
            "rule_version": "1.0-exp",
            "profile_id": "bazi-natal-project-v1",
        }
        second = build_report(reordered, Path("fixture.json"), "b" * 64)

        self.assertEqual(canonical_json(first), canonical_json(second))

    def test_fixture_digest_is_independent_of_checkout_line_endings(self):
        fixture = _fixture()
        fixture_bytes = canonical_json(fixture).encode("utf-8")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lf_path = root / "fixture-lf.json"
            crlf_path = root / "fixture-crlf.json"
            lf_path.write_bytes(fixture_bytes)
            crlf_path.write_bytes(fixture_bytes.replace(b"\n", b"\r\n"))

            lf_report = build_report(fixture, fixture_path=lf_path)
            crlf_report = build_report(fixture, fixture_path=crlf_path)

        self.assertEqual(lf_report["fixture"]["sha256"], crlf_report["fixture"]["sha256"])

    def test_repo_absolute_fixture_path_is_normalized(self):
        report = build_report(_fixture(), FIXTURE_PATH, "c" * 64)

        self.assertEqual(
            report["fixture"]["path"],
            "qualification/bazi/decadal/synthetic-engine-view.v1.json",
        )

    def test_real_fixture_is_present_and_bound_to_baseline(self):
        fixture_path = Path(__file__).parents[1] / "qualification/bazi/decadal/synthetic-engine-view.v1.json"
        self.assertTrue(fixture_path.is_file())
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.assertEqual(fixture["source_commit"], BASELINE_SHA)
        self.assertEqual(validate_fixture(fixture), [])

    def test_direct_and_module_cli_entrypoints_load(self):
        root = Path(__file__).parents[1]
        direct = subprocess.run(
            [sys.executable, str(root / "tools" / "build_bazi_decadal_qualification.py"), "--help"],
            cwd=str(root),
            capture_output=True,
            text=True,
        )
        module = subprocess.run(
            [sys.executable, "-m", "tools.build_bazi_decadal_qualification", "--help"],
            cwd=str(root),
            capture_output=True,
            text=True,
        )

        self.assertEqual(direct.returncode, 0, direct.stderr)
        self.assertEqual(module.returncode, 0, module.stderr)

    def test_fixture_decadal_values_match_existing_project_engine_serializer(self):
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        birth_vector = fixture["birth_vector"]
        resolution = resolve_calendar(birth_vector["reported_datetime"], birth_vector["timezone"])
        self.assertTrue(resolution.ok, getattr(resolution, "error", None))
        place = birth_vector["resolved_location"]
        location = ResolvedBirthPlace(
            canonical_name=place["canonical_name"],
            latitude=place["latitude"],
            longitude=place["longitude"],
            timezone=birth_vector["timezone"],
            provider_name=place["provider_name"],
            provider_version=place["provider_version"],
            resolution_status=place["resolution_status"],
            provider_reference=place["provider_reference"],
        )
        time_views = build_birth_time_views(resolution.context, location)
        sex = Sex.MALE if birth_vector["sex"] == "male" else Sex.FEMALE
        chart = build_bazi_natal(resolution.context, time_views, sex)
        serialized = _serialize_bazi(chart)

        self.assertEqual(chart.effective_datetime.isoformat(), fixture["effective_datetime"])
        self.assertEqual(chart.profile.profile_id, fixture["profile"]["profile_id"])
        self.assertEqual(chart.profile.rule_version, fixture["profile"]["rule_version"])
        self.assertEqual(chart.profile.decadal_rule, fixture["profile"]["decadal_rule"])
        self.assertEqual(serialized["decadal_direction"], fixture["decadal_direction"])
        self.assertEqual(serialized["decadal_periods"], fixture["periods"])


if __name__ == "__main__":
    unittest.main()
