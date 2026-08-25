import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from engine.vendor.materialize import materialize_private_vendor


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PUBLIC_ROOTS = {"lunar_python", "tzdata"}


def _public_root(name):
    return name.split(".", 1)[0] if name else ""


class VendorImportIsolationTests(unittest.TestCase):
    def test_materialized_private_vendor_tree_contains_no_symlinks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vendor_root = materialize_private_vendor(ROOT, Path(temp_dir))
            self.assertTrue(vendor_root.is_dir(), str(vendor_root))
            paths = list(vendor_root.rglob("*"))
            self.assertTrue(paths)
            self.assertEqual([str(path) for path in paths if path.is_symlink()], [])

    def test_vendored_python_never_imports_public_vendor_names(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vendor_root = materialize_private_vendor(ROOT, Path(temp_dir))
            violations = []
            python_files = sorted(vendor_root.rglob("*.py"))
            self.assertTrue(python_files)
            for path in python_files:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if _public_root(alias.name) in FORBIDDEN_PUBLIC_ROOTS:
                                violations.append((path.relative_to(vendor_root).as_posix(), node.lineno, alias.name))
                    elif isinstance(node, ast.ImportFrom) and node.level == 0:
                        if _public_root(node.module or "") in FORBIDDEN_PUBLIC_ROOTS:
                            violations.append((path.relative_to(vendor_root).as_posix(), node.lineno, node.module))
            self.assertEqual(violations, [])

    def test_private_namespaces_import_from_materialized_shards_under_python_s(self):
        script = r'''
import importlib
import sys
import tempfile
from pathlib import Path
from engine.vendor.materialize import materialize_private_vendor

root = Path.cwd()
with tempfile.TemporaryDirectory() as temp_dir:
    materialize_private_vendor(root, Path(temp_dir))
    sys.path.insert(0, temp_dir)
    lunar = importlib.import_module("_metaphysics_lab_vendor.lunar_python")
    tzdata = importlib.import_module("_metaphysics_lab_vendor.tzdata")
    assert hasattr(lunar, "Solar")
    assert getattr(tzdata, "__version__", None) == "2026.3"
    assert getattr(tzdata, "IANA_VERSION", None) == "2026c"
'''
        completed = subprocess.run(
            [sys.executable, "-S", "-c", script],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
