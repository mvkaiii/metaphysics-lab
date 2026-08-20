import subprocess
import sys
import unittest


class ZiweiHourCliTests(unittest.TestCase):
    def test_module_cli_has_no_runpy_warning_and_outputs_hour(self):
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "engine.ziwei.hour",
                "--birth-lunar-month", "5",
                "--birth-hour-branch", "戌",
                "--flow-year-branch", "酉",
                "--lunar-month", "1",
                "--lunar-day", "2",
                "--hour-branch", "丑",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("RuntimeWarning", proc.stderr)
        self.assertIn('"flow_hour_ming_branch": "巳"', proc.stdout)


if __name__ == "__main__":
    unittest.main()
