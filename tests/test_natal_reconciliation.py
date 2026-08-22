import unittest

from engine.birth.reconciliation import ConflictSeverity, ReconciliationStatus
from engine.natal.models import ExternalNatalView, NatalSource, ProjectNatalView, SourcedValue
from engine.natal.reconciliation import compare_scalar, reconcile_natal


class NatalReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.external_source = NatalSource(
            source_type="external",
            source_name="Astralium",
            source_version="synthetic",
            rule_profile="astralium-imported",
            rule_version="unknown",
            maturity="external",
            validation_status="provided",
        )
        self.project_source = NatalSource(
            source_type="project",
            source_name="Metaphysics Lab",
            source_version="2C0-exp",
            rule_profile="natal-foundation-v1",
            rule_version="1.0-exp",
            maturity="experimental",
            validation_status="qualified_candidate",
        )

    def sourced(self, value, source):
        return SourcedValue(value, source)

    def test_status_and_severity_enums_are_fixed_contract(self):
        self.assertEqual([item.value for item in ReconciliationStatus], [
            "MATCH", "EQUIVALENT", "CONFLICT", "NOT_COMPARABLE"
        ])
        self.assertEqual([item.value for item in ConflictSeverity], [
            "INFO", "CAUTION", "BLOCKING"
        ])

    def test_compare_scalar_same_value_is_match(self):
        field = compare_scalar(
            "ziwei.ming_palace",
            self.sourced("巳", self.external_source),
            self.sourced("巳", self.project_source),
        )
        self.assertEqual(field.status, "MATCH")
        self.assertEqual(field.severity, "INFO")
        self.assertEqual(field.selected_value, "巳")
        self.assertEqual(field.reason, "matched")

    def test_time_difference_can_be_materially_equivalent(self):
        field = compare_scalar(
            "birth.effective_time",
            self.sourced("19:20", self.external_source),
            self.sourced("19:16", self.project_source),
            equivalent=lambda external, project: True,
        )
        self.assertEqual(field.status, "EQUIVALENT")
        self.assertEqual(field.severity, "INFO")
        self.assertEqual(field.reason, "materially_equivalent")

    def test_missing_side_is_not_comparable_and_selects_available_value(self):
        field = compare_scalar(
            "ziwei.body_palace",
            None,
            self.sourced("午", self.project_source),
        )
        self.assertEqual(field.status, "NOT_COMPARABLE")
        self.assertEqual(field.severity, "INFO")
        self.assertEqual(field.selected_source, "project")
        self.assertEqual(field.selected_value, "午")

    def test_ming_palace_conflict_is_blocking_but_brightness_is_caution(self):
        ming = compare_scalar(
            "ziwei.ming_palace",
            self.sourced("巳", self.external_source),
            self.sourced("午", self.project_source),
        )
        brightness = compare_scalar(
            "ziwei.stars.紫微.brightness",
            self.sourced("旺", self.external_source),
            self.sourced("廟", self.project_source),
        )
        self.assertEqual((ming.status, ming.severity), ("CONFLICT", "BLOCKING"))
        self.assertEqual((brightness.status, brightness.severity), ("CONFLICT", "CAUTION"))
        self.assertEqual(ming.selected_source, "none")

    def test_blocking_path_matrix_covers_required_core_fields(self):
        paths = (
            "bazi.pillars.year",
            "bazi.pillars.month",
            "bazi.pillars.day",
            "bazi.pillars.hour",
            "birth.effective_hour_branch",
            "ziwei.ming_palace",
            "ziwei.body_palace",
            "ziwei.five_element_bureau",
            "ziwei.major_stars.紫微.palace",
            "ziwei.transformation_required_stars.文曲.palace",
            "ziwei.birth_transformations.祿",
            "bazi.decadal_direction",
            "ziwei.decadal_cycles.1.palace",
        )
        for path in paths:
            with self.subTest(path=path):
                field = compare_scalar(
                    path,
                    self.sourced("A", self.external_source),
                    self.sourced("B", self.project_source),
                )
                self.assertEqual(field.severity, "BLOCKING")

    def test_reconcile_uses_star_identity_not_raw_list_order(self):
        external = ExternalNatalView(
            birth={},
            bazi={},
            ziwei={
                "stars": [
                    {"star": "紫微", "palace": "夫妻", "brightness": "旺"},
                    {"star": "天機", "palace": "命宮", "brightness": "平"},
                ]
            },
            source=self.external_source,
        )
        project = ProjectNatalView(
            birth={},
            time_basis={},
            bazi={},
            ziwei={
                "stars": [
                    {"star": "天機", "palace": "命宮", "brightness": "平"},
                    {"star": "紫微", "palace": "夫妻", "brightness": "旺"},
                ]
            },
            source=self.project_source,
        )
        resolved = reconcile_natal(external, project, project_maturity="experimental")
        by_path = {field.path: field for field in resolved.fields}
        self.assertEqual(by_path["ziwei.stars.紫微.palace"].status, "MATCH")
        self.assertEqual(by_path["ziwei.stars.天機.palace"].status, "MATCH")
        self.assertFalse(any(field.status == "CONFLICT" for field in resolved.fields))

    def test_reconcile_partial_views_emit_not_comparable_instead_of_synthesizing(self):
        external = ExternalNatalView(
            birth={}, bazi={}, ziwei={"ming_palace": "巳"}, source=self.external_source
        )
        project = ProjectNatalView(
            birth={}, time_basis={}, bazi={}, ziwei={"body_palace": "午"}, source=self.project_source
        )
        resolved = reconcile_natal(external, project, project_maturity="experimental")
        by_path = {field.path: field for field in resolved.fields}
        self.assertEqual(by_path["ziwei.ming_palace"].status, "NOT_COMPARABLE")
        self.assertEqual(by_path["ziwei.body_palace"].status, "NOT_COMPARABLE")
        self.assertEqual(by_path["ziwei.ming_palace"].selected_source, "external")
        self.assertEqual(by_path["ziwei.body_palace"].selected_source, "project")


if __name__ == "__main__":
    unittest.main()
