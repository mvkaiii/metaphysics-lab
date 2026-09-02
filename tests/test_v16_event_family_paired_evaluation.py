import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from engine.distribution.event_family_paired_evaluation import (
    PAIRED_INPUT_SCHEMA,
    PAIRED_REPORT_SCHEMA,
    evaluate_event_family_paired_comparison,
)
from engine.distribution.event_family_paired_oracle import seal_event_family_paired_oracle


FIXTURE = Path("tests/fixtures/v1.6-event-family-paired-evaluation.synthetic.v1.json")
CLI = Path("tools/evaluate_v16_event_family_paired.py")


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def rendered_bytes(value):
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def load_payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def shared_universe(payload):
    rows = payload["cases"][0]["legacy_adapter_bundle"]["children"]
    return sorted(
        [
            {
                "child_claim_id": row["child_claim_id"],
                "primary_domain": row["primary_domain"],
                "event_family": row["event_family"],
            }
            for row in rows
        ],
        key=lambda row: row["child_claim_id"],
    )


def refresh_payload(payload):
    for oracle_case in payload["oracle"]["cases"]:
        oracle_case["child_outcomes"] = sorted(
            oracle_case["child_outcomes"], key=lambda row: row["child_claim_id"]
        )
        body = {
            "case_id": oracle_case["case_id"],
            "target_scope": oracle_case["target_scope"],
            "child_outcomes": oracle_case["child_outcomes"],
        }
        oracle_case["case_digest"] = digest(body)

    payload["oracle_seal_receipt"] = seal_event_family_paired_oracle(
        oracle=payload["oracle"],
        shared_child_universe=shared_universe(payload),
    )

    for case in payload["cases"]:
        legacy = case["legacy_adapter_bundle"]
        legacy_body = dict(legacy)
        legacy_body.pop("legacy_adapter_digest", None)
        legacy["legacy_adapter_digest"] = digest(legacy_body)

        hoc = case["candidate_hoc_bundle"]
        hoc_body = dict(hoc)
        hoc_body.pop("hybrid_output_contract_digest", None)
        hoc["hybrid_output_contract_digest"] = digest(hoc_body)

        case_body = {
            "case_id": case["case_id"],
            "legacy_adapter_bundle": legacy,
            "candidate_hoc_bundle": hoc,
        }
        case["input_digest"] = digest(case_body)
    return payload


def candidate_child(hoc, child_id):
    for row in hoc["children"] + hoc["audit_only_children"]:
        if row["child_claim_id"] == child_id:
            return row
    raise AssertionError("missing candidate child")


def set_candidate_rendered(hoc, child_id, rendered):
    ordinary = hoc["children"]
    audit = hoc["audit_only_children"]
    row = candidate_child(hoc, child_id)
    hoc["render_units"] = [
        unit
        for unit in hoc["render_units"]
        if child_id not in unit["member_child_claim_ids"]
    ]
    ordinary[:] = [item for item in ordinary if item["child_claim_id"] != child_id]
    audit[:] = [item for item in audit if item["child_claim_id"] != child_id]
    if rendered:
        row["authority_decision"] = "render"
        row["visibility"] = "primary"
        row["authorized_specificity"] = "concrete_event"
        row["cross_system_relation"] = "direct_convergence"
        row["required_caveats"] = []
        ordinary.append(row)
        hoc["render_units"].append(
            {
                "render_unit_id": "render-unit:%s" % child_id.rsplit(":", 1)[-1],
                "member_child_claim_ids": [child_id],
                "primary_domain": row["primary_domain"],
                "target_scope": hoc["target_scope"],
                "composition_type": "direct_convergence_child",
                "cross_system_relations": ["direct_convergence"],
                "visibility": "primary",
                "authorized_specificity": "concrete_event",
                "required_caveats": [],
                "causality_allowed": False,
                "source_efa_digest": "e" * 64,
                "source_c2_digest": "c" * 64,
                "source_hcc_digest": hoc["source_hybrid_claim_composer_digest"],
            }
        )
    else:
        row["authority_decision"] = "abstain_child"
        row["visibility"] = "audit_only"
        row["authorized_specificity"] = None
        row["cross_system_relation"] = None
        row["required_caveats"] = []
        audit.append(row)


class EventFamilyPairedEvaluationTests(unittest.TestCase):
    def test_synthetic_comparison_reports_aggregate_pareto_improvement(self):
        payload = load_payload()
        report = evaluate_event_family_paired_comparison(payload)

        self.assertEqual(payload["schema_version"], PAIRED_INPUT_SCHEMA)
        self.assertEqual(report["schema_version"], PAIRED_REPORT_SCHEMA)
        self.assertEqual(report["case_count"], 1)
        self.assertEqual(report["scored_child_count"], 3)
        self.assertEqual(report["indeterminate_child_count"], 0)
        self.assertEqual(
            report["legacy_metrics"],
            {
                "supported_child_hit_count": 2,
                "supported_child_miss_count": 0,
                "unsupported_child_render_count": 1,
                "specificity_overreach_count": 1,
                "caveat_error_count": 1,
                "false_convergence_count": 2,
            },
        )
        self.assertEqual(
            report["candidate_metrics"],
            {
                "supported_child_hit_count": 2,
                "supported_child_miss_count": 0,
                "unsupported_child_render_count": 0,
                "specificity_overreach_count": 0,
                "caveat_error_count": 0,
                "false_convergence_count": 0,
            },
        )
        self.assertEqual(report["research_label"], "PARETO_IMPROVEMENT_EVIDENCE")
        self.assertFalse(report["promotion_allowed"])
        serialized = json.dumps(report, ensure_ascii=False)
        for forbidden in ("synthetic-paired-001", "child:yearly", "career", "role_change"):
            self.assertNotIn(forbidden, serialized)

    def test_arm_child_universes_must_exactly_match_oracle(self):
        payload = load_payload()
        hoc = payload["cases"][0]["candidate_hoc_bundle"]
        hoc["audit_only_children"] = []
        refresh_payload(payload)
        with self.assertRaises(ValueError):
            evaluate_event_family_paired_comparison(payload)

    def test_indeterminate_outcome_is_excluded_from_accuracy_denominators(self):
        payload = load_payload()
        outcome = next(
            row
            for row in payload["oracle"]["cases"][0]["child_outcomes"]
            if row["event_family"] == "income_change"
        )
        outcome["outcome_status"] = "indeterminate"
        refresh_payload(payload)
        report = evaluate_event_family_paired_comparison(payload)
        self.assertEqual(report["scored_child_count"], 2)
        self.assertEqual(report["indeterminate_child_count"], 1)
        self.assertEqual(report["legacy_metrics"]["unsupported_child_render_count"], 0)

    def test_all_four_research_labels_are_reachable_without_private_semantics(self):
        self.assertEqual(
            evaluate_event_family_paired_comparison(load_payload())["research_label"],
            "PARETO_IMPROVEMENT_EVIDENCE",
        )

        tradeoff = load_payload()
        set_candidate_rendered(
            tradeoff["cases"][0]["candidate_hoc_bundle"],
            "child:yearly:career:leadership_change",
            False,
        )
        refresh_payload(tradeoff)
        self.assertEqual(
            evaluate_event_family_paired_comparison(tradeoff)["research_label"],
            "TRADEOFF",
        )

        equal = load_payload()
        for outcome in equal["oracle"]["cases"][0]["child_outcomes"]:
            outcome["expected_cross_system_relation"] = "direct_convergence"
            outcome["caveat_required"] = False
            if outcome["outcome_status"] == "supported":
                outcome["maximum_supported_specificity"] = "concrete_event"
        legacy_rows = equal["cases"][0]["legacy_adapter_bundle"]["children"]
        income_legacy = next(row for row in legacy_rows if row["event_family"] == "income_change")
        income_legacy["decision"] = "abstain_child"
        income_legacy["authorized_specificity"] = None
        income_legacy["caveat_required"] = False
        hoc = equal["cases"][0]["candidate_hoc_bundle"]
        set_candidate_rendered(hoc, "child:yearly:career:role_change", True)
        refresh_payload(equal)
        self.assertEqual(
            evaluate_event_family_paired_comparison(equal)["research_label"],
            "NON_INFERIOR_NO_STRICT_GAIN",
        )

        regression = copy.deepcopy(equal)
        set_candidate_rendered(
            regression["cases"][0]["candidate_hoc_bundle"],
            "child:yearly:career:role_change",
            False,
        )
        refresh_payload(regression)
        self.assertEqual(
            evaluate_event_family_paired_comparison(regression)["research_label"],
            "REGRESSION",
        )

    def test_input_and_source_digest_tampering_fail_closed(self):
        payload = load_payload()
        payload["cases"][0]["legacy_adapter_bundle"]["children"][0][
            "caveat_required"
        ] = True
        with self.assertRaises(ValueError):
            evaluate_event_family_paired_comparison(payload)

        payload = load_payload()
        payload["cases"][0]["input_digest"] = "0" * 64
        with self.assertRaises(ValueError):
            evaluate_event_family_paired_comparison(payload)

    def test_evaluation_cli_matches_api_and_is_byte_deterministic(self):
        expected = rendered_bytes(
            evaluate_event_family_paired_comparison(load_payload())
        )
        first = subprocess.run(
            [sys.executable, str(CLI), "--input", str(FIXTURE)],
            check=False,
            capture_output=True,
        )
        second = subprocess.run(
            [sys.executable, str(CLI), "--input", str(FIXTURE)],
            check=False,
            capture_output=True,
        )
        self.assertEqual(first.returncode, 0, first.stderr.decode("utf-8"))
        self.assertEqual(second.returncode, 0, second.stderr.decode("utf-8"))
        self.assertEqual(first.stdout, expected)
        self.assertEqual(second.stdout, expected)

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "--input",
                    str(FIXTURE),
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
            self.assertEqual(result.stdout, b"")
            self.assertEqual(output.read_bytes(), expected)


if __name__ == "__main__":
    unittest.main()
