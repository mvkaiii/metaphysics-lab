from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.ziwei.basis import build_palace_stem_index, build_star_location_index
from engine.ziwei.errors import ZiweiPhase2AError
from engine.ziwei.flying import (
    build_natal_flying_graph,
    fly_transformations,
    presentation_relation,
)
from engine.ziwei.models import (
    ChartIdentity,
    CycleStemSource,
    LayerProvenance,
    PalaceStemRecord,
    StarLocationRecord,
)
from engine.ziwei.transformation_profiles import PROFILE_ID, RULE_VERSION
from engine.ziwei.transformations import get_transformation_set

TRANSFORMATION_TYPES = ("祿", "權", "科", "忌")
LEGAL_STEMS = tuple("甲乙丙丁戊己庚辛壬癸")


def _gate(checked, matched):
    return {
        "checked": checked,
        "matched": matched,
        "mismatches": checked - matched,
        "status": "PASS" if matched == checked else "FAIL",
    }


def _multiset_match_count(expected, actual):
    return sum((Counter(expected) & Counter(actual)).values())


def _validate_private_shape(payload):
    required = {
        "source_profile",
        "chart_id",
        "star_locations",
        "palace_stems",
        "natal_expected_edges",
        "decadal",
        "yearly",
        "presentation_expected",
    }
    missing = sorted(required.difference(payload))
    if missing:
        raise ZiweiPhase2AError(
            "qualification_mismatch",
            "private qualification input is missing required fields",
            {"missing": missing},
        )
    if len(payload["natal_expected_edges"]) != 48:
        raise ZiweiPhase2AError(
            "qualification_mismatch",
            "private natal qualification requires exactly 48 expected edges",
            {"count": len(payload["natal_expected_edges"])},
        )
    if len(payload["decadal"].get("expected_edges", ())) != 4:
        raise ZiweiPhase2AError(
            "qualification_mismatch",
            "private decadal qualification requires exactly four expected edges",
        )
    if len(payload["yearly"]) != 7:
        raise ZiweiPhase2AError(
            "qualification_mismatch",
            "private yearly qualification requires exactly seven yearly entries",
            {"count": len(payload["yearly"])},
        )
    for item in payload["yearly"]:
        if len(item.get("expected_edges", ())) != 4:
            raise ZiweiPhase2AError(
                "qualification_mismatch",
                "each private yearly qualification entry requires exactly four expected edges",
                {"reference": item.get("reference")},
            )


def _qualify_external_transformation_profile(payload):
    external_transformations = {}
    for edge in payload["natal_expected_edges"]:
        key = (edge["source_stem"], edge["type"])
        value = edge["star"]
        if key in external_transformations and external_transformations[key] != value:
            raise ZiweiPhase2AError(
                "qualification_mismatch",
                "external source gives conflicting transformation stars",
            )
        external_transformations[key] = value

    required_keys = {
        (stem, transformation_type)
        for stem in LEGAL_STEMS
        for transformation_type in TRANSFORMATION_TYPES
    }
    if set(external_transformations) != required_keys:
        raise ZiweiPhase2AError(
            "qualification_mismatch",
            "external natal edges must cover all ten stems and four transformation types",
            {
                "expected_keys": 40,
                "actual_keys": len(external_transformations),
            },
        )

    matched = 0
    for stem in LEGAL_STEMS:
        result = get_transformation_set(stem)
        for item in result.transformations:
            if external_transformations[(stem, item.type.value)] == item.star:
                matched += 1
    return _gate(40, matched)


def _build_private_basis(payload):
    chart = ChartIdentity(
        payload["chart_id"],
        "natal",
        payload["source_profile"],
    )
    provenance = LayerProvenance(
        "validated_source_fact",
        "Astralium",
        payload["source_profile"],
        None,
        None,
        None,
    )
    star_records = tuple(
        StarLocationRecord(item["star"], item["palace"])
        for item in payload["star_locations"]
    )
    stem_records = tuple(
        PalaceStemRecord(item["palace"], item["heavenly_stem"])
        for item in payload["palace_stems"]
    )
    stars = build_star_location_index(star_records, chart, provenance)
    stems = build_palace_stem_index(stem_records, chart, provenance)
    return chart, stars, stems


def _qualify_natal(payload, stars, stems):
    graph = build_natal_flying_graph(stems, stars)
    expected = [
        (
            edge["source_palace"],
            edge["source_stem"],
            edge["type"],
            edge["star"],
            edge["target_palace"],
        )
        for edge in payload["natal_expected_edges"]
    ]
    actual = [
        (
            edge.source.palace,
            edge.source.heavenly_stem,
            edge.transformation_type.value,
            edge.star,
            edge.target_palace,
        )
        for edge in graph.edges
    ]
    return graph, _gate(48, _multiset_match_count(expected, actual))


def _qualify_cycle(chart, stars, scope, reference, stem, expected_edges):
    source = CycleStemSource("cycle_stem", chart, scope, reference, stem)
    actual_edges = fly_transformations(get_transformation_set(stem), stars, source)
    expected = [
        (edge["type"], edge["star"], edge["target_palace"])
        for edge in expected_edges
    ]
    actual = [
        (edge.transformation_type.value, edge.star, edge.target_palace)
        for edge in actual_edges
    ]
    return _multiset_match_count(expected, actual)


def _qualify_presentation(payload, graph):
    expected = [
        (item["source_palace"], item["type"], item["arrow"])
        for item in payload["presentation_expected"]
    ]
    actual = []
    for edge in graph.edges:
        arrow = presentation_relation(edge)
        if arrow is not None:
            actual.append(
                (edge.source.palace, edge.transformation_type.value, arrow)
            )
    matched = _multiset_match_count(expected, actual)
    checked = max(len(expected), len(actual))
    if checked == 0:
        return _gate(0, 0)
    return _gate(checked, matched if Counter(expected) == Counter(actual) else matched)


def qualify_private(payload, source_digest, run_timestamp):
    _validate_private_shape(payload)
    transformation_gate = _qualify_external_transformation_profile(payload)
    chart, stars, stems = _build_private_basis(payload)

    graph, natal_gate = _qualify_natal(payload, stars, stems)

    decadal = payload["decadal"]
    decadal_matched = _qualify_cycle(
        chart,
        stars,
        "decadal",
        decadal["reference"],
        decadal["stem"],
        decadal["expected_edges"],
    )
    decadal_gate = _gate(4, decadal_matched)

    yearly_matched = 0
    for item in payload["yearly"]:
        yearly_matched += _qualify_cycle(
            chart,
            stars,
            "yearly",
            item["reference"],
            item["stem"],
            item["expected_edges"],
        )
    yearly_gate = _gate(28, yearly_matched)

    flying_matched = (
        natal_gate["matched"] + decadal_gate["matched"] + yearly_gate["matched"]
    )
    flying_gate = _gate(80, flying_matched)
    presentation_gate = _qualify_presentation(payload, graph)

    overall_pass = (
        transformation_gate["status"] == "PASS"
        and flying_gate["status"] == "PASS"
    )
    return {
        "source_system": "Astralium",
        "source_profile": payload["source_profile"],
        "source_digest": source_digest,
        "rule_profile": PROFILE_ID,
        "rule_version": RULE_VERSION,
        "transformation_profile": transformation_gate,
        "natal": natal_gate,
        "decadal": decadal_gate,
        "yearly": yearly_gate,
        "flying_total": flying_gate,
        "presentation": presentation_gate,
        "status": "PASS" if overall_pass else "FAIL",
        "run_timestamp": run_timestamp,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--run-timestamp", default="2026-08-21T00:00:00Z")
    args = parser.parse_args(argv)

    raw = Path(args.input).read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    source_digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    evidence = qualify_private(payload, source_digest, args.run_timestamp)
    Path(args.output).write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    gates = (
        ("ASTRALIUM_TRANSFORMATION_40_PASS", evidence["transformation_profile"]),
        ("ASTRALIUM_NATAL_48_PASS", evidence["natal"]),
        ("ASTRALIUM_DECADAL_4_PASS", evidence["decadal"]),
        ("ASTRALIUM_YEARLY_28_PASS", evidence["yearly"]),
        ("ASTRALIUM_FLYING_80_PASS", evidence["flying_total"]),
    )
    for marker, gate in gates:
        if gate["status"] == "PASS":
            print(marker)
        else:
            print(marker.replace("_PASS", "_FAIL"))

    return 0 if evidence["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
