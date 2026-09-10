import unittest

from tools import build_release_package


class V17ReleasePackageTests(unittest.TestCase):
    def test_release_package_identity_and_members_are_v170(self):
        self.assertEqual(build_release_package.RELEASE_VERSION, "1.7.0")
        self.assertEqual(
            build_release_package.USER_PACKAGE_NAME,
            "Metaphysics-Lab-v1.7.0-User-Package.zip",
        )
        self.assertEqual(
            set(build_release_package.USER_ASSETS),
            {"metaphysics_core.md", "metaphysics_lab.py", "project_instructions.txt"},
        )


if __name__ == "__main__":
    unittest.main()
