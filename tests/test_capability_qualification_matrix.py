import copy
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.build_capability_qualification_matrix import (
    build_matrix,
    validate_evidence_index,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_SHA = "872c60b2e959ea48d25524b74686e488f576ec6f"


class CapabilityQualificationMatrixTests(unittest.TestCase):
    def test_matrix_takes_maturity_only_from_manifest(self):
        manifest = self._manifest(maturity="stable")
        index = self._index()
        index["entries"][0]["maturity"] = "experimental"

        errors = validate_evidence_index(manifest, index, REPO_ROOT)

        self.assertTrue(any("maturity" in error for error in errors))
        with self.assertRaises(ValueError):
            build_matrix(manifest, index, REPO_ROOT)

    def test_rule_scope_hash_mismatch_rejected(self):
        manifest = self._manifest(rule_version="1.0")
        index = self._index(rule_version="2.0")

        errors = validate_evidence_index(manifest, index, REPO_ROOT)

        self.assertTrue(any("rule_version" in error for error in errors))

    def test_unsupported_scope_is_rejected(self):
        manifest = self._manifest(supported_scopes=["daily"])
        index = self._index(scope="hourly")

        errors = validate_evidence_index(manifest, index, REPO_ROOT)

        self.assertTrue(any("scope" in error and "supported" in error for error in errors))

    def test_unsupported_profile_is_rejected(self):
        manifest = self._manifest(
            supported_profiles=[{"profile_id": "v1", "rule_version": "1.0-exp"}]
        )
        index = self._index(profile_id="v2")

        errors = validate_evidence_index(manifest, index, REPO_ROOT)

        self.assertTrue(any("profile_id" in error and "supported" in error for error in errors))

    def test_profile_specific_rule_version_is_enforced(self):
        manifest = self._manifest(
            supported_profiles=[
                {"profile_id": "v1", "rule_version": "1.0-exp"},
                {"profile_id": "v2", "rule_version": "2.1-exp"},
            ]
        )
        index = self._index(profile_id="v2", rule_version="1.0-exp")

        errors = validate_evidence_index(manifest, index, REPO_ROOT)

        self.assertTrue(any("profile" in error and "rule_version" in error for error in errors))

        index["entries"][0]["rule_version"] = "2.1-exp"
        self.assertEqual(validate_evidence_index(manifest, index, REPO_ROOT), [])
        self.assertEqual(build_matrix(manifest, index, REPO_ROOT)["entries"][0]["rule_version"], "2.1-exp")

    def test_unknown_source_commit_fails_closed(self):
        manifest = self._manifest()
        index = self._index()
        index["source_commit"] = "f" * 40

        errors = validate_evidence_index(manifest, index, REPO_ROOT)

        self.assertTrue(any("source_commit" in error and "repository" in error for error in errors))

    def test_working_tree_only_evidence_does_not_fallback(self):
        manifest = self._manifest()
        index = self._index()
        path = REPO_ROOT / "tests" / "test_capability_qualification_matrix.py"
        index["entries"][0]["evidence_refs"] = [self._ref(path, scope="default")]

        errors = validate_evidence_index(manifest, index, REPO_ROOT)

        self.assertTrue(any("unavailable" in error for error in errors))

    def test_missing_file_and_wrong_hash_are_rejected(self):
        manifest = self._manifest()
        index = self._index()
        index["entries"][0]["evidence_refs"] = [
            self._ref_for_relative("requirements.txt", sha256="0" * 64),
            self._ref_for_relative("tests/missing-evidence.json", sha256="0" * 64),
        ]

        errors = validate_evidence_index(manifest, index, REPO_ROOT)

        self.assertTrue(any("sha256 mismatch" in error for error in errors))
        self.assertTrue(any("unavailable" in error for error in errors))

    def test_evidence_reference_binds_entry_identity(self):
        manifest = self._manifest()
        index = self._index()
        ref = self._ref_for_relative("requirements.txt")
        ref.update(
            {
                "source_commit": "0" * 40,
                "scope": "other",
                "profile_id": "other",
                "rule_version": "other",
            }
        )
        index["entries"][0]["evidence_refs"] = [ref]

        errors = validate_evidence_index(manifest, index, REPO_ROOT)

        self.assertTrue(any("source_commit" in error for error in errors))
        self.assertTrue(any("scope" in error for error in errors))
        self.assertTrue(any("profile_id" in error for error in errors))
        self.assertTrue(any("rule_version" in error for error in errors))

    def test_malformed_inputs_return_validation_errors(self):
        manifest = self._manifest(
            supported_scopes=[{"not": "text"}],
            supported_profiles=[{"profile_id": ["not", "text"]}],
        )
        index = self._index()
        index["entries"][0]["evidence_refs"] = None

        errors = validate_evidence_index(manifest, index, REPO_ROOT)

        self.assertTrue(errors)
        self.assertTrue(any("supported_scopes" in error for error in errors))
        self.assertTrue(any("supported_profiles" in error for error in errors))
        self.assertTrue(any("evidence_refs" in error for error in errors))

    def test_missing_evidence_is_visible_gap(self):
        manifest = self._manifest()
        index = self._index(evidence_status="needs_verification")

        matrix = build_matrix(manifest, index, REPO_ROOT)

        row = matrix["entries"][0]
        self.assertEqual(row["maturity"], "experimental")
        self.assertEqual(row["evidence_status"], "needs_verification")
        self.assertEqual(row["evidence_refs"], [])
        self.assertEqual(row["promotion_decision"], "not_decided")

    def test_unknown_and_duplicate_keys_rejected(self):
        manifest = self._manifest()
        index = self._index()
        index["entries"].append(copy.deepcopy(index["entries"][0]))
        index["entries"].append(self._entry(capability_id="missing.capability"))

        errors = validate_evidence_index(manifest, index, REPO_ROOT)

        self.assertTrue(any("duplicate" in error for error in errors))
        self.assertTrue(any("unknown capability" in error for error in errors))

    def test_historical_pass_does_not_promote_capability(self):
        manifest = self._manifest(maturity="experimental")
        index = self._index(evidence_status="recorded")

        matrix = build_matrix(manifest, index, REPO_ROOT)

        row = matrix["entries"][0]
        self.assertEqual(row["maturity"], "experimental")
        self.assertEqual(row["promotion_decision"], "not_decided")

    def test_private_payload_is_not_embedded(self):
        manifest = self._manifest()
        index = self._index()
        index["entries"][0]["private_payload"] = {"raw_birth_data": "forbidden"}

        errors = validate_evidence_index(manifest, index, REPO_ROOT)

        self.assertTrue(any("unknown field" in error for error in errors))

    def test_output_is_deterministic_and_sorted_by_identity(self):
        manifest = {
            "manifest_version": "1.0",
            "capabilities": {
                "synthetic.z": self._capability("synthetic.z"),
                "synthetic.a": self._capability("synthetic.a"),
            },
        }
        index = {
            "schema_version": "1.0",
            "classification": "capability_qualification_evidence_index",
            "source_commit": BASELINE_SHA,
            "entries": [
                self._entry(capability_id="synthetic.z"),
                self._entry(capability_id="synthetic.a"),
            ],
        }

        first = build_matrix(manifest, index, REPO_ROOT)
        reordered = copy.deepcopy(manifest)
        reordered["capabilities"] = {
            "synthetic.a": reordered["capabilities"]["synthetic.a"],
            "synthetic.z": reordered["capabilities"]["synthetic.z"],
        }
        second = build_matrix(reordered, index, REPO_ROOT)

        self.assertEqual(first, second)
        self.assertEqual(
            [row["capability_id"] for row in first["entries"]],
            ["synthetic.a", "synthetic.z"],
        )

    def test_script_entrypoint_can_load_repo_modules(self):
        command = [
            sys.executable,
            str(REPO_ROOT / "tools" / "build_capability_qualification_matrix.py"),
            "--repo-root",
            str(REPO_ROOT),
            "--index",
            str(REPO_ROOT / "qualification" / "capabilities" / "evidence-index.v1.json"),
            "--output",
            str(REPO_ROOT / "docs" / "qualification" / "capability-matrix.md"),
            "--check",
        ]
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

    def test_check_mode_does_not_write_output(self):
        index_path = REPO_ROOT / "qualification" / "capabilities" / "evidence-index.v1.json"
        output_bytes = (REPO_ROOT / "docs" / "qualification" / "capability-matrix.md").read_bytes()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "matrix.md"
            output_path.write_bytes((REPO_ROOT / "docs" / "qualification" / "capability-matrix.md").read_bytes())
            before = output_path.stat().st_mtime_ns
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "tools" / "build_capability_qualification_matrix.py"),
                    "--repo-root",
                    str(REPO_ROOT),
                    "--index",
                    str(index_path),
                    "--output",
                    str(output_path),
                    "--check",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertEqual(output_path.read_bytes(), output_bytes)
            self.assertEqual(output_path.stat().st_mtime_ns, before)

    @staticmethod
    def _capability(
        capability_id,
        maturity="experimental",
        rule_version="1.0-exp",
        supported_scopes=None,
        supported_profiles=None,
    ):
        capability = {
            "id": capability_id,
            "implementation": "implemented",
            "maturity": maturity,
            "routing": "on_demand",
            "rule_version": rule_version,
            "module": "engine.synthetic",
            "dependencies": [],
        }
        if supported_scopes is not None:
            capability["supported_scopes"] = supported_scopes
        if supported_profiles is not None:
            capability["supported_profiles"] = supported_profiles
        return capability

    @classmethod
    def _manifest(
        cls,
        maturity="experimental",
        rule_version="1.0-exp",
        supported_scopes=None,
        supported_profiles=None,
    ):
        return {
            "manifest_version": "1.0",
            "capabilities": {
                "synthetic.capability": cls._capability(
                    "synthetic.capability",
                    maturity,
                    rule_version,
                    supported_scopes,
                    supported_profiles,
                )
            },
        }

    @staticmethod
    def _entry(
        capability_id="synthetic.capability",
        scope="default",
        profile_id="default",
        rule_version="1.0-exp",
        evidence_status="needs_verification",
    ):
        return {
            "capability_id": capability_id,
            "scope": scope,
            "profile_id": profile_id,
            "rule_version": rule_version,
            "evidence_status": evidence_status,
            "evidence_refs": [],
            "deterministic_contract": [],
            "boundary_cases": [],
            "fixture_refs": [],
            "regression_refs": [],
            "reference_qualification": [],
            "prospective_evidence": [],
            "failure_modes": [],
            "known_limitations": ["synthetic test scope"],
            "promotion_criteria": [],
            "promotion_decision": "not_decided",
        }

    @staticmethod
    def _ref_for_relative(relative, sha256=None, scope="default"):
        path = REPO_ROOT / relative
        if sha256 is None:
            sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        return {
            "path": relative,
            "sha256": sha256,
            "kind": "repository_evidence_reference",
            "status": "recorded_repo_evidence",
            "source_commit": BASELINE_SHA,
            "scope": scope,
            "profile_id": "default",
            "rule_version": "1.0-exp",
        }

    @classmethod
    def _ref(cls, path, scope="default"):
        return cls._ref_for_relative(path.relative_to(REPO_ROOT).as_posix(), scope=scope)

    @classmethod
    def _index(cls, **entry_overrides):
        entry = cls._entry(**entry_overrides)
        return {
            "schema_version": "1.0",
            "classification": "capability_qualification_evidence_index",
            "source_commit": BASELINE_SHA,
            "entries": [entry],
        }


if __name__ == "__main__":
    unittest.main()
