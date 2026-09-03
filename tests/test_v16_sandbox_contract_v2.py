import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = Path("tests/fixtures/v1.6.0-isolated-sandbox-base.v1.json")
KNOWN_REALITY_PATH = Path(
    "tests/fixtures/operator-only/v1.6.0-isolated-sandbox-known-reality.v1.json"
)
HISTORICAL_LEDGER_PATH = Path(
    "tests/fixtures/operator-only/v1.6.0-isolated-sandbox-historical-ledger.v1.json"
)
SCRIPT_PATH = Path("docs/release/v1.6.0-isolated-sandbox-script.v2.md")
TRANSCRIPT_PATH = Path("docs/release/v1.6.0-isolated-sandbox-transcript.md")
EVIDENCE_PATH = Path(
    "docs/release/v1.6.0-isolated-sandbox-conversation-validation.md"
)
RUBRICS = (
    "temporal_ownership_pass",
    "specificity_pass",
    "calibration_narrowing_pass",
    "cutoff_contamination_pass",
    "experimental_ceiling_pass",
    "natural_language_pass",
    "algorithm_disclosure_pass",
    "strategy_forecast_separation_pass",
)


def _load_validator():
    path = ROOT / "tools" / "validate_v16_sandbox_evidence.py"
    spec = importlib.util.spec_from_file_location("validate_v16_sandbox_evidence_v2_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validator = _load_validator()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True
    ).strip()


def _write_evidence(path: Path, fields: dict) -> None:
    lines = []
    rubric_lines = []
    for key, value in fields.items():
        if key in RUBRICS:
            rubric_lines.append(f"- {key}: {value}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("")
    lines.append("## Critical rubric")
    lines.extend(rubric_lines)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _valid_v2_evidence_fields() -> dict:
    fields = {
        "schema_version": "v1.6.0-isolated-sandbox-evidence.v2",
        "status": "PASS",
        "script_version": "v1.6.0-isolated-sandbox-script.v2",
        "base_fixture_version": "v1.6.0-isolated-sandbox-base.v1",
        "known_reality_fixture_version": "v1.6.0-isolated-sandbox-known-reality.v1",
        "historical_ledger_fixture_version": "v1.6.0-isolated-sandbox-historical-ledger.v1",
        "tested_release_candidate_sha": _git_head(),
        "tested_distribution_digest": "0" * 64,
        "tested_user_package_sha256": "0" * 64,
        "script_sha256": "0" * 64,
        "base_fixture_sha256": "0" * 64,
        "known_reality_fixture_sha256": "0" * 64,
        "historical_ledger_fixture_sha256": "0" * 64,
        "sandbox_run_id": "run-v2-test",
        "sandbox_environment": "fresh isolated synthetic test context",
        "executed_at": "2026-09-04T00:00:00Z",
        "transcript_reference": TRANSCRIPT_PATH.as_posix(),
        "transcript_sha256": "0" * 64,
    }
    for path_key, relative in (
        ("script_sha256", SCRIPT_PATH),
        ("base_fixture_sha256", BASE_PATH),
        ("known_reality_fixture_sha256", KNOWN_REALITY_PATH),
        ("historical_ledger_fixture_sha256", HISTORICAL_LEDGER_PATH),
        ("transcript_sha256", TRANSCRIPT_PATH),
    ):
        path = ROOT / relative
        if path.is_file():
            fields[path_key] = _sha256(path)
    if SCRIPT_PATH.is_file() and BASE_PATH.is_file() and TRANSCRIPT_PATH.is_file():
        from tools import build_release_package
        from tools import run_v16_release_surface_validation

        surface = run_v16_release_surface_validation.run(ROOT / "dist" / "ai")
        package = build_release_package.render_user_package(ROOT / "dist" / "ai")
        fields["tested_distribution_digest"] = surface["distribution_digest"]
        fields["tested_user_package_sha256"] = hashlib.sha256(package).hexdigest()
    for rubric in RUBRICS:
        fields[rubric] = "PASS"
    return fields


def _validate_evidence_with_fields(fields: dict) -> dict:
    with tempfile.TemporaryDirectory() as temp_dir:
        evidence = Path(temp_dir) / "evidence.md"
        _write_evidence(evidence, fields)
        return validator.validate_evidence(ROOT, evidence, _git_head())


def _write_v2_fixture_set(root: Path) -> None:
    (root / BASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / KNOWN_REALITY_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / HISTORICAL_LEDGER_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / BASE_PATH).write_text(
        json.dumps(
            {
                "fixture_version": "v1.6.0-isolated-sandbox-base.v1",
                "classification": "synthetic_test_case",
                "privacy": "fictional_no_real_user_data",
                "subject": {
                    "display_name": "Mina",
                    "sex": "female",
                    "birth_date": "1992-08-17",
                    "birth_time": "14:30",
                    "birth_place": "高雄市",
                },
                "target_year": 2027,
            }
        ),
        encoding="utf-8",
    )
    (root / KNOWN_REALITY_PATH).write_text(
        json.dumps(
            {
                "fixture_version": "v1.6.0-isolated-sandbox-known-reality.v1",
                "classification": "operator_only_known_reality",
                "privacy": "fictional_no_real_user_data",
                "known_reality_context": {
                    "known_before_lock": True,
                    "event_date": "2027-04-15",
                    "event_time": "20:00",
                    "summary": "synthetic fixed known reality",
                },
            }
        ),
        encoding="utf-8",
    )
    (root / HISTORICAL_LEDGER_PATH).write_text(
        json.dumps(
            {
                "fixture_version": "v1.6.0-isolated-sandbox-historical-ledger.v1",
                "classification": "operator_only_historical_ledger",
                "privacy": "fictional_no_real_user_data",
                "historical_event_ledger": [
                    {"year": 2016, "status": "verified", "summary": "synthetic"}
                ],
            }
        ),
        encoding="utf-8",
    )


def _make_git_history(changed_path: str):
    temp_dir = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    subprocess.run(["git", "init", "-q"], cwd=str(root), check=True)
    (root / "stable.txt").write_text("stable\n", encoding="utf-8")
    subprocess.run(["git", "add", "stable.txt"], cwd=str(root), check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=contract-test",
            "-c",
            "user.email=contract-test@example.invalid",
            "commit",
            "-qm",
            "base",
        ],
        cwd=str(root),
        check=True,
    )
    tested_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(root), text=True
    ).strip()
    changed = root / changed_path
    changed.parent.mkdir(parents=True, exist_ok=True)
    changed.write_text("evidence delta\n", encoding="utf-8")
    subprocess.run(["git", "add", changed_path], cwd=str(root), check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=contract-test",
            "-c",
            "user.email=contract-test@example.invalid",
            "commit",
            "-qm",
            "delta",
        ],
        cwd=str(root),
        check=True,
    )
    current_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(root), text=True
    ).strip()
    return temp_dir, root, tested_sha, current_sha


class V16SandboxContractV2Tests(unittest.TestCase):
    def test_v2_validator_exposes_new_paths_and_versions(self):
        self.assertEqual(
            validator.EVIDENCE_SCHEMA_VERSION,
            "v1.6.0-isolated-sandbox-evidence.v2",
        )
        self.assertEqual(
            validator.SCRIPT_VERSION,
            "v1.6.0-isolated-sandbox-script.v2",
        )
        self.assertEqual(validator.BASE_FIXTURE_PATH, BASE_PATH)
        self.assertEqual(validator.KNOWN_REALITY_FIXTURE_PATH, KNOWN_REALITY_PATH)
        self.assertEqual(validator.HISTORICAL_LEDGER_FIXTURE_PATH, HISTORICAL_LEDGER_PATH)
        self.assertEqual(validator.TRANSCRIPT_PATH, TRANSCRIPT_PATH)

    def test_split_fixtures_preserve_canonical_mina_values_and_visibility(self):
        self.assertTrue((ROOT / BASE_PATH).is_file())
        self.assertTrue((ROOT / KNOWN_REALITY_PATH).is_file())
        self.assertTrue((ROOT / HISTORICAL_LEDGER_PATH).is_file())
        base = json.loads((ROOT / BASE_PATH).read_text(encoding="utf-8"))
        known = json.loads((ROOT / KNOWN_REALITY_PATH).read_text(encoding="utf-8"))
        ledger = json.loads((ROOT / HISTORICAL_LEDGER_PATH).read_text(encoding="utf-8"))

        self.assertEqual(base["subject"]["display_name"], "Mina")
        self.assertEqual(base["subject"]["birth_date"], "1992-08-17")
        self.assertEqual(base["target_year"], 2027)
        self.assertNotIn("known_reality_context", base)
        self.assertNotIn("historical_event_ledger", base)
        self.assertEqual(known["known_reality_context"]["event_date"], "2027-04-15")
        self.assertEqual(known["known_reality_context"]["event_time"], "20:00")
        self.assertEqual(
            [row["year"] for row in ledger["historical_event_ledger"]],
            list(range(2016, 2026)),
        )

    def test_base_fixture_rejects_combined_known_reality_or_ledger(self):
        self.assertTrue(callable(getattr(validator, "validate_fixture_contract", None)))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_v2_fixture_set(root)
            base_path = root / BASE_PATH
            base = json.loads(base_path.read_text(encoding="utf-8"))
            base["known_reality_context"] = {"contaminated": True}
            base_path.write_text(json.dumps(base), encoding="utf-8")
            errors = validator.validate_fixture_contract(root)
            self.assertIn("base_fixture_contains_known_reality_context", errors)

    def test_operator_fixture_rejects_cross_visibility_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_v2_fixture_set(root)
            known_path = root / KNOWN_REALITY_PATH
            known = json.loads(known_path.read_text(encoding="utf-8"))
            known["subject"] = {"display_name": "Mina"}
            known_path.write_text(json.dumps(known), encoding="utf-8")
            errors = validator.validate_fixture_contract(root)
            self.assertIn("known_reality_fixture_unexpected_field:subject", errors)

    def test_unknown_critical_rubric_fails_closed(self):
        fields = _valid_v2_evidence_fields()
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence = Path(temp_dir) / "evidence.md"
            _write_evidence(evidence, fields)
            evidence.write_text(
                evidence.read_text(encoding="utf-8")
                + "- unrecognized_rubric: PASS\n",
                encoding="utf-8",
            )
            report = validator.validate_evidence(ROOT, evidence, _git_head())
            self.assertIn("unknown_rubric:unrecognized_rubric", report["errors"])

    def test_missing_operator_fixture_hash_fails(self):
        fields = _valid_v2_evidence_fields()
        fields.pop("known_reality_fixture_sha256")
        report = _validate_evidence_with_fields(fields)
        self.assertIn("known_reality_fixture_sha256_invalid", report["errors"])

    def test_wrong_transcript_hash_fails(self):
        fields = _valid_v2_evidence_fields()
        fields["transcript_sha256"] = "0" * 64
        report = _validate_evidence_with_fields(fields)
        self.assertIn("transcript_sha256_mismatch", report["errors"])

    def test_any_critical_rubric_fail_blocks_release(self):
        fields = _valid_v2_evidence_fields()
        fields["specificity_pass"] = "FAIL"
        report = _validate_evidence_with_fields(fields)
        self.assertNotIn("evidence_schema_mismatch", report["errors"])
        self.assertIn("rubric_not_pass:specificity_pass", report["errors"])

    def test_tested_sha_followed_by_non_evidence_change_fails(self):
        temp_dir, root, tested_sha, current_sha = _make_git_history(
            "dist/ai/metaphysics_lab.py"
        )
        try:
            errors = validator._validate_evidence_seal_delta(root, tested_sha, current_sha)
            self.assertIn(
                "post_sandbox_non_evidence_change:dist/ai/metaphysics_lab.py",
                errors,
            )
        finally:
            temp_dir.cleanup()

    def test_valid_evidence_only_seal_delta_passes(self):
        for path in (
            "docs/release/v1.6.0-isolated-sandbox-transcript.md",
            "docs/release/v1.6.0-isolated-sandbox-conversation-validation.md",
            "docs/release/v1.6.0-qualification.md",
        ):
            temp_dir, root, tested_sha, current_sha = _make_git_history(path)
            try:
                self.assertEqual(
                    validator._validate_evidence_seal_delta(root, tested_sha, current_sha),
                    [],
                    path,
                )
            finally:
                temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
