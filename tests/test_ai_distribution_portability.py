import importlib.util
import json
import os
import runpy
import shutil
import socket
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BIRTH = {
    "sex": "male",
    "birth_date": "1984-03-13",
    "birth_time": "19:20",
    "birth_place": "台北市",
}


class AIDistributionPortabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools import build_ai_distribution as builder

        cls._build_temp = tempfile.TemporaryDirectory()
        cls._build_root = Path(cls._build_temp.name)
        builder.build_distribution(ROOT, cls._build_root)
        cls.bundle = cls._build_root / "metaphysics_lab.py"
        if not cls.bundle.is_file():
            raise AssertionError("fresh portable bundle was not generated")

    @classmethod
    def tearDownClass(cls):
        cls._build_temp.cleanup()

    @staticmethod
    def _clean_env():
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        env["PYTHONNOUSERSITE"] = "1"
        return env

    @classmethod
    def run_clean_bundle(cls, action, payload=None):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle = root / "metaphysics_lab.py"
            shutil.copyfile(cls.bundle, bundle)
            if sorted(path.name for path in root.iterdir()) != ["metaphysics_lab.py"]:
                raise AssertionError("clean sandbox must contain only metaphysics_lab.py")
            request = json.dumps(
                {"action": action, "payload": {} if payload is None else payload},
                ensure_ascii=False,
            )
            completed = subprocess.run(
                [sys.executable, "-S", str(bundle), "request", "--input", "-"],
                cwd=str(root),
                input=request,
                text=True,
                capture_output=True,
                env=cls._clean_env(),
            )
            if completed.returncode != 0:
                raise AssertionError(completed.stdout + completed.stderr)
            lines = [line for line in completed.stdout.splitlines() if line.strip()]
            if len(lines) != 1:
                raise AssertionError("clean bundle must emit exactly one JSON object: %r" % completed.stdout)
            return json.loads(lines[0])

    def test_clean_python_s_builds_taipei_natal_from_birth_only(self):
        result = self.run_clean_bundle("build_natal", {"birth": BIRTH})
        self.assertTrue(result["ok"], result)
        data = result["data"]
        location = data["resolved_location"]
        project = data["project_natal"]
        self.assertEqual(location["provider_name"], "metaphysics_lab_offline_registry")
        self.assertEqual(location["timezone"], "Asia/Taipei")
        self.assertEqual(set(project["bazi"]["pillars"]), {"year", "month", "day", "hour"})
        self.assertEqual(len(project["ziwei"]["palaces"]), 12)
        self.assertIsNotNone(data["normalized_natal"]["project"])

    def test_clean_python_s_runtime_info_reports_bundled_core_available(self):
        result = self.run_clean_bundle("runtime_info", {})
        self.assertTrue(result["ok"], result)
        data = result["data"]
        bundled = data["bundled_dependencies"]
        self.assertEqual(bundled["lunar-python"]["version"], "1.4.8")
        self.assertEqual(bundled["tzdata"]["version"], "2026.3")
        self.assertTrue(bundled["lunar-python"]["available"])
        self.assertTrue(bundled["tzdata"]["available"])
        self.assertFalse(bundled["lunar-python"]["runtime_uses_environment_package"])
        self.assertFalse(bundled["tzdata"]["runtime_uses_environment_package"])
        optional = data["optional_external_dependencies"]
        self.assertFalse(optional["geopy"]["installed"])
        self.assertFalse(optional["timezonefinder"]["installed"])

    def test_fake_public_packages_cannot_change_project_natal(self):
        baseline = self.run_clean_bundle("build_natal", {"birth": BIRTH})
        self.assertTrue(baseline["ok"], baseline)

        for version in ("0.0", "1.4.7", "999.0", "fake"):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                bundle = root / "metaphysics_lab.py"
                shutil.copyfile(self.bundle, bundle)
                for package_name in ("lunar_python", "tzdata"):
                    package = root / package_name
                    package.mkdir()
                    (package / "__init__.py").write_text(
                        "__version__ = %r\nPUBLIC_FAKE = True\n" % version,
                        encoding="utf-8",
                    )
                request = json.dumps(
                    {"action": "build_natal", "payload": {"birth": BIRTH}},
                    ensure_ascii=False,
                )
                completed = subprocess.run(
                    [sys.executable, "-S", str(bundle), "request", "--input", "-"],
                    cwd=str(root),
                    input=request,
                    text=True,
                    capture_output=True,
                    env=self._clean_env(),
                )
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                polluted = json.loads(completed.stdout)
                self.assertEqual(polluted, baseline)

    def test_preloaded_public_modules_cannot_change_project_natal(self):
        baseline = self.run_clean_bundle("build_natal", {"birth": BIRTH})
        self.assertTrue(baseline["ok"], baseline)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle = root / "metaphysics_lab.py"
            shutil.copyfile(self.bundle, bundle)
            launcher = root / "launcher.py"
            launcher.write_text(
                "import runpy, sys, types\n"
                "for name in ('lunar_python', 'tzdata'):\n"
                "    module = types.ModuleType(name)\n"
                "    module.__version__ = '999.0-fake'\n"
                "    module.PUBLIC_FAKE = True\n"
                "    sys.modules[name] = module\n"
                "sys.argv = [sys.argv[1], 'request', '--input', '-']\n"
                "runpy.run_path(sys.argv[0], run_name='__main__')\n",
                encoding="utf-8",
            )
            request = json.dumps(
                {"action": "build_natal", "payload": {"birth": BIRTH}},
                ensure_ascii=False,
            )
            completed = subprocess.run(
                [sys.executable, "-S", str(launcher), str(bundle)],
                cwd=str(root),
                input=request,
                text=True,
                capture_output=True,
                env=self._clean_env(),
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            polluted = json.loads(completed.stdout)
            self.assertEqual(polluted, baseline)

    def test_offline_taipei_build_never_opens_network_socket(self):
        spec = importlib.util.spec_from_file_location("metaphysics_lab_portability_bundle", self.bundle)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        def forbidden_socket(*_args, **_kwargs):
            raise AssertionError("offline-supported natal build must not open a network socket")

        try:
            with mock.patch.object(socket, "socket", side_effect=forbidden_socket):
                result = module.dispatch("build_natal", {"birth": BIRTH})
            self.assertTrue(result["ok"], result)
            self.assertEqual(
                result["data"]["resolved_location"]["provider_name"],
                "metaphysics_lab_offline_registry",
            )
        finally:
            module._cleanup_runtime_root()


if __name__ == "__main__":
    unittest.main()
