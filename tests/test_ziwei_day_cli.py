import subprocess
import sys
import unittest


class ZiweiDayCliTests(unittest.TestCase):
    def test_module_cli_has_no_runpy_warning(self):
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "engine.ziwei.day",
                "--birth-lunar-month", "5",
                "--birth-hour-branch", "戌",
                "--flow-year-branch", "酉",
                "--lunar-month", "1",
                "--lunar-day", "2",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("RuntimeWarning", proc.stderr)
        self.assertIn('"flow_day_ming_branch": "辰"', proc.stdout)


if __name__ == "__main__":
    unittest.main()
