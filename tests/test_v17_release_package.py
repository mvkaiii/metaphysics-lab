import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools import build_release_package


class V17ReleasePackageTests(unittest.TestCase):
    def test_release_package_identity_and_members_are_v171_patch(self):
        self.assertEqual(build_release_package.RELEASE_VERSION, "1.7.1")
        self.assertEqual(
            build_release_package.USER_PACKAGE_NAME,
            "Metaphysics-Lab-v1.7.1-User-Package.zip",
        )
        self.assertEqual(
            set(build_release_package.USER_ASSETS),
            {"metaphysics_core.md", "metaphysics_lab.py", "project_instructions.txt"},
        )

    def test_verify_with_explicit_output_writes_verified_package(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            distribution = Path(temp_dir) / "dist"
            distribution.mkdir()
            for name in build_release_package.USER_ASSETS:
                (distribution / name).write_text(f"fixture:{name}\n", encoding="utf-8")
            output = Path(temp_dir) / "verified.zip"

            with redirect_stdout(io.StringIO()):
                result = build_release_package.main(
                    [
                        "--distribution-dir",
                        str(distribution),
                        "--verify",
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertTrue(output.is_file())
            self.assertEqual(
                output.read_bytes(),
                build_release_package.render_user_package(distribution),
            )


if __name__ == "__main__":
    unittest.main()
