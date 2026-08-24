import ast
import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = ROOT / "_metaphysics_lab_vendor"
FORBIDDEN_PUBLIC_ROOTS = {"lunar_python", "tzdata"}


def _public_root(name):
    return name.split(".", 1)[0] if name else ""


class VendorImportIsolationTests(unittest.TestCase):
    def test_private_vendor_tree_exists_and_contains_no_symlinks(self):
        self.assertTrue(VENDOR_ROOT.is_dir(), str(VENDOR_ROOT))
        paths = list(VENDOR_ROOT.rglob("*"))
        self.assertTrue(paths)
        self.assertEqual([str(path) for path in paths if path.is_symlink()], [])

    def test_vendored_python_never_imports_public_vendor_names(self):
        violations = []
        python_files = sorted(VENDOR_ROOT.rglob("*.py"))
        self.assertTrue(python_files)
        for path in python_files:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if _public_root(alias.name) in FORBIDDEN_PUBLIC_ROOTS:
                            violations.append((path.relative_to(ROOT).as_posix(), node.lineno, alias.name))
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    if _public_root(node.module or "") in FORBIDDEN_PUBLIC_ROOTS:
                        violations.append((path.relative_to(ROOT).as_posix(), node.lineno, node.module))
        self.assertEqual(violations, [])

    def test_private_namespaces_import_without_public_aliases(self):
        lunar = importlib.import_module("_metaphysics_lab_vendor.lunar_python")
        tzdata = importlib.import_module("_metaphysics_lab_vendor.tzdata")
        self.assertTrue(hasattr(lunar, "Solar"))
        self.assertEqual(getattr(tzdata, "__version__", None), "2026.3")
        self.assertEqual(getattr(tzdata, "IANA_VERSION", None), "2026c")


if __name__ == "__main__":
    unittest.main()
