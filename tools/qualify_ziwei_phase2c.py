#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from engine.ziwei.flowing_stars import FLOWING_STAR_PROFILE_ID, place_flowing_stars_for_pair


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUBLIC_FIXTURE = ROOT / "qualification" / "ziwei" / "phase2c" / "public-iztro-flowing-star-vectors.json"
EXPECTED_ORACLE_VERSION = "2.6.0"
EXPECTED_ORACLE_REVISION = "814b77e6371e1050cac31bbf674db3c3138fcfde"
EXPECTED_CASE_COUNT = 600
EXPECTED_PLACEMENT_COUNT = 6120


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _project_triplets(scope: str, stem: str, branch: str) -> Tuple[Tuple[str, str, str], ...]:
    return tuple(
        (placement.base_star, placement.category, placement.target_branch)
        for placement in place_flowing_stars_for_pair(scope, stem, branch)
    )


def _oracle_triplets(placements: Iterable[Mapping[str, Any]]) -> Tuple[Tuple[str, str, str], ...]:
    return tuple(
        (str(item["base_star"]), str(item["category"]), str(item["target_branch"]))
        for item in placements
    )


def qualify_public(path: Path = DEFAULT_PUBLIC_FIXTURE) -> Dict[str, Any]:
    data = _load_json(Path(path))
    metadata_errors: List[Dict[str, Any]] = []

    expected_metadata = {
        "profile_id": FLOWING_STAR_PROFILE_ID,
        "oracle.package_version": EXPECTED_ORACLE_VERSION,
        "oracle.revision": EXPECTED_ORACLE_REVISION,
        "source_case_count": EXPECTED_CASE_COUNT,
        "placement_check_count": EXPECTED_PLACEMENT_COUNT,
    }
    actual_metadata = {
        "profile_id": data.get("profile_id"),
        "oracle.package_version": data.get("oracle", {}).get("package_version"),
        "oracle.revision": data.get("oracle", {}).get("revision"),
        "source_case_count": data.get("source_case_count"),
        "placement_check_count": data.get("placement_check_count"),
    }
    for field, expected in expected_metadata.items():
        actual = actual_metadata[field]
        if actual != expected:
            metadata_errors.append({"field": field, "expected": expected, "actual": actual})

    cases = tuple(data.get("cases", ()))
    mismatches: List[Dict[str, Any]] = []
    checked_placements = 0
    for index, case in enumerate(cases):
        scope = str(case["scope"])
        stem = str(case["stem"])
        branch = str(case["branch"])
        oracle = _oracle_triplets(case["placements"])
        project = _project_triplets(scope, stem, branch)
        checked_placements += len(oracle)
        if project != oracle:
            mismatches.append(
                {
                    "index": index,
                    "scope": scope,
                    "stem": stem,
                    "branch": branch,
                    "expected": oracle,
                    "actual": project,
                }
            )

    if len(cases) != EXPECTED_CASE_COUNT:
        metadata_errors.append({"field": "cases.length", "expected": EXPECTED_CASE_COUNT, "actual": len(cases)})
    if checked_placements != EXPECTED_PLACEMENT_COUNT:
        metadata_errors.append(
            {"field": "checked_placements", "expected": EXPECTED_PLACEMENT_COUNT, "actual": checked_placements}
        )

    unexpected_mismatch_count = len(metadata_errors) + len(mismatches)
    status = "PASS" if unexpected_mismatch_count == 0 else "FAIL"
    return {
        "source": "SylarLong/iztro",
        "status": status,
        "profile_id": FLOWING_STAR_PROFILE_ID,
        "oracle_version": actual_metadata["oracle.package_version"],
        "oracle_revision": actual_metadata["oracle.revision"],
        "source_case_count": len(cases),
        "placement_check_count": checked_placements,
        "unexpected_mismatch_count": unexpected_mismatch_count,
        "metadata_error_count": len(metadata_errors),
        "case_mismatch_count": len(mismatches),
        "metadata_errors": metadata_errors,
        "mismatches": mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Qualify Phase 2C Ziwei flowing-star placements")
    parser.add_argument("--public", action="store_true", help="run the pinned public iztro qualification")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_PUBLIC_FIXTURE)
    args = parser.parse_args()

    if not args.public:
        parser.error("only --public is currently supported; Astralium private qualification remains PENDING")

    report = qualify_public(args.fixture)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["source_case_count"] == EXPECTED_CASE_COUNT and report["status"] == "PASS":
        print("IZTRO_FLOWING_STARS_600_600_PASS")
    if report["unexpected_mismatch_count"] == 0:
        print("IZTRO_FLOWING_STARS_0_UNEXPECTED_MISMATCH")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
