import json
from pathlib import Path
import subprocess
import sys
import unittest

from engine.ziwei.capabilities import get_capability


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "qualification" / "ziwei" / "phase2c" / "phase2c-summary.json"
PUBLIC_FIXTURE = ROOT / "qualification" / "ziwei" / "phase2c" / "public-iztro-flowing-star-vectors.json"
PRIVATE_SUMMARY = ROOT / "qualification" / "ziwei" / "phase2c" / "private-astralium-summary.json"
APPROVED_DESIGN_HEAD = "be0745af16d4d40cb7e3bd90c1667ee2dc5a2cd0"
FORBIDDEN_PRIVATE_KEYS = {
    "full_name",
    "full_address",
    "hospital",
    "birth_datetime",
    "raw_birth_input",
    "raw_chart",
    "raw_payload",
    "external_raw",
}
APPROVED_STARS = {
    "天魁",
    "天鉞",
    "文昌",
    "文曲",
    "祿存",
    "擎羊",
    "陀羅",
    "天馬",
    "紅鸞",
    "天喜",
    "年解",
}
SUMMARY_TOP_LEVEL_KEYS = {
    "profile_id",
    "rule_version",
    "public_qualification",
    "private_qualification",
    "capability_states",
    "release_version",
    "approved_design_revision",
}


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _walk(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


class ZiweiPhase2CAcceptanceTests(unittest.TestCase):
    def test_summary_records_public_and_private_evidence(self):
        summary = _load(SUMMARY)
        self.assertEqual(set(summary), SUMMARY_TOP_LEVEL_KEYS)
        public = summary["public_qualification"]
        private = summary["private_qualification"]
        self.assertEqual(public["source_case_count"], 600)
        self.assertEqual(public["placement_check_count"], 6120)
        self.assertEqual(public["unexpected_mismatch_count"], 0)
        self.assertEqual(public["status"], "PASS")
        self.assertEqual(private["status"], "PENDING")
        self.assertEqual(private["case_count"], 0)
        self.assertEqual(private["unexpected_mismatch_count"], 0)
        self.assertFalse(private["promotion_allowed"])

    def test_capability_states_do_not_cascade(self):
        expected = {
            "ziwei.flowing_stars": ("implemented", "experimental", "on_demand", "1.0-exp"),
            "ziwei.transformations": ("implemented", "stable", "on_demand", "1.0"),
            "ziwei.flying": ("implemented", "stable", "on_demand", "1.0"),
            "ziwei.flow_month_stem": ("implemented", "experimental", "on_demand", "1.0-exp"),
            "ziwei.flow_day_stem": ("implemented", "experimental", "on_demand", "1.0-exp"),
            "ziwei.flow_hour_stem": ("implemented", "experimental", "on_demand", "1.0-exp"),
            "ziwei.natal_chart": ("implemented", "experimental", "on_demand", "1.0-exp"),
        }
        for capability_id, state in expected.items():
            with self.subTest(capability_id=capability_id):
                cap = get_capability(capability_id)
                actual = (cap["implementation"], cap["maturity"], cap["routing"], cap["rule_version"])
                self.assertEqual(actual, state)

        summary_states = _load(SUMMARY)["capability_states"]
        for capability_id, state in expected.items():
            self.assertEqual(summary_states[capability_id], "/".join(state))

    def test_release_identity_is_unchanged(self):
        text = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        self.assertIn("Metaphysics Lab Core：**v1.2.0**", text)
        self.assertEqual(_load(SUMMARY)["release_version"], "v1.2.0")

    def test_summary_and_private_evidence_are_privacy_safe(self):
        for path in (SUMMARY, PRIVATE_SUMMARY):
            data = _load(path)
            for key, value in _walk(data):
                self.assertNotIn(key.lower(), FORBIDDEN_PRIVATE_KEYS)
                if isinstance(value, str):
                    lowered = value.lower()
                    self.assertNotIn("private/", lowered)
                    self.assertNotIn("/private/", lowered)
                    self.assertNotIn("\\private\\", lowered)

    def test_public_fixture_has_no_excluded_star_leakage(self):
        fixture = _load(PUBLIC_FIXTURE)
        for case in fixture["cases"]:
            stars = {placement["base_star"] for placement in case["placements"]}
            self.assertTrue(stars <= APPROVED_STARS)
            self.assertNotIn("歲建", stars)
            self.assertNotIn("將星", stars)
            self.assertNotIn("博士", stars)
            self.assertNotIn("長生", stars)

    def test_phase2c_does_not_change_qimen(self):
        result = subprocess.run(
            ["git", "diff", "--name-only", "%s...HEAD" % APPROVED_DESIGN_HEAD],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        changed = tuple(line.strip() for line in result.stdout.splitlines() if line.strip())
        qimen = tuple(path for path in changed if "qimen" in path.lower() or "奇門" in path)
        self.assertEqual(qimen, ())

    def test_public_qualifier_emits_private_pending_marker(self):
        result = subprocess.run(
            [sys.executable, "tools/qualify_ziwei_phase2c.py", "--public"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("IZTRO_FLOWING_STARS_600_600_PASS", result.stdout)
        self.assertIn("IZTRO_FLOWING_STARS_0_UNEXPECTED_MISMATCH", result.stdout)
        self.assertIn("PHASE2C_PRIVATE_FLOWING_STARS_PENDING_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
