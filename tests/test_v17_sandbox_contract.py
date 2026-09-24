import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = Path("docs/release/v1.7.0-isolated-sandbox-script.md")
BASE_FIXTURE_PATH = Path("docs/release/v1.7.0-isolated-sandbox-base.json")
QUALIFICATION_PATH = Path("docs/release/v1.7.0-qualification.md")
TRANSCRIPT_PATH = Path("docs/release/v1.7.0-isolated-sandbox-transcript.md")
VALIDATOR_PATH = ROOT / "tools" / "validate_v17_sandbox_evidence.py"

SCENARIOS = tuple("S%02d" % number for number in range(1, 13))
RUBRICS = (
    "guided_count_pass",
    "guided_timing_pass",
    "guided_specificity_pass",
    "case_integrity_pass",
    "no_auto_delete_pass",
    "validation_context_pass",
    "clean_denominator_pass",
    "blindness_pass",
    "experimental_ceiling_pass",
    "natural_language_pass",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_validator():
    if not VALIDATOR_PATH.is_file():
        raise AssertionError("v1.7 sandbox evidence validator is missing")
    spec = importlib.util.spec_from_file_location("validate_v17_sandbox_evidence_test", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("v1.7 sandbox evidence validator cannot be imported")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class V17SandboxContractTests(unittest.TestCase):
    def test_contract_artifacts_freeze_scenarios_and_critical_rubrics(self):
        for relative in (SCRIPT_PATH, BASE_FIXTURE_PATH, QUALIFICATION_PATH):
            self.assertTrue((ROOT / relative).is_file(), relative.as_posix())
        script = (ROOT / SCRIPT_PATH).read_text(encoding="utf-8")
        qualification = (ROOT / QUALIFICATION_PATH).read_text(encoding="utf-8")
        for scenario in SCENARIOS:
            self.assertIn(scenario, script)
        for rubric in RUBRICS:
            self.assertIn(rubric, script)
            self.assertIn(rubric, qualification)
        status_lines = [
            line.split(":", 1)[1].strip()
            for line in qualification.splitlines()
            if line.startswith("status:")
        ]
        self.assertEqual(len(status_lines), 1)
        self.assertIn(status_lines[0], {"PENDING", "PASS", "FAIL"})

    def test_base_fixture_is_synthetic_and_blind_safe(self):
        path = ROOT / BASE_FIXTURE_PATH
        self.assertTrue(path.is_file())
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["fixture_version"], "v1.7.0-isolated-sandbox-base.v1")
        self.assertEqual(payload["classification"], "synthetic_test_case")
        self.assertEqual(payload["privacy"], "fictional_no_real_user_data")
        self.assertFalse(payload["contains_private_user_data"])
        self.assertFalse(payload["contains_outcome_data"])
        forbidden = {
            "known_reality_context",
            "historical_event_ledger",
            "validation_events",
            "actual_outcome",
            "private_user_data",
        }
        self.assertFalse(forbidden & set(payload))

    @staticmethod
    def _pass_evidence(root: Path) -> Path:
        release_dir = root / "docs" / "release"
        release_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / SCRIPT_PATH, root / SCRIPT_PATH)
        shutil.copy2(ROOT / BASE_FIXTURE_PATH, root / BASE_FIXTURE_PATH)
        transcript = root / TRANSCRIPT_PATH
        transcript.write_text("# Synthetic v1.7 isolated sandbox transcript\n\nAll content is fictional.\n", encoding="utf-8")
        evidence = release_dir / "synthetic-pass-evidence.md"
        lines = [
            "# Synthetic v1.7 sandbox evidence",
            "",
            "schema_version: v1.7.0-isolated-sandbox-evidence.v1",
            "status: PASS",
            "script_version: v1.7.0-isolated-sandbox-script.v4",
            "base_fixture_version: v1.7.0-isolated-sandbox-base.v1",
            "tested_release_candidate_sha: %s" % ("a" * 40),
            "candidate_frozen_at: 2026-09-10T18:00:00+08:00",
            "executed_at: 2026-09-10T18:10:00+08:00",
            "adjudicated_at: 2026-09-10T18:20:00+08:00",
            "sandbox_run_id: synthetic-unit-test",
            "sandbox_environment: synthetic-unit-test",
            "model_ui_label: Synthetic Model Label",
            "script_sha256: %s" % _sha256(root / SCRIPT_PATH),
            "base_fixture_sha256: %s" % _sha256(root / BASE_FIXTURE_PATH),
            "transcript_sha256: %s" % _sha256(transcript),
            "transcript_reference: %s" % TRANSCRIPT_PATH.as_posix(),
            "",
            "## Scenario results",
        ]
        lines.extend("- %s: PASS" % scenario for scenario in SCENARIOS)
        lines.extend(["", "## Critical rubric"])
        lines.extend("- %s: PASS" % rubric for rubric in RUBRICS)
        evidence.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return evidence

    def test_validator_accepts_synthetic_pass_evidence(self):
        validator = _load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = self._pass_evidence(root)
            report = validator.validate_evidence(root, evidence, "a" * 40)
        self.assertEqual(report["status"], "PASS", report)
        self.assertTrue(report["release_allowed"], report)

    def test_validator_rejects_tampered_transcript_rubric_and_fixture(self):
        validator = _load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = self._pass_evidence(root)
            transcript = root / TRANSCRIPT_PATH
            transcript.write_text(transcript.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
            report = validator.validate_evidence(root, evidence, "a" * 40)
            self.assertEqual(report["status"], "FAIL")
            self.assertIn("transcript_sha256_mismatch", report["errors"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = self._pass_evidence(root)
            text = evidence.read_text(encoding="utf-8").replace(
                "- blindness_pass: PASS", "- blindness_pass: FAIL"
            )
            evidence.write_text(text, encoding="utf-8")
            report = validator.validate_evidence(root, evidence, "a" * 40)
            self.assertEqual(report["status"], "FAIL")
            self.assertIn("rubric_not_pass:blindness_pass", report["errors"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = self._pass_evidence(root)
            base_path = root / BASE_FIXTURE_PATH
            payload = json.loads(base_path.read_text(encoding="utf-8"))
            payload["known_reality_context"] = {"hidden": "synthetic but forbidden in base"}
            base_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            report = validator.validate_evidence(root, evidence, "a" * 40)
            self.assertEqual(report["status"], "FAIL")
            self.assertIn("base_fixture_contains_known_reality_context", report["errors"])

    def test_validator_rejects_pending_model_ui_label(self):
        validator = _load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = self._pass_evidence(root)
            text = evidence.read_text(encoding="utf-8").replace(
                "model_ui_label: Synthetic Model Label", "model_ui_label: PENDING"
            )
            evidence.write_text(text, encoding="utf-8")
            report = validator.validate_evidence(root, evidence, "a" * 40)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("model_ui_label_missing", report["errors"])


if __name__ == "__main__":
    unittest.main()
