#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.distribution.capabilities import get_capability as get_distribution_capability
from engine.distribution.constants import CASE_SCHEMA_VERSION
from engine.distribution.manifest import (
    CAPABILITY_MANIFEST_VERSION,
    capability_manifest_digest,
    load_capability_manifest,
)
from engine.distribution.runtime import dispatch
from engine.historical.capabilities import get_capability as get_historical_capability
from tools import build_ai_distribution, build_release_package


RELEASE_VERSION = "1.7.0"
RELEASE_SURFACE_CHECKS = (
    "capability_manifest_v1",
    "case_doctor_contract",
    "case_reconciliation_dry_run",
    "prospective_v1_frozen_identity",
    "prospective_validation_v2",
    "guided_inquiry_contract",
    "project_instructions_size",
    "case_schema_1_1",
    "selector_v1_default",
    "interpretation_v1_default",
    "deterministic_user_package",
    "python39_compile",
    "distribution_parity",
)


def _focused_test(test_name: str) -> bool:
    suite = unittest.defaultTestLoader.loadTestsFromName(test_name)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    return result.wasSuccessful()


def _check_capability_manifest_v1(_distribution_dir: Path) -> bool:
    manifest = load_capability_manifest()
    digest = capability_manifest_digest(manifest)
    capabilities = manifest.get("capabilities", {})
    return (
        CAPABILITY_MANIFEST_VERSION == "1.0"
        and manifest.get("manifest_version") == "1.0"
        and list(capabilities) == sorted(capabilities)
        and len(digest) == 64
    )


def _check_case_doctor_contract(_distribution_dir: Path) -> bool:
    return _focused_test(
        "tests.test_v17_case_doctor.CaseDoctorTests."
        "test_clean_base_has_exact_output_shape_and_passes"
    )


def _check_case_reconciliation_dry_run(_distribution_dir: Path) -> bool:
    return _focused_test(
        "tests.test_v17_case_reconciliation.CaseReconciliationPlannerTests."
        "test_clean_case_returns_deterministic_no_change"
    )


def _check_prospective_v1_frozen_identity(_distribution_dir: Path) -> bool:
    return _focused_test(
        "tests.test_v17_release_contract.V17ReleaseContractTests."
        "test_v15_prospective_lock_identity_remains_exact"
    )


def _check_prospective_validation_v2(_distribution_dir: Path) -> bool:
    context_payload = {
        "forecast_id": "PV2-release-surface",
        "locked_at": "2026-09-09T09:30:00+08:00",
        "knowledge_cutoff_at": "2026-09-09T09:20:00+08:00",
        "question_mode": "future_forecast",
        "knowledge_state_at_lock": "unknown",
        "prediction_window": {
            "start": "2026-10-01T00:00:00+08:00",
            "end": "2026-10-31T23:59:59+08:00",
        },
    }
    classified = dispatch("classify_validation_context", context_payload)
    if not classified.get("ok"):
        return False
    summary = dispatch(
        "build_validation_summary",
        {
            "records": [
                {
                    "validation_context": classified["data"],
                    "verification_state": "matched",
                }
            ]
        },
    )
    return bool(
        summary.get("ok")
        and summary.get("data", {}).get("clean_denominator", {}).get("scorable_count") == 1
    )


def _check_guided_inquiry_contract(_distribution_dir: Path) -> bool:
    return _focused_test(
        "tests.test_v17_guided_inquiry.GuidedInquiryPolicyTests."
        "test_entry_pass_returns_exactly_three_suggestions"
    )


def _check_project_instructions_size(distribution_dir: Path) -> bool:
    text = (distribution_dir / "project_instructions.txt").read_text(encoding="utf-8")
    return bool(text) and len(text) <= 8000


def _check_case_schema_1_1(_distribution_dir: Path) -> bool:
    return CASE_SCHEMA_VERSION == "1.1"


def _check_selector_v1_default(_distribution_dir: Path) -> bool:
    capability = get_historical_capability("historical.activation_selector")
    return (
        capability.get("profile_id") == "historical-activation-bazi-v1"
        and capability.get("rule_version") == "1.0-exp"
    )


def _check_interpretation_v1_default(_distribution_dir: Path) -> bool:
    capability = get_distribution_capability("distribution.interpretation_contract")
    return capability.get("rule_version") == "lin_tianji_interpretation_contract_v1-exp"


def _check_deterministic_user_package(distribution_dir: Path) -> bool:
    first = build_release_package.render_user_package(distribution_dir)
    second = build_release_package.render_user_package(distribution_dir)
    if first != second:
        return False
    report = build_release_package.verify_user_package(first, distribution_dir)
    return (
        build_release_package.RELEASE_VERSION == RELEASE_VERSION
        and report.get("integrity_verified") is True
        and report.get("release_version") == RELEASE_VERSION
        and tuple(report.get("members", ())) == build_release_package.USER_ASSETS
    )


def _check_python39_compile(distribution_dir: Path) -> bool:
    path = distribution_dir / "metaphysics_lab.py"
    compile(path.read_text(encoding="utf-8"), str(path), "exec")
    return True


def _check_distribution_parity(distribution_dir: Path) -> bool:
    expected = build_ai_distribution.render_distribution(_REPO_ROOT)
    if tuple(expected) != build_ai_distribution.ARTIFACT_NAMES:
        return False
    return all(
        (distribution_dir / name).read_bytes() == content
        for name, content in expected.items()
    )


_CHECK_FUNCTIONS = (
    ("capability_manifest_v1", _check_capability_manifest_v1),
    ("case_doctor_contract", _check_case_doctor_contract),
    ("case_reconciliation_dry_run", _check_case_reconciliation_dry_run),
    ("prospective_v1_frozen_identity", _check_prospective_v1_frozen_identity),
    ("prospective_validation_v2", _check_prospective_validation_v2),
    ("guided_inquiry_contract", _check_guided_inquiry_contract),
    ("project_instructions_size", _check_project_instructions_size),
    ("case_schema_1_1", _check_case_schema_1_1),
    ("selector_v1_default", _check_selector_v1_default),
    ("interpretation_v1_default", _check_interpretation_v1_default),
    ("deterministic_user_package", _check_deterministic_user_package),
    ("python39_compile", _check_python39_compile),
    ("distribution_parity", _check_distribution_parity),
)


def run(distribution_dir: Path) -> dict:
    distribution = Path(distribution_dir)
    rows = []
    for name, check in _CHECK_FUNCTIONS:
        try:
            passed = bool(check(distribution))
        except Exception:
            passed = False
        rows.append({"check": name, "status": "PASS" if passed else "FAIL"})
    return {
        "release_version": RELEASE_VERSION,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "checks": rows,
        "note": (
            "v1.7 deterministic release-surface orchestration over canonical runtime, "
            "focused contracts, distribution, and user package"
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate the Metaphysics Lab v1.7 release surface")
    parser.add_argument("--distribution-dir", default="dist/ai")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    distribution = Path(args.distribution_dir)
    if not distribution.is_absolute():
        distribution = _REPO_ROOT / distribution
    report = run(distribution)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        for row in report["checks"]:
            print("%s: %s" % (row["check"], row["status"]))
        print("status: %s" % report["status"])
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
