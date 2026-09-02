import copy
import hashlib
import json
import unittest

from engine.distribution.evidence import build_evidence_features
from engine.distribution.runtime import dispatch


BIRTH = {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time": "19:20",
    "birth_place": "台北市",
}

RESOLVED_TAIPEI = {
    "canonical_name": "Taipei City, Taiwan",
    "latitude": 25.033,
    "longitude": 121.5654,
    "timezone": "Asia/Taipei",
    "provider_name": "ai_host",
    "provider_version": "user-confirmed",
    "provider_reference": None,
}


def canonical_bytes(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


class DistributionForecastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        built = dispatch(
            "build_natal",
            {"birth": BIRTH, "resolved_location": RESOLVED_TAIPEI},
        )
        if not built.get("ok"):
            raise AssertionError(built)
        cls.normalized = built["data"]["normalized_natal"]

    def forecast(self, target, scopes, **extra):
        payload = {
            "normalized_natal": self.normalized,
            "target": {
                "civil_datetime": target,
                "timezone": "Asia/Taipei",
            },
            "requested_scopes": scopes,
        }
        payload.update(extra)
        return dispatch("resolve_forecast_context", payload)

    def test_yearly_monthly_only_materializes_requested_scopes(self):
        result = self.forecast("2026-09-15T14:30:00", ["yearly", "monthly"])
        self.assertTrue(result["ok"], result)
        data = result["data"]
        self.assertIn("bazi", data)
        self.assertIn("calendar_context_summary", data)
        self.assertEqual(set(data["ziwei"]), {"yearly", "monthly"})
        self.assertNotIn("daily", data["ziwei"])
        self.assertNotIn("hourly", data["ziwei"])
        self.assertNotIn("decadal", data["ziwei"])
        for scope in ("yearly", "monthly"):
            layer = data["ziwei"][scope]
            self.assertEqual(layer["scope"], scope)
            self.assertTrue(layer["reference"])
            self.assertEqual(layer["classification"], "Project 推導盤面")
            self.assertEqual(layer["maturity"], "experimental")
            self.assertEqual(layer["flowing_star_layer"]["classification"], "Project 推導盤面")
            self.assertEqual(layer["flowing_star_layer"]["maturity"], "experimental")
        self.assertEqual(data["provenance"]["target_calendar_resolutions"], 1)
        self.assertNotIn("interpretation", data)
        self.assertNotIn("advice", data)

    def test_yearly_transformations_share_the_yearly_flowing_source(self):
        result = self.forecast("2025-06-15T12:00:00", ["yearly"])
        self.assertTrue(result["ok"], result)
        yearly = result["data"]["ziwei"]["yearly"]
        transform = yearly["transformation_layer"]
        flowing = yearly["flowing_star_layer"]

        self.assertEqual(transform["identity"]["scope"], "yearly")
        self.assertEqual(transform["identity"]["reference"], flowing["source"]["reference"])
        self.assertEqual(transform["source"]["heavenly_stem"], flowing["source"]["heavenly_stem"])
        self.assertEqual(transform["source"]["scope"], "yearly")
        self.assertEqual(len(transform["transformations"]["transformations"]), 4)
        self.assertEqual(len(transform["flying_edges"]), 4)

    def test_yearly_2025_uses_existing_yi_transformation_profile(self):
        result = self.forecast("2025-06-15T12:00:00", ["yearly"])
        self.assertTrue(result["ok"], result)
        rows = result["data"]["ziwei"]["yearly"]["transformation_layer"]["transformations"]["transformations"]
        actual = [(row["type"], row["star"]) for row in rows]
        self.assertEqual(
            actual,
            [("祿", "天機"), ("權", "天梁"), ("科", "紫微"), ("忌", "太陰")],
        )

    def test_evidence_extraction_preserves_forecast_truth_and_is_deterministic(self):
        result = self.forecast(
            "2026-09-15T14:30:00",
            ["yearly", "monthly", "daily", "hourly"],
        )
        self.assertTrue(result["ok"], result)
        context = result["data"]

        before_bytes = canonical_bytes(context)
        before_digest = hashlib.sha256(before_bytes).hexdigest()
        first = build_evidence_features(context, target_scope="yearly")
        after_bytes = canonical_bytes(context)
        after_digest = hashlib.sha256(after_bytes).hexdigest()
        second = build_evidence_features(context, target_scope="yearly")

        self.assertEqual(before_bytes, after_bytes)
        self.assertEqual(before_digest, after_digest)
        self.assertEqual(first["source_context_digest"], before_digest)
        self.assertEqual(canonical_bytes(first), canonical_bytes(second))
        self.assertEqual(
            [feature["feature_id"] for feature in first["features"]],
            [feature["feature_id"] for feature in second["features"]],
        )
        self.assertEqual(
            {feature["scope"] for feature in first["features"]},
            {"decadal", "yearly", "monthly", "daily", "hourly"},
        )
        bazi_decadal = [
            feature
            for feature in first["features"]
            if feature["system"] == "bazi" and feature["scope"] == "decadal"
        ]
        self.assertEqual(len(bazi_decadal), 1)
        self.assertEqual(bazi_decadal[0]["role"], "modifier")
        self.assertFalse(
            any(
                feature["system"] == "ziwei" and feature["scope"] == "decadal"
                for feature in first["features"]
            )
        )

    def test_late_zi_daily_hourly_use_fine_cycle_boundary_while_calendar_stays_neutral(self):
        result = self.forecast("2026-09-15T23:30:00", ["daily", "hourly"])
        self.assertTrue(result["ok"], result)
        data = result["data"]
        calendar = data["calendar_context_summary"]
        self.assertEqual(calendar["normalized_time"]["gregorian_date"], "2026-09-15")
        self.assertFalse(calendar["policies"]["metaphysics_day_boundary_applied"])
        self.assertEqual(calendar["normalized_time"]["hour_branch"], "子")

        daily = data["ziwei"]["daily"]["resolved_cycle"]
        hourly = data["ziwei"]["hourly"]["resolved_cycle"]
        self.assertEqual(daily["civil_date"], "2026-09-15")
        self.assertEqual(daily["effective_date"], "2026-09-16")
        self.assertEqual(hourly["effective_date"], "2026-09-16")
        self.assertIn("late_zi_forward-v1", daily["reference"])
        self.assertIn("late_zi_forward-v1", hourly["reference"])

    def test_fine_cycle_transformations_and_flowing_stars_share_one_resolved_source(self):
        result = self.forecast("2026-09-15T14:30:00", ["monthly", "daily", "hourly"])
        self.assertTrue(result["ok"], result)
        for scope in ("monthly", "daily", "hourly"):
            layer = result["data"]["ziwei"][scope]
            resolved = layer["resolved_cycle"]
            transform = layer["transformation_layer"]
            flowing = layer["flowing_star_layer"]
            self.assertEqual(transform["identity"]["reference"], resolved["reference"])
            self.assertEqual(flowing["source"]["reference"], resolved["reference"])
            self.assertEqual(transform["source"]["heavenly_stem"], resolved["heavenly_stem"])
            self.assertEqual(flowing["source"]["heavenly_stem"], resolved["heavenly_stem"])
            self.assertEqual(flowing["source"]["earthly_branch"], resolved["earthly_branch"])
            self.assertEqual(layer["source_resolution_count"], 1)

    def test_decadal_uses_stored_project_stem_branch_without_recalculation(self):
        project = self.normalized["project"]
        period = next(item for item in project["ziwei"]["decadal_cycles"] if item["index"] == 5)
        result = self.forecast(
            "2026-09-15T14:30:00",
            ["decadal"],
            ziwei_decadal_index=5,
        )
        self.assertTrue(result["ok"], result)
        layer = result["data"]["ziwei"]["decadal"]
        source = layer["flowing_star_layer"]["source"]
        self.assertEqual(source["heavenly_stem"] + source["earthly_branch"], period["stem_branch"])
        self.assertEqual(layer["decadal_period"]["stem_branch"], period["stem_branch"])
        self.assertIn(":5:", layer["reference"])

    def test_blocking_natal_conflict_fails_closed(self):
        blocked = copy.deepcopy(self.normalized)
        blocked["validation"]["blocking_conflict_count"] = 1
        result = dispatch(
            "resolve_forecast_context",
            {
                "normalized_natal": blocked,
                "target": {
                    "civil_datetime": "2026-09-15T14:30:00",
                    "timezone": "Asia/Taipei",
                },
                "requested_scopes": ["yearly"],
            },
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "forecast_basis_blocked")
        self.assertEqual(result["error"]["details"]["reason"], "blocking_natal_conflict")

    def test_missing_project_ziwei_facts_fails_closed(self):
        missing = copy.deepcopy(self.normalized)
        missing["project"]["ziwei"] = {}
        result = dispatch(
            "resolve_forecast_context",
            {
                "normalized_natal": missing,
                "target": {
                    "civil_datetime": "2026-09-15T14:30:00",
                    "timezone": "Asia/Taipei",
                },
                "requested_scopes": ["monthly"],
            },
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "forecast_basis_blocked")
        self.assertEqual(result["error"]["details"]["reason"], "missing_project_ziwei_facts")

    def test_decadal_scope_requires_explicit_index(self):
        result = self.forecast("2026-09-15T14:30:00", ["decadal"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "missing_decadal_index")


if __name__ == "__main__":
    unittest.main()
