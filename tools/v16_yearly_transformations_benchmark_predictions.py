from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

from engine.distribution.event_family_attribution import build_event_family_attribution_bundle
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

# Frozen before outcome adjudication. These rows contain only temporal identity.
CASES = (
    ("case-2016", "2016-06-15T12:00:00"),
    ("case-2018", "2018-06-15T12:00:00"),
    ("case-2019", "2019-06-15T12:00:00"),
    ("case-2020", "2020-06-15T12:00:00"),
    ("case-2021", "2021-06-15T12:00:00"),
    ("case-2023", "2023-06-15T12:00:00"),
    ("case-2024", "2024-06-15T12:00:00"),
    ("case-2025", "2025-06-15T12:00:00"),
    ("case-2026", "2026-06-15T12:00:00"),
)


def canonical_bytes(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def require_ok(result, label):
    if not result.get("ok"):
        raise RuntimeError(f"{label} failed: {result}")
    return result["data"]


def arm_from_context(context):
    interpreted = require_ok(
        dispatch(
            "interpret_structural_evidence",
            {"forecast_context": context, "target_scope": "yearly"},
        ),
        "interpret_structural_evidence",
    )
    ranked = require_ok(
        dispatch(
            "rank_evidence",
            {"features": interpreted["features"], "target_scope": "yearly"},
        ),
        "rank_evidence",
    )["ranking"]
    efa = build_event_family_attribution_bundle(
        base_ranking=ranked,
        structural_interpretation=interpreted,
    )
    opened = sorted(
        (
            child["primary_domain"],
            child["event_family"],
            tuple(child["direct_target_systems"]),
        )
        for child in efa["children"]
        if child["child_opened"]
    )
    return {
        "interpretation_digest": interpreted["interpretation_digest"],
        "ranking_digest": ranked["ranking_digest"],
        "event_family_attribution_digest": efa["event_family_attribution_digest"],
        "opened_domains": ranked["opened_domains"],
        "opened_children": [
            {
                "primary_domain": domain,
                "event_family": family,
                "direct_target_systems": list(systems),
            }
            for domain, family, systems in opened
        ],
    }


def child_keys(arm):
    return {
        (row["primary_domain"], row["event_family"])
        for row in arm["opened_children"]
    }


def main():
    natal = require_ok(
        dispatch(
            "build_natal",
            {"birth": BIRTH, "resolved_location": RESOLVED_TAIPEI},
        ),
        "build_natal",
    )["normalized_natal"]

    rows = []
    for case_id, target in CASES:
        forecast = require_ok(
            dispatch(
                "resolve_forecast_context",
                {
                    "normalized_natal": natal,
                    "target": {
                        "civil_datetime": target,
                        "timezone": "Asia/Taipei",
                    },
                    "requested_scopes": ["yearly"],
                },
            ),
            f"forecast {case_id}",
        )
        yearly = forecast["ziwei"]["yearly"]
        if "transformation_layer" not in yearly:
            raise RuntimeError(f"candidate yearly transformation layer missing for {case_id}")

        baseline_context = copy.deepcopy(forecast)
        baseline_context["ziwei"]["yearly"].pop("transformation_layer", None)

        baseline = arm_from_context(baseline_context)
        candidate = arm_from_context(forecast)
        baseline_keys = child_keys(baseline)
        candidate_keys = child_keys(candidate)

        transform = yearly["transformation_layer"]
        rows.append(
            {
                "case_id": case_id,
                "target": target,
                "yearly_reference": yearly["reference"],
                "yearly_stem": transform["heavenly_stem"],
                "yearly_transformations": [
                    {
                        "transformation_type": edge["transformation_type"],
                        "star": edge["star"],
                        "target_palace": edge["target_palace"],
                    }
                    for edge in transform["flying_edges"]
                ],
                "baseline": baseline,
                "candidate": candidate,
                "new_children": [
                    {"primary_domain": domain, "event_family": family}
                    for domain, family in sorted(candidate_keys - baseline_keys)
                ],
                "removed_children": [
                    {"primary_domain": domain, "event_family": family}
                    for domain, family in sorted(baseline_keys - candidate_keys)
                ],
            }
        )

    try:
        head_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        head_sha = None

    payload = {
        "schema": "v1.6-yearly-transformations-retrospective-predictions.v1",
        "research_status": "RETROSPECTIVE_RESEARCH_ONLY",
        "promotion_allowed": False,
        "official_paired_scoring": False,
        "branch_head_sha": head_sha,
        "arm_definition": {
            "baseline": "same branch forecast context with yearly transformation_layer removed before structural interpretation",
            "candidate": "same branch actual forecast context with yearly transformation_layer retained",
        },
        "case_count": len(rows),
        "cases": rows,
    }
    digest = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    payload["prediction_digest"] = digest
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    print(text)


if __name__ == "__main__":
    main()
