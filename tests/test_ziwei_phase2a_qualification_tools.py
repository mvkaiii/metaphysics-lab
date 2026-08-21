import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.qualify_ziwei_phase2a_public import (
    parse_iztro_heavenly_stems,
    qualify_public_profile,
)

IZTRO_FRAGMENT = """
export const heavenlyStems = {
  jiaHeavenly: { mutagen: ['lianzhenMaj', 'pojunMaj', 'wuquMaj', 'taiyangMaj'] },
  yiHeavenly: { mutagen: ['tianjiMaj', 'tianliangMaj', 'ziweiMaj', 'taiyinMaj'] },
  bingHeavenly: { mutagen: ['tiantongMaj', 'tianjiMaj', 'wenchangMin', 'lianzhenMaj'] },
  dingHeavenly: { mutagen: ['taiyinMaj', 'tiantongMaj', 'tianjiMaj', 'jumenMaj'] },
  wuHeavenly: { mutagen: ['tanlangMaj', 'taiyinMaj', 'youbiMin', 'tianjiMaj'] },
  jiHeavenly: { mutagen: ['wuquMaj', 'tanlangMaj', 'tianliangMaj', 'wenquMin'] },
  gengHeavenly: { mutagen: ['taiyangMaj', 'wuquMaj', 'taiyinMaj', 'tiantongMaj'] },
  xinHeavenly: { mutagen: ['jumenMaj', 'taiyangMaj', 'wenquMin', 'wenchangMin'] },
  renHeavenly: { mutagen: ['tianliangMaj', 'ziweiMaj', 'zuofuMin', 'wuquMaj'] },
  guiHeavenly: { mutagen: ['pojunMaj', 'jumenMaj', 'taiyinMaj', 'tanlangMaj'] },
};
"""


class ZiweiPublicQualificationTests(unittest.TestCase):
    def test_parser_extracts_ten_stems(self):
        table = parse_iztro_heavenly_stems(IZTRO_FRAGMENT)
        self.assertEqual(len(table), 10)
        self.assertEqual(table["丙"], ("天同", "天機", "文昌", "廉貞"))

    def test_exact_external_table_is_40_of_40_pass(self):
        table = parse_iztro_heavenly_stems(IZTRO_FRAGMENT)
        evidence = qualify_public_profile(
            table,
            "814b77e6371e1050cac31bbf674db3c3138fcfde",
            "2026-08-21T00:00:00Z",
        )
        self.assertEqual(evidence["cases_checked"], 40)
        self.assertEqual(evidence["cases_matched"], 40)
        self.assertEqual(evidence["mismatches"], [])
        self.assertEqual(evidence["status"], "PASS")

    def test_one_external_mismatch_is_fail(self):
        table = dict(parse_iztro_heavenly_stems(IZTRO_FRAGMENT))
        table["丙"] = ("天同", "天機", "文昌", "天機")
        evidence = qualify_public_profile(
            table,
            "814b77e6371e1050cac31bbf674db3c3138fcfde",
            "2026-08-21T00:00:00Z",
        )
        self.assertEqual(evidence["cases_matched"], 39)
        self.assertEqual(evidence["status"], "FAIL")

    def test_direct_cli_invocation_can_import_project_engine(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "heavenlyStems.ts"
            output_path = Path(tmp_dir) / "evidence.json"
            source_path.write_text(IZTRO_FRAGMENT, encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "tools/qualify_ziwei_phase2a_public.py",
                    "--source-ts",
                    str(source_path),
                    "--source-revision",
                    "814b77e6371e1050cac31bbf674db3c3138fcfde",
                    "--run-timestamp",
                    "2026-08-21T00:00:00Z",
                    "--output",
                    str(output_path),
                ],
                cwd=str(repo_root),
                text=True,
                capture_output=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            evidence = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(evidence["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
