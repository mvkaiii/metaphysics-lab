import importlib.util
import json
import unittest
from pathlib import Path

from engine.distribution.capabilities import get_capability as get_distribution_capability
from engine.historical.capabilities import get_capability as get_historical_capability
from tools import build_release_package

ROOT = Path(__file__).resolve().parents[1]


class V16ReleaseContractTests(unittest.TestCase):
    def test_release_package_identity_is_v160(self):
        self.assertEqual(build_release_package.RELEASE_VERSION, "1.6.0")
        self.assertEqual(
            build_release_package.USER_PACKAGE_NAME,
            "Metaphysics-Lab-v1.6.0-User-Package.zip",
        )

    def test_v1_defaults_remain_stable_while_v16_research_layers_ship_non_default(self):
        selector = get_historical_capability("historical.activation_selector")
        interpretation = get_distribution_capability("distribution.interpretation_contract")
        self.assertEqual(selector["profile_id"], "historical-activation-bazi-v1")
        self.assertEqual(selector["rule_version"], "1.0-exp")
        self.assertEqual(
            interpretation["rule_version"],
            "lin_tianji_interpretation_contract_v1-exp",
        )
        self.assertTrue((ROOT / "engine" / "ziwei" / "yearly_cycle.py").is_file())

    def test_v16_release_surface_validator_exists(self):
        path = ROOT / "tools" / "run_v16_release_surface_validation.py"
        self.assertTrue(path.is_file())
        spec = importlib.util.spec_from_file_location("run_v16_release_surface_validation_test", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.run(ROOT / "dist" / "ai")
        self.assertEqual(report["status"], "PASS", report)

    def test_v16_validation_and_release_workflows_are_versioned_and_fail_closed(self):
        validation = ROOT / ".github" / "workflows" / "lin-tianji-v1.6-validation.yml"
        release = ROOT / ".github" / "workflows" / "release-v1.6.yml"
        self.assertTrue(validation.is_file())
        self.assertTrue(release.is_file())
        release_text = release.read_text(encoding="utf-8")
        self.assertIn("v1.6.0", release_text)
        self.assertIn("Metaphysics-Lab-v1.6.0-User-Package.zip", release_text)
        self.assertIn("validate_v16_sandbox_evidence.py", release_text)
        self.assertIn("v1.6.0-isolated-sandbox-transcript.md", release_text)
        self.assertIn("gh release create v1.6.0", release_text)
        self.assertTrue((ROOT / ".github" / "workflows" / "release-v1.5.yml").is_file())

    def test_v16_qualification_keeps_v2_sandbox_gate_pending(self):
        qualification = ROOT / "docs" / "release" / "v1.6.0-qualification.md"
        text = qualification.read_text(encoding="utf-8")
        self.assertIn("sandbox_contract_version: v1.6.0-isolated-sandbox-script.v2", text)
        self.assertIn("sandbox_evidence_status: PENDING", text)
        self.assertIn("operator-only", text)
        self.assertIn("staged visibility", text)
        self.assertIn(
            "- [ ] isolated sandbox conversation validation PASS on exact release candidate SHA",
            text,
        )

    def test_v16_release_docs_exist_and_state_no_accuracy_promotion(self):
        notes = ROOT / "docs" / "發布說明-v1.6.0.md"
        qualification = ROOT / "docs" / "release" / "v1.6.0-qualification.md"
        self.assertTrue(notes.is_file())
        self.assertTrue(qualification.is_file())
        text = notes.read_text(encoding="utf-8") + "\n" + qualification.read_text(encoding="utf-8")
        for required in (
            "v1.6.0",
            "Y1",
            "Experimental",
            "不代表預測準確度已被證明",
            "promotion_allowed=false",
        ):
            self.assertIn(required, text)

    def test_v16_sandbox_kit_is_synthetic_and_pending_evidence_fails_closed(self):
        legacy_script = ROOT / "docs" / "release" / "v1.6.0-isolated-sandbox-script.md"
        legacy_fixture = ROOT / "tests" / "fixtures" / "v1.6.0-isolated-sandbox-fixture.v1.json"
        script = ROOT / "docs" / "release" / "v1.6.0-isolated-sandbox-script.v2.md"
        fixture = ROOT / "tests" / "fixtures" / "v1.6.0-isolated-sandbox-base.v1.json"
        known_reality = ROOT / "tests" / "fixtures" / "operator-only" / "v1.6.0-isolated-sandbox-known-reality.v1.json"
        historical_ledger = ROOT / "tests" / "fixtures" / "operator-only" / "v1.6.0-isolated-sandbox-historical-ledger.v1.json"
        pending = ROOT / "tests" / "fixtures" / "v1.6.0-isolated-sandbox-evidence.pending.md"
        transcript = ROOT / "docs" / "release" / "v1.6.0-isolated-sandbox-transcript.md"
        validator = ROOT / "tools" / "validate_v16_sandbox_evidence.py"
        self.assertFalse(legacy_script.exists())
        self.assertFalse(legacy_fixture.exists())
        self.assertTrue(script.is_file())
        self.assertTrue(fixture.is_file())
        self.assertTrue(known_reality.is_file())
        self.assertTrue(historical_ledger.is_file())
        self.assertTrue(pending.is_file())
        self.assertTrue(transcript.is_file())
        self.assertTrue(validator.is_file())
        base = json.loads(fixture.read_text(encoding="utf-8"))
        known = json.loads(known_reality.read_text(encoding="utf-8"))
        ledger = json.loads(historical_ledger.read_text(encoding="utf-8"))
        self.assertEqual(base["fixture_version"], "v1.6.0-isolated-sandbox-base.v1")
        self.assertEqual(known["fixture_version"], "v1.6.0-isolated-sandbox-known-reality.v1")
        self.assertEqual(ledger["fixture_version"], "v1.6.0-isolated-sandbox-historical-ledger.v1")
        self.assertNotIn("known_reality_context", base)
        self.assertNotIn("historical_event_ledger", base)
        self.assertEqual(len(ledger["historical_event_ledger"]), 10)
        self.assertEqual(
            [row["year"] for row in ledger["historical_event_ledger"]],
            list(range(2016, 2026)),
        )
        combined = script.read_text(encoding="utf-8") + "\n" + fixture.read_text(encoding="utf-8")
        self.assertIn("fictional", combined.lower())
        self.assertNotIn("1984-03-13", combined)
        self.assertNotIn("event_date", combined)
        self.assertIn("Y1", script.read_text(encoding="utf-8"))
        self.assertIn("Experimental", script.read_text(encoding="utf-8"))
        self.assertIn("P05", script.read_text(encoding="utf-8"))
        self.assertIn("P06", script.read_text(encoding="utf-8"))
        self.assertIn("staged_visibility_v2", script.read_text(encoding="utf-8"))
        self.assertIn("initial context", script.read_text(encoding="utf-8"))
        self.assertIn("blind", script.read_text(encoding="utf-8").lower())
        pending_text = pending.read_text(encoding="utf-8")
        self.assertIn("schema_version: v1.6.0-isolated-sandbox-evidence.v2", pending_text)
        self.assertIn("transcript_sha256: PENDING", pending_text)
        self.assertNotIn("status: PASS", pending_text)
        self.assertIn(
            "formal_synthetic_sandbox_transcript",
            transcript.read_text(encoding="utf-8"),
        )

        spec = importlib.util.spec_from_file_location("validate_v16_sandbox_evidence_test", validator)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.validate_evidence(ROOT, pending, "f" * 40)
        self.assertEqual(report["status"], "PENDING", report)
        self.assertFalse(report["release_allowed"], report)
        self.assertIn("evidence_status_not_pass", report["errors"])


if __name__ == "__main__":
    unittest.main()
