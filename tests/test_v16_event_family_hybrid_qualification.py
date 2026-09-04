from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from engine.distribution.event_family_hybrid_qualification import (
    INPUT_SCHEMA,
    NEGATIVE_COUNTER_FIELDS,
    REPORT_SCHEMA,
    evaluate_event_family_hybrid_qualification,
    validate_event_family_hybrid_qualification_input,
)


FIXTURE = Path(__file__).parent / "fixtures" / "v1.6-event-family-hybrid-qualification.synthetic.v1.json"
EXPECTED_INPUT_SCHEMA = "v1.6-event-family-hybrid-qualification-input.v1"
EXPECTED_REPORT_SCHEMA = "v1.6-event-family-hybrid-qualification-report.v1"
EXPECTED_NEGATIVE_COUNTERS = (
    "supported_child_miss_count",
    "unsupported_child_open_count",
    "role_scope_attribution_error_count",
    "provenance_loss_count",
    "over_render_count",
    "under_render_count",
    "specificity_overreach_count",
    "specificity_excessive_downgrade_count",
    "caveat_omission_count",
    "unnecessary_caveat_count",
    "false_convergence_count",
    "missed_convergence_count",
    "parallel_group_error_count",
    "divergence_erasure_count",
    "false_divergence_count",
    "false_absence_penalty_count",
    "visibility_loss_count",
    "unauthorized_render_unit_count",
    "audit_leak_count",
    "manifest_specificity_overreach_count",
    "required_caveat_manifest_omission_count",
    "unsupported_causality_authority_count",
    "identity_mismatch_count",
    "source_digest_failure_count",
    "determinism_failure_count",
    "cutoff_contamination_count",
)


def canonical_digest(value):
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def refresh_case(case):
    case.pop("input_digest", None)
    case["input_digest"] = canonical_digest(case)


def refresh_hoc(case):
    hoc = case["hoc_bundle"]
    hoc.pop("hybrid_output_contract_digest", None)
    hoc["hybrid_output_contract_digest"] = canonical_digest(hoc)
    receipt = case["determinism_receipt"]
    receipt["first_hoc_digest"] = hoc["hybrid_output_contract_digest"]
    receipt["second_hoc_digest"] = hoc["hybrid_output_contract_digest"]
    refresh_case(case)


def case_by_id(payload, case_id):
    return next(row for row in payload["cases"] if row["case_id"] == case_id)


def expectation_by_family(case, family):
    suffix = ":" + family
    return next(row for row in case["child_expectations"] if row["child_claim_id"].endswith(suffix))


def hcc_child_by_family(case, family):
    return next(row for row in case["hcc_bundle"]["children"] if row["event_family"] == family)


def hoc_unit_for_child(case, child_id):
    return next(row for row in case["hoc_bundle"]["render_units"] if child_id in row["member_child_claim_ids"])


class EventFamilyHybridQualificationQ2Tests(unittest.TestCase):
    def test_public_schema_and_counter_names_are_frozen(self):
        self.assertEqual(INPUT_SCHEMA, EXPECTED_INPUT_SCHEMA)
        self.assertEqual(REPORT_SCHEMA, EXPECTED_REPORT_SCHEMA)
        self.assertEqual(tuple(NEGATIVE_COUNTER_FIELDS), EXPECTED_NEGATIVE_COUNTERS)

    def test_baseline_synthetic_matrix_passes_without_promotion(self):
        payload = load_fixture()
        validated = validate_event_family_hybrid_qualification_input(payload)
        self.assertEqual(validated, payload)

        report = evaluate_event_family_hybrid_qualification(payload)
        self.assertEqual(report["schema_version"], REPORT_SCHEMA)
        self.assertEqual(report["classification"], "synthetic_validation")
        self.assertEqual(report["case_count"], len(payload["cases"]))
        self.assertEqual(
            report["child_count"],
            sum(len(row["child_expectations"]) for row in payload["cases"]),
        )
        self.assertEqual(report["general_conformance_status"], "PASS")
        self.assertIs(report["promotion_allowed"], False)
        for field in EXPECTED_NEGATIVE_COUNTERS:
            self.assertEqual(report[field], 0, field)
        self.assertEqual(report["decision_alignment"]["partial"], 0)
        self.assertEqual(report["decision_alignment"]["missed"], 0)
        self.assertEqual(len(report["input_set_digest"]), 64)
        self.assertEqual(len(report["report_digest"]), 64)

    def test_semantic_mutations_raise_the_expected_negative_counters(self):
        def run(mutator):
            payload = load_fixture()
            mutator(payload)
            return evaluate_event_family_hybrid_qualification(payload)

        mutations = {}

        def supported_child_miss(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            row = expectation_by_family(case, "modifier_only")
            row.update({
                "expected_opened": True,
                "expected_direct_target_systems": ["bazi"],
                "expected_direct_target_dependency_families": ["dep:expected"],
                "expected_authorization": "render_with_caveat",
                "minimum_acceptable_specificity": "event_family",
                "maximum_specificity": "event_family",
                "caveat_required": True,
                "expected_cross_system_relation": "single_system_qualified",
                "expected_visibility": "primary",
                "expected_in_render_manifest": True,
            })
            refresh_case(case)
        mutations["supported_child_miss_count"] = supported_child_miss
        mutations["under_render_count"] = supported_child_miss

        def unsupported_open(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            row = expectation_by_family(case, "leadership_change")
            row.update({
                "expected_opened": False,
                "expected_direct_target_systems": [],
                "expected_direct_target_dependency_families": [],
                "expected_authorization": "abstain_child",
                "minimum_acceptable_specificity": None,
                "maximum_specificity": None,
                "caveat_required": False,
                "expected_cross_system_relation": None,
                "expected_visibility": "audit_only",
                "expected_in_render_manifest": False,
            })
            refresh_case(case)
        mutations["unsupported_child_open_count"] = unsupported_open
        mutations["over_render_count"] = unsupported_open
        mutations["unauthorized_render_unit_count"] = unsupported_open

        def attribution(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            row = expectation_by_family(case, "leadership_change")
            row["expected_direct_target_systems"] = ["ziwei"]
            refresh_case(case)
        mutations["role_scope_attribution_error_count"] = attribution

        def provenance(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            row = expectation_by_family(case, "leadership_change")
            row["expected_direct_target_dependency_families"] = ["dep:missing"]
            refresh_case(case)
        mutations["provenance_loss_count"] = provenance

        def specificity_over(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            row = expectation_by_family(case, "role_change")
            row["maximum_specificity"] = "event_family"
            row["minimum_acceptable_specificity"] = "event_family"
            refresh_case(case)
        mutations["specificity_overreach_count"] = specificity_over

        def specificity_down(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            row = expectation_by_family(case, "leadership_change")
            row["minimum_acceptable_specificity"] = "concrete_event"
            row["maximum_specificity"] = "concrete_event"
            refresh_case(case)
        mutations["specificity_excessive_downgrade_count"] = specificity_down

        def caveat_omission(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            expectation_by_family(case, "role_change")["caveat_required"] = True
            refresh_case(case)
        mutations["caveat_omission_count"] = caveat_omission

        def unnecessary_caveat(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            row = expectation_by_family(case, "leadership_change")
            row["expected_authorization"] = "render"
            row["caveat_required"] = False
            refresh_case(case)
        mutations["unnecessary_caveat_count"] = unnecessary_caveat

        def false_convergence(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            expectation_by_family(case, "role_change")["expected_cross_system_relation"] = "single_system_qualified"
            refresh_case(case)
        mutations["false_convergence_count"] = false_convergence

        def missed_convergence(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            expectation_by_family(case, "leadership_change")["expected_cross_system_relation"] = "direct_convergence"
            refresh_case(case)
        mutations["missed_convergence_count"] = missed_convergence

        def parallel_group(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            case["composition_expectations"][0]["member_child_claim_ids"] = case["composition_expectations"][0]["member_child_claim_ids"][:-1]
            refresh_case(case)
        mutations["parallel_group_error_count"] = parallel_group

        def divergence_erasure(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            expectation_by_family(case, "leadership_change")["expected_cross_system_relation"] = "divergence"
            refresh_case(case)
        mutations["divergence_erasure_count"] = divergence_erasure

        def false_divergence(payload):
            case = case_by_id(payload, "Q2-D-explicit-divergence")
            expectation_by_family(case, "role_change")["expected_cross_system_relation"] = "single_system_qualified"
            refresh_case(case)
        mutations["false_divergence_count"] = false_divergence

        def absence_penalty(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            child_id = expectation_by_family(case, "modifier_only")["child_claim_id"]
            case["absence_policy_cases"].append({
                "child_claim_id": child_id,
                "materialized_system": "bazi",
                "missing_system": "ziwei",
                "expected_authorization": "render_with_caveat",
                "expected_relation": "single_system_qualified",
            })
            refresh_case(case)
        mutations["false_absence_penalty_count"] = absence_penalty

        def visibility(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            expectation_by_family(case, "leadership_change")["expected_visibility"] = "secondary"
            refresh_case(case)
        mutations["visibility_loss_count"] = visibility

        def audit_leak(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            hoc = case["hoc_bundle"]
            child = hoc["children"].pop(0)
            hoc["audit_only_children"].append(child)
            refresh_hoc(case)
        mutations["audit_leak_count"] = audit_leak

        def manifest_specificity(payload):
            case = case_by_id(payload, "Q2-B-layered-secondary-absence")
            hoc = case["hoc_bundle"]
            hoc["render_units"][0]["authorized_specificity"] = "concrete_event"
            refresh_hoc(case)
        mutations["manifest_specificity_overreach_count"] = manifest_specificity

        def manifest_caveat(payload):
            case = case_by_id(payload, "Q2-B-layered-secondary-absence")
            hoc = case["hoc_bundle"]
            hoc["render_units"][0]["required_caveats"] = []
            refresh_hoc(case)
        mutations["required_caveat_manifest_omission_count"] = manifest_caveat

        def causality(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            case["hoc_bundle"]["render_units"][0]["causality_allowed"] = True
            refresh_hoc(case)
        mutations["unsupported_causality_authority_count"] = causality

        def identity(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            case["hoc_bundle"]["source_hybrid_claim_composer_digest"] = "f" * 64
            refresh_hoc(case)
        mutations["identity_mismatch_count"] = identity

        def source_digest(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            case["efa_bundle"]["children"][0]["child_opened"] = False
            refresh_case(case)
        mutations["source_digest_failure_count"] = source_digest

        def determinism(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            case["determinism_receipt"]["second_hoc_digest"] = "e" * 64
            refresh_case(case)
        mutations["determinism_failure_count"] = determinism

        def cutoff(payload):
            case = case_by_id(payload, "Q2-A-mixed-primary")
            case["cutoff_contamination"] = True
            refresh_case(case)
        mutations["cutoff_contamination_count"] = cutoff

        for field in EXPECTED_NEGATIVE_COUNTERS:
            with self.subTest(field=field):
                report = run(mutations[field])
                self.assertGreater(report[field], 0)
                self.assertEqual(report["general_conformance_status"], "FAIL")
                self.assertIs(report["promotion_allowed"], False)

    def test_blanket_abstention_cannot_pass_by_silence(self):
        payload = load_fixture()
        for case in payload["cases"]:
            for row in case["child_expectations"]:
                if row["expected_authorization"] in {"render", "render_with_caveat"}:
                    row.update({
                        "expected_opened": True,
                        "expected_authorization": "render_with_caveat",
                        "minimum_acceptable_specificity": "event_family",
                        "maximum_specificity": row["maximum_specificity"] or "event_family",
                        "caveat_required": True,
                        "expected_in_render_manifest": True,
                    })
            for decision in case["c2_bundle"]["decisions"]:
                decision["decision"] = "abstain_child"
                decision["authorized_specificity"] = None
            c2 = case["c2_bundle"]
            c2.pop("hierarchical_claim_authority_digest", None)
            c2["hierarchical_claim_authority_digest"] = canonical_digest(c2)
            refresh_case(case)
        report = evaluate_event_family_hybrid_qualification(payload)
        self.assertTrue(report["supported_child_miss_count"] > 0 or report["under_render_count"] > 0)
        self.assertEqual(report["general_conformance_status"], "FAIL")

    def test_unknown_and_private_fields_fail_closed_at_every_public_layer(self):
        mutations = []
        payload = load_fixture(); payload["subject_name"] = "forbidden"; mutations.append(payload)
        payload = load_fixture(); payload["cases"][0]["birth_date"] = "2000-01-01"; mutations.append(payload)
        payload = load_fixture(); payload["cases"][0]["child_expectations"][0]["actual_event"] = "forbidden"; mutations.append(payload)
        payload = load_fixture(); payload["cases"][0]["efa_bundle"]["notes"] = "forbidden"; mutations.append(payload)
        for payload in mutations:
            with self.subTest(keys=list(payload.keys())):
                with self.assertRaises(ValueError):
                    validate_event_family_hybrid_qualification_input(payload)

    def test_input_digest_mismatch_is_validation_error_not_a_scored_case(self):
        payload = load_fixture()
        payload["cases"][0]["input_digest"] = "0" * 64
        with self.assertRaises(ValueError):
            validate_event_family_hybrid_qualification_input(payload)

    def test_private_enum_is_metrics_only_and_never_promotable(self):
        payload = load_fixture()
        payload["classification"] = "private_external_evaluation"
        report = evaluate_event_family_hybrid_qualification(payload)
        self.assertEqual(report["general_conformance_status"], "METRICS_ONLY")
        self.assertIs(report["promotion_allowed"], False)


if __name__ == "__main__":
    unittest.main()
