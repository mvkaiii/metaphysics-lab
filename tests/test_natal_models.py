import unittest
from dataclasses import FrozenInstanceError

from engine.natal.errors import NatalFoundationError
from engine.natal.models import (
    ExternalNatalView,
    NatalSource,
    NormalizedNatalChart,
    ProjectNatalView,
    ResolvedField,
    ResolvedNatalView,
    SourcedValue,
)


class NatalModelTests(unittest.TestCase):
    def setUp(self):
        self.external_source = NatalSource(
            source_type="external",
            source_name="Astralium",
            source_version="public-example",
            rule_profile="astralium-imported",
            rule_version="unknown",
            maturity="external",
            validation_status="provided",
        )
        self.project_source = NatalSource(
            source_type="project",
            source_name="Metaphysics Lab",
            source_version="2C0-exp",
            rule_profile="ziwei-natal-true-solar-common-v1",
            rule_version="1.0-exp",
            maturity="experimental",
            validation_status="qualified_candidate",
        )

    def test_normalized_model_keeps_external_and_project_values_separate(self):
        external = SourcedValue("巳", self.external_source)
        project = SourcedValue("午", self.project_source)
        field = ResolvedField(
            path="ziwei.ming_palace",
            status="CONFLICT",
            severity="BLOCKING",
            selected_source="external",
            selected_value="巳",
            external_value=external,
            project_value=project,
            reason="project_engine_experimental",
        )
        self.assertEqual(field.external_value.value, "巳")
        self.assertEqual(field.project_value.value, "午")
        self.assertEqual(field.selected_value, "巳")

    def test_views_freeze_nested_mappings_without_mutating_source_input(self):
        birth = {"reported_datetime": "1984-03-13T19:20:00+08:00"}
        bazi = {"pillars": {"year": "甲子"}}
        ziwei = {"ming_palace": "巳"}
        external = ExternalNatalView(birth=birth, bazi=bazi, ziwei=ziwei, source=self.external_source)
        birth["reported_datetime"] = "changed"
        bazi["pillars"]["year"] = "changed"
        ziwei["ming_palace"] = "changed"
        self.assertEqual(external.birth["reported_datetime"], "1984-03-13T19:20:00+08:00")
        self.assertEqual(external.bazi["pillars"]["year"], "甲子")
        self.assertEqual(external.ziwei["ming_palace"], "巳")
        with self.assertRaises(TypeError):
            external.birth["x"] = "y"
        with self.assertRaises(TypeError):
            external.bazi["pillars"]["year"] = "乙丑"

    def test_project_view_preserves_time_basis_as_separate_layer(self):
        view = ProjectNatalView(
            birth={"reported_datetime": "1984-03-13T19:20:00+08:00"},
            time_basis={"effective_time_basis": "true_solar", "effective_hour_branch": "戌"},
            bazi={"pillars": {"day": "丙辰"}},
            ziwei={"ming_palace": "巳"},
            source=self.project_source,
        )
        self.assertEqual(view.time_basis["effective_time_basis"], "true_solar")
        self.assertEqual(view.birth["reported_datetime"], "1984-03-13T19:20:00+08:00")

    def test_resolved_field_rejects_unknown_status_severity_and_selection(self):
        external = SourcedValue("巳", self.external_source)
        project = SourcedValue("午", self.project_source)
        for kwargs in (
            {"status": "MAYBE", "severity": "INFO", "selected_source": "external"},
            {"status": "MATCH", "severity": "DANGER", "selected_source": "external"},
            {"status": "MATCH", "severity": "INFO", "selected_source": "mystery"},
        ):
            with self.assertRaises(NatalFoundationError) as caught:
                ResolvedField(
                    path="ziwei.ming_palace",
                    selected_value="巳",
                    external_value=external,
                    project_value=project,
                    reason="test",
                    **kwargs,
                )
            self.assertEqual(caught.exception.code, "invalid_natal_model")

    def test_selected_source_must_have_matching_sourced_value(self):
        project = SourcedValue("午", self.project_source)
        with self.assertRaises(NatalFoundationError):
            ResolvedField(
                path="ziwei.ming_palace",
                status="NOT_COMPARABLE",
                severity="INFO",
                selected_source="external",
                selected_value=None,
                external_value=None,
                project_value=project,
                reason="external_missing",
            )

    def test_to_dict_preserves_both_raw_views_and_resolved_selection(self):
        external_view = ExternalNatalView(
            birth={"reported_datetime": "1984-03-13T19:20:00+08:00"},
            bazi={},
            ziwei={"ming_palace": "巳"},
            source=self.external_source,
        )
        project_view = ProjectNatalView(
            birth={"reported_datetime": "1984-03-13T19:20:00+08:00"},
            time_basis={"effective_time_basis": "true_solar"},
            bazi={},
            ziwei={"ming_palace": "午"},
            source=self.project_source,
        )
        resolved = ResolvedNatalView((
            ResolvedField(
                path="ziwei.ming_palace",
                status="CONFLICT",
                severity="BLOCKING",
                selected_source="external",
                selected_value="巳",
                external_value=SourcedValue("巳", self.external_source),
                project_value=SourcedValue("午", self.project_source),
                reason="project_engine_experimental",
            ),
        ))
        chart = NormalizedNatalChart(
            identity="public-synthetic-chart",
            external=external_view,
            project=project_view,
            resolved=resolved,
            validation={"status": "conflict"},
            provenance={"classification": "normalized_natal"},
        )
        payload = chart.to_dict()
        self.assertEqual(payload["external"]["ziwei"]["ming_palace"], "巳")
        self.assertEqual(payload["project"]["ziwei"]["ming_palace"], "午")
        field = payload["resolved"]["fields"][0]
        self.assertEqual(field["selected_source"], "external")
        self.assertEqual(field["selected_value"], "巳")
        self.assertEqual(field["external_value"]["value"], "巳")
        self.assertEqual(field["project_value"]["value"], "午")

    def test_all_models_are_frozen(self):
        source = self.project_source
        value = SourcedValue("巳", source, notes=("note",))
        with self.assertRaises(FrozenInstanceError):
            source.source_name = "changed"
        with self.assertRaises(FrozenInstanceError):
            value.value = "午"


if __name__ == "__main__":
    unittest.main()
