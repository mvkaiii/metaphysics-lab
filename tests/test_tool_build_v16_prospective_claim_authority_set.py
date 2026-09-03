from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from engine.distribution.prospective_claim_authority_set import build_claim_authority_set
from tests.test_distribution_prospective_claim_authority_set import ROOT, _members


TOOL = ROOT / "tools" / "build_v16_prospective_claim_authority_set.py"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


class ProspectiveClaimAuthoritySetCliTests(unittest.TestCase):
    def test_cli_builds_canonical_private_artifact_without_stdout(self) -> None:
        protocol, source, members = _members()
        expected = build_claim_authority_set(protocol, source, members, promotion_allowed=False)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            protocol_path = root / "protocol.json"
            source_path = root / "source.json"
            members_path = root / "members.json"
            output_path = root / "authority.json"
            _write_json(protocol_path, protocol)
            _write_json(source_path, source)
            _write_json(members_path, members)

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "--protocol",
                    str(protocol_path),
                    "--source-manifest",
                    str(source_path),
                    "--case-authorities",
                    str(members_path),
                    "--output",
                    str(output_path),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stdout, "")
            self.assertTrue(output_path.exists())
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8")), expected)
            rendered = output_path.read_bytes()
            self.assertTrue(rendered.endswith(b"\n"))
            self.assertEqual(rendered.count(b"\n"), 1)

    def test_cli_requires_explicit_output(self) -> None:
        protocol, source, members = _members()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            protocol_path = root / "protocol.json"
            source_path = root / "source.json"
            members_path = root / "members.json"
            _write_json(protocol_path, protocol)
            _write_json(source_path, source)
            _write_json(members_path, members)

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "--protocol",
                    str(protocol_path),
                    "--source-manifest",
                    str(source_path),
                    "--case-authorities",
                    str(members_path),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
