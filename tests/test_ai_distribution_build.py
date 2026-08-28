import base64
import hashlib
import importlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ARTIFACTS = [
    "metaphysics_core.md",
    "metaphysics_lab.py",
    "project_instructions.txt",
]
FORBIDDEN_FIXED_MD = (
    "Phase 2C",
    "600/600",
    "814b77e6",
    "ziwei.flowing_stars =",
)


class AIDistributionBuildTests(unittest.TestCase):
    @staticmethod
    def builder():
        spec = importlib.util.find_spec("tools.build_ai_distribution")
        if spec is None:
            raise AssertionError("tools.build_ai_distribution must exist")
        return importlib.import_module("tools.build_ai_distribution")

    @staticmethod
    def _copy_distribution_fixture(target: Path) -> None:
        for relative in ("engine", "templates", "vendor", "data/birth_places", "core"):
            source = ROOT / relative
            destination = target / relative
            shutil.copytree(source, destination)

    def _assert_build_fails_without_artifacts(self, root: Path, expected_error=None):
        builder = self.builder()
        output = root / "dist" / "ai"
        with self.assertRaises(Exception) as caught:
            builder.build_distribution(root, output)
        if expected_error is not None:
            self.assertEqual(str(caught.exception), expected_error)
        if output.exists():
            self.assertEqual(
                [path.name for path in output.iterdir() if path.is_file()],
                [],
                "integrity failure must happen before artifact emission",
            )

    def test_same_source_tree_builds_byte_identical_three_artifacts(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = Path(first_dir)
            second = Path(second_dir)
            builder.build_distribution(ROOT, first)
            builder.build_distribution(ROOT, second)
            self.assertEqual(sorted(path.name for path in first.iterdir()), EXPECTED_ARTIFACTS)
            self.assertEqual(sorted(path.name for path in second.iterdir()), EXPECTED_ARTIFACTS)
            for name in EXPECTED_ARTIFACTS:
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes(), name)

    def test_project_instructions_is_normalized_exact_core_prompt(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as output_dir:
            output = Path(output_dir)
            builder.build_distribution(ROOT, output)
            expected = (ROOT / "core" / "核心提示詞.md").read_text(encoding="utf-8").replace("\r\n", "\n").rstrip() + "\n"
            actual = (output / "project_instructions.txt").read_text(encoding="utf-8")
            self.assertEqual(actual, expected)

    def test_fixed_markdown_contains_stable_source_markers_but_no_dynamic_snapshot(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as output_dir:
            output = Path(output_dir)
            builder.build_distribution(ROOT, output)
            core = (output / "metaphysics_core.md").read_text(encoding="utf-8")
            instructions = (output / "project_instructions.txt").read_text(encoding="utf-8")
            self.assertIn("Source: core/AI工作流程.md", core)
            self.assertIn("Source: core/命理分析作業規範.md", core)
            combined = core + "\n" + instructions
            for forbidden in FORBIDDEN_FIXED_MD:
                self.assertNotIn(forbidden, combined)
            self.assertNotIn("命理推導計算規則.md", core)

    def test_bundle_has_generated_marker_digest_and_no_absolute_builder_path(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as output_dir:
            output = Path(output_dir)
            builder.build_distribution(ROOT, output)
            text = (output / "metaphysics_lab.py").read_text(encoding="utf-8")
            self.assertIn("GENERATED FILE - DO NOT EDIT", text)
            self.assertIn("SOURCE_DIGEST =", text)
            self.assertIn("BUILD_FORMAT_VERSION = '1.1'", text)
            self.assertNotIn(str(ROOT), text)
            self.assertNotIn("/home/runner/", text)
            self.assertNotIn("qualification/", text)
            self.assertNotIn("tests/", text)

    def test_bundle_input_discovery_is_allowlisted_and_includes_portable_data_when_present(self):
        builder = self.builder()
        paths = builder.discover_bundle_inputs(ROOT)
        self.assertIn("engine/distribution/runtime.py", paths)
        self.assertIn("templates/case/00_project_index.md.tmpl", paths)
        self.assertIn("data/birth_places/schema.v1.json", paths)
        self.assertTrue(any(path.startswith("vendor/artifacts/") for path in paths))
        self.assertTrue(all(not path.startswith("tests/") for path in paths))
        self.assertTrue(all(not path.startswith("qualification/") for path in paths))
        self.assertTrue(all(not path.startswith("docs/") for path in paths))
        allowed = (
            "engine/",
            "templates/",
            "_metaphysics_lab_vendor/",
            "vendor/artifacts/",
            "vendor/manifest.json",
            "vendor/licenses/",
            "data/birth_places/registry.v1.json",
            "data/birth_places/schema.v1.json",
            "data/birth_places/SOURCES.md",
        )
        for path in paths:
            self.assertTrue(any(path == prefix or path.startswith(prefix) for prefix in allowed), path)

    def test_build_file_record_normalizes_first_party_text_and_preserves_binary_bytes(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "engine").mkdir()
            (root / "engine" / "sample.py").write_bytes(b"print('x')\r\n")
            (root / "_metaphysics_lab_vendor" / "tzdata" / "zoneinfo" / "Asia").mkdir(parents=True)
            binary = b"TZif\x00\xff\x10\r\n"
            (root / "_metaphysics_lab_vendor" / "tzdata" / "zoneinfo" / "Asia" / "Taipei").write_bytes(binary)

            text_record = builder.build_file_record(root, "engine/sample.py")
            binary_record = builder.build_file_record(
                root, "_metaphysics_lab_vendor/tzdata/zoneinfo/Asia/Taipei"
            )

            self.assertEqual(text_record["encoding"], "base64")
            self.assertEqual(base64.b64decode(text_record["content"]), b"print('x')\n")
            self.assertEqual(binary_record["encoding"], "base64")
            self.assertEqual(base64.b64decode(binary_record["content"]), binary)
            self.assertEqual(binary_record["sha256"], hashlib.sha256(binary).hexdigest())

    def test_payload_carries_binary_records_losslessly(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "_metaphysics_lab_vendor" / "tzdata" / "zoneinfo" / "Asia" / "Taipei"
            target.parent.mkdir(parents=True)
            binary = b"TZif2\x00\xff\x80\x10\r\n"
            target.write_bytes(binary)

            encoded, digest, source_files = builder._payload(root)
            raw = __import__("zlib").decompress(base64.b64decode(encoded.encode("ascii")))
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            payload = json.loads(raw.decode("utf-8"))
            records = {record["path"]: record for record in payload["files"]}
            record = records["_metaphysics_lab_vendor/tzdata/zoneinfo/Asia/Taipei"]
            self.assertEqual(record["encoding"], "base64")
            self.assertEqual(base64.b64decode(record["content"]), binary)
            self.assertEqual(record["sha256"], hashlib.sha256(binary).hexdigest())
            self.assertEqual(source_files[record["path"]], record["sha256"])

    def test_source_digest_covers_vendor_registry_and_license_inputs(self):
        builder = self.builder()
        source_paths = builder.discover_bundle_inputs(ROOT)
        vendor_path = next(path for path in source_paths if path.startswith("vendor/artifacts/"))
        license_path = next(path for path in source_paths if path.startswith("vendor/licenses/"))
        mutation_paths = (
            vendor_path,
            "data/birth_places/registry.v1.json",
            license_path,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in source_paths:
                source = ROOT / relative
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())

            _, baseline_digest, _ = builder._payload(root)
            for relative in mutation_paths:
                with self.subTest(relative=relative):
                    target = root / relative
                    original = target.read_bytes()
                    target.write_bytes(original + b"\nportable-bundle-digest-mutation")
                    _, mutated_digest, _ = builder._payload(root)
                    self.assertNotEqual(mutated_digest, baseline_digest)
                    target.write_bytes(original)
                    _, restored_digest, _ = builder._payload(root)
                    self.assertEqual(restored_digest, baseline_digest)

    def test_payload_records_are_base64_only_and_digest_covers_binary_safe_json(self):
        builder = self.builder()
        encoded, digest, source_files = builder._payload(ROOT)
        raw = __import__("zlib").decompress(base64.b64decode(encoded.encode("ascii")))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
        payload = json.loads(raw.decode("utf-8"))
        self.assertEqual(payload["build_format_version"], "1.1")
        self.assertTrue(payload["files"])
        self.assertTrue(any(record["path"].startswith("vendor/artifacts/") for record in payload["files"]))
        for record in payload["files"]:
            self.assertEqual(record["encoding"], "base64")
            self.assertNotIn("text", record)
            decoded = base64.b64decode(record["content"])
            self.assertEqual(hashlib.sha256(decoded).hexdigest(), record["sha256"])
            self.assertEqual(source_files[record["path"]], record["sha256"])

    def test_vendor_shard_tamper_fails_before_artifact_emission(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._copy_distribution_fixture(root)
            manifest = json.loads((root / "vendor/manifest.json").read_text(encoding="utf-8"))
            shard = root / manifest["packages"][0]["artifact_shards"][0]
            original = shard.read_bytes()
            replacement = b"A" if original[:1] != b"A" else b"B"
            shard.write_bytes(replacement + original[1:])
            self._assert_build_fails_without_artifacts(root)

    def test_manifest_tree_hash_tamper_fails_before_artifact_emission(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._copy_distribution_fixture(root)
            manifest_path = root / "vendor/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["packages"][0]["vendored_tree_sha256"] = "0" * 64
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            self._assert_build_fails_without_artifacts(root)

    def test_invalid_registry_fails_before_artifact_emission(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._copy_distribution_fixture(root)
            registry = root / "data/birth_places/registry.v1.json"
            registry.write_bytes(registry.read_bytes() + b"\n{")
            self._assert_build_fails_without_artifacts(root)

    def test_missing_required_vendor_license_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._copy_distribution_fixture(root)
            manifest = json.loads((root / "vendor/manifest.json").read_text(encoding="utf-8"))
            license_path = root / manifest["packages"][0]["license_file"]
            license_path.unlink()
            self._assert_build_fails_without_artifacts(root, "vendor_license_missing")

    def test_distribution_size_limit_is_fixed_at_five_mib(self):
        builder = self.builder()
        self.assertEqual(builder.MAX_BUNDLE_BYTES, 5 * 1024 * 1024)
        builder.enforce_size_limit("x" * builder.MAX_BUNDLE_BYTES)
        with self.assertRaisesRegex(RuntimeError, "^distribution_size_limit_exceeded$"):
            builder.enforce_size_limit("x" * (builder.MAX_BUNDLE_BYTES + 1))

    def test_render_distribution_applies_size_guard_to_generated_script(self):
        builder = self.builder()
        oversized = "x" * (5 * 1024 * 1024 + 1)
        with mock.patch.object(builder, "_render_bundle", return_value=oversized):
            with self.assertRaisesRegex(RuntimeError, "^distribution_size_limit_exceeded$"):
                builder.render_distribution(ROOT)

    def test_check_mode_detects_drift(self):
        self.builder()
        with tempfile.TemporaryDirectory() as output_dir:
            output = Path(output_dir)
            subprocess.run(
                [sys.executable, "tools/build_ai_distribution.py", "--output-dir", str(output)],
                cwd=str(ROOT),
                check=True,
                text=True,
                capture_output=True,
            )
            clean = subprocess.run(
                [sys.executable, "tools/build_ai_distribution.py", "--output-dir", str(output), "--check"],
                cwd=str(ROOT),
                text=True,
                capture_output=True,
            )
            self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
            with (output / "project_instructions.txt").open("a", encoding="utf-8") as handle:
                handle.write("drift\n")
            drift = subprocess.run(
                [sys.executable, "tools/build_ai_distribution.py", "--output-dir", str(output), "--check"],
                cwd=str(ROOT),
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(drift.returncode, 0)
            self.assertIn("project_instructions.txt", drift.stdout + drift.stderr)


if __name__ == "__main__":
    unittest.main()
