from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


# Existing verified-event oracle. This file is intentionally separate from the
# prediction generator so historical outcomes cannot influence evidence formation.
ORACLE = {
    "case-2016": {
        "timing": "scorable",
        "truth": [
            "跨國考察/移動",
            "朋友合作創業",
            "合作爭執終止",
            "重新進入職場/新部門",
        ],
        "components": [
            ("mobility_external", "movement_external"),
            ("peers", "peer_relations|peer_alignment"),
            ("peers", "pressure_or_friction|friction_or_change"),
            ("career", "career_role"),
        ],
    },
    "case-2018": {
        "timing": "boundary_ambiguous",
        "truth": ["女友搬入家中", "開始規劃結婚"],
        "components": [
            ("home_property", "home_property|movement_or_change"),
            ("partnership", "close_partnership"),
        ],
    },
    "case-2019": {
        "timing": "scorable",
        "truth": ["約10–11月結婚"],
        "components": [("partnership", "close_partnership")],
    },
    "case-2020": {
        "timing": "scorable",
        "truth": [
            "未確認重要關係/合作衝突",
            "未確認工作生活節奏重大重整",
        ],
        "components": [],
        "known_absent_directions": [
            ("partnership", "close_partnership"),
            ("career", "career_role"),
        ],
    },
    "case-2021": {
        "timing": "scorable",
        "truth": ["9月兒子出生", "11月轉職新公司", "薪資增加約34%"],
        "components": [
            ("children_creation", "children_creation"),
            ("career", "career_role"),
            ("finance", "earned_income"),
        ],
    },
    "case-2023": {
        "timing": "scorable",
        "truth": ["購買房屋", "約10月交屋入住"],
        "components": [
            ("home_property", "home_property"),
            ("finance", "income_assets"),
        ],
    },
    "case-2024": {
        "timing": "boundary_ambiguous",
        "truth": ["年初公司裁員", "小組4人縮為2人"],
        "components": [
            ("career", "career_role"),
            ("career", "downsizing|adverse_change"),
        ],
    },
    "case-2025": {
        "timing": "scorable",
        "truth": ["3月上半月額外年終獎金"],
        "components": [("finance", "earned_income|income_assets")],
    },
    "case-2026": {
        "timing": "scorable",
        "truth": [
            "3月升經理",
            "4月額外年終",
            "4月拔牙補骨",
            "約4月合作邀約",
            "5月福岡旅行",
            "父親土地掛售中",
        ],
        "components": [
            ("career", "career_role"),
            ("finance", "earned_income|income_assets"),
            ("health", "health_load"),
            ("partnership", "close_partnership"),
            ("mobility_external", "movement_external"),
            ("home_property", "home_property"),
        ],
    },
}


def canonical_bytes(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def arm_keys(arm):
    return {
        (row["primary_domain"], row["event_family"])
        for row in arm["opened_children"]
    }


def component_supported(keys, domain, expression):
    return any((domain, family) in keys for family in expression.split("|"))


def positive_status(checks, timing):
    total = len(checks)
    supported = sum(1 for row in checks if row["supported"])
    if total == 0:
        return "NO_POSITIVE_COMPONENTS"
    if supported == 0:
        return "MISS_CORE_FAMILY"
    if supported == total:
        return (
            "MATCH_COMPONENT_COVERAGE_BOUNDARY_AMBIGUOUS"
            if timing == "boundary_ambiguous"
            else "MATCH_AT_EVENT_FAMILY_COVERAGE"
        )
    return (
        "PARTIAL_BOUNDARY_AMBIGUOUS"
        if timing == "boundary_ambiguous"
        else "PARTIAL"
    )


def checks_for(keys, components):
    rows = []
    for domain, expression in components:
        rows.append(
            {
                "primary_domain": domain,
                "expected_family_expression": expression,
                "supported": component_supported(keys, domain, expression),
            }
        )
    return rows


def classify_new_child(key, oracle):
    domain, family = key
    for expected_domain, expression in oracle.get("components", []):
        if domain == expected_domain and family in expression.split("|"):
            return "SUPPORTS_VERIFIED_COMPONENT"
    for absent_domain, absent_family in oracle.get("known_absent_directions", []):
        if key == (absent_domain, absent_family):
            return "KNOWN_CONTROL_CONFLICT"
    return "INDETERMINATE_NO_COMPLETE_OUTCOME_CENSUS"


def main(path):
    predictions = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = []
    aggregate = {
        "positive_component_support_baseline": 0,
        "positive_component_support_candidate": 0,
        "positive_component_total": 0,
        "known_control_conflicts_baseline": 0,
        "known_control_conflicts_candidate": 0,
        "new_children_total": 0,
        "new_children_supporting_verified_components": 0,
        "new_children_known_control_conflicts": 0,
        "new_children_indeterminate": 0,
    }

    for prediction in predictions["cases"]:
        case_id = prediction["case_id"]
        oracle = ORACLE[case_id]
        baseline_keys = arm_keys(prediction["baseline"])
        candidate_keys = arm_keys(prediction["candidate"])

        baseline_checks = checks_for(baseline_keys, oracle.get("components", []))
        candidate_checks = checks_for(candidate_keys, oracle.get("components", []))
        baseline_status = positive_status(baseline_checks, oracle["timing"])
        candidate_status = positive_status(candidate_checks, oracle["timing"])

        known_absent = oracle.get("known_absent_directions", [])
        baseline_conflicts = [
            {"primary_domain": domain, "event_family": family}
            for domain, family in known_absent
            if (domain, family) in baseline_keys
        ]
        candidate_conflicts = [
            {"primary_domain": domain, "event_family": family}
            for domain, family in known_absent
            if (domain, family) in candidate_keys
        ]

        new_children = []
        for child in prediction["new_children"]:
            key = (child["primary_domain"], child["event_family"])
            classification = classify_new_child(key, oracle)
            new_children.append({**child, "outcome_classification": classification})
            aggregate["new_children_total"] += 1
            if classification == "SUPPORTS_VERIFIED_COMPONENT":
                aggregate["new_children_supporting_verified_components"] += 1
            elif classification == "KNOWN_CONTROL_CONFLICT":
                aggregate["new_children_known_control_conflicts"] += 1
            else:
                aggregate["new_children_indeterminate"] += 1

        aggregate["positive_component_support_baseline"] += sum(
            1 for row in baseline_checks if row["supported"]
        )
        aggregate["positive_component_support_candidate"] += sum(
            1 for row in candidate_checks if row["supported"]
        )
        aggregate["positive_component_total"] += len(candidate_checks)
        aggregate["known_control_conflicts_baseline"] += len(baseline_conflicts)
        aggregate["known_control_conflicts_candidate"] += len(candidate_conflicts)

        rows.append(
            {
                "case_id": case_id,
                "timing": oracle["timing"],
                "truth": oracle["truth"],
                "baseline_status": (
                    "KNOWN_WRONG_DIRECTIONS_PRESENT"
                    if known_absent and baseline_conflicts
                    else baseline_status
                ),
                "candidate_status": (
                    "KNOWN_WRONG_DIRECTIONS_PRESENT"
                    if known_absent and candidate_conflicts
                    else candidate_status
                ),
                "baseline_component_checks": baseline_checks,
                "candidate_component_checks": candidate_checks,
                "baseline_known_control_conflicts": baseline_conflicts,
                "candidate_known_control_conflicts": candidate_conflicts,
                "new_children": new_children,
                "removed_children": prediction["removed_children"],
            }
        )

    aggregate["positive_component_support_delta"] = (
        aggregate["positive_component_support_candidate"]
        - aggregate["positive_component_support_baseline"]
    )
    aggregate["known_control_conflict_delta"] = (
        aggregate["known_control_conflicts_candidate"]
        - aggregate["known_control_conflicts_baseline"]
    )

    payload = {
        "schema": "v1.6-yearly-transformations-retrospective-adjudication.v1",
        "research_status": "RETROSPECTIVE_RESEARCH_ONLY",
        "promotion_allowed": False,
        "official_paired_scoring": False,
        "prediction_digest": predictions["prediction_digest"],
        "case_count": len(rows),
        "cases": rows,
        "aggregate": aggregate,
        "interpretation_guardrails": [
            "Positive component support is retrospective family-level coverage, not prospective prediction accuracy.",
            "New children are not labeled false positives from silence; absent a complete outcome census they remain indeterminate.",
            "2020 uses only the already-recorded negative-control directions and does not generalize absence to all other children.",
            "Boundary-ambiguous 2018 and 2024 cases are not clean annual timing scores.",
        ],
    }
    payload["adjudication_digest"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python tools/v16_yearly_transformations_benchmark_adjudicate.py PREDICTIONS.json")
    main(sys.argv[1])
