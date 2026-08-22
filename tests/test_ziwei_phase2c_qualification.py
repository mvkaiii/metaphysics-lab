import json
import unittest
from pathlib import Path

from tools.qualify_ziwei_phase2c import qualify_public


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "qualification" / "ziwei" / "phase2c" / "public-iztro-flowing-star-vectors.json"
PRIVATE_SUMMARY = ROOT / "qualification" / "ziwei" / "phase2c" / "private-astralium-summary.json"
PINNED_REVISION = "814b77e6371e1050cac31bbf674db3c3138fcfde"
BASE_CATALOG = ("天魁", "天鉞", "文昌", "文曲", "祿存", "擎羊", "陀羅", "天馬", "紅鸞", "天喜")


class ZiweiPhase2CQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_public_fixture_is_exact_pinned_oracle(self):
        data = self.fixture
        self.assertEqual(data["schema"], "metaphysics-lab.ziwei.phase2c.public-qualification.v1")
        self.assertEqual(data["profile_id"], "ziwei-flowing-stars-common-v1")
        self.assertEqual(data["oracle"]["repository"], "SylarLong/iztro")
        self.assertEqual(data["oracle"]["package_version"], "2.6.0")
        self.assertEqual(data["oracle"]["revision"], PINNED_REVISION)
        self.assertEqual(data["source_case_count"], 600)
        self.assertEqual(data["placement_check_count"], 6120)
        self.assertEqual(len(data["cases"]), 600)

    def test_independent_golden_anchors_are_exact(self):
        expected = {
            ("decadal", "庚", "辰"): (
                ("天魁", "soft", "丑"), ("天鉞", "soft", "未"), ("文昌", "soft", "亥"),
                ("文曲", "soft", "卯"), ("祿存", "lucun", "申"), ("擎羊", "tough", "酉"),
                ("陀羅", "tough", "未"), ("天馬", "tianma", "寅"), ("紅鸞", "flower", "亥"),
                ("天喜", "flower", "巳"),
            ),
            ("yearly", "癸", "卯"): (
                ("天魁", "soft", "卯"), ("天鉞", "soft", "巳"), ("文昌", "soft", "卯"),
                ("文曲", "soft", "亥"), ("祿存", "lucun", "子"), ("擎羊", "tough", "丑"),
                ("陀羅", "tough", "亥"), ("天馬", "tianma", "巳"), ("紅鸞", "flower", "子"),
                ("天喜", "flower", "午"), ("年解", "helper", "未"),
            ),
        }
        anchors = {}
        for item in self.fixture["golden_anchors"]:
            key = (item["scope"], item["stem"], item["branch"])
            anchors[key] = tuple(
                (placement["base_star"], placement["category"], placement["target_branch"])
                for placement in item["placements"]
            )
        self.assertEqual(anchors, expected)

    def test_fixture_contains_only_approved_scope_and_star_catalog(self):
        allowed_scopes = {"decadal", "yearly", "monthly", "daily", "hourly"}
        for case in self.fixture["cases"]:
            self.assertIn(case["scope"], allowed_scopes)
            expected = set(BASE_CATALOG + (("年解",) if case["scope"] == "yearly" else ()))
            self.assertEqual({item["base_star"] for item in case["placements"]}, expected)
        serialized = json.dumps(self.fixture, ensure_ascii=False)
        for excluded in ("歲前十二神", "將前十二神", "博士十二神", "長生十二神", "小限流曜"):
            self.assertNotIn(excluded, serialized)
        for private_key in ("full_name", "full_address", "hospital", "birth_datetime", "raw_birth_input", "raw_chart", "raw_payload"):
            self.assertNotIn(private_key, serialized)

    def test_public_qualification_matches_all_600_cases(self):
        report = qualify_public(FIXTURE)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["source_case_count"], 600)
        self.assertEqual(report["placement_check_count"], 6120)
        self.assertEqual(report["unexpected_mismatch_count"], 0)
        self.assertEqual(report["profile_id"], "ziwei-flowing-stars-common-v1")
        self.assertEqual(report["oracle_revision"], PINNED_REVISION)

    def test_private_astralium_qualification_starts_pending(self):
        summary = json.loads(PRIVATE_SUMMARY.read_text(encoding="utf-8"))
        self.assertEqual(summary, {
            "source": "Astralium flowing-stars",
            "status": "PENDING",
            "case_count": 0,
            "unexpected_mismatch_count": 0,
            "promotion_allowed": False,
            "raw_private_data_committed": False,
        })


if __name__ == "__main__":
    unittest.main()
