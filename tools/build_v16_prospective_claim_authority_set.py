from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.distribution.prospective_claim_authority_set import build_claim_authority_set


def _load(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _canonical_line(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a private v1.6 prospective composite claim-authority set"
    )
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--case-authorities", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = build_claim_authority_set(
        _load(args.protocol),
        _load(args.source_manifest),
        _load(args.case_authorities),
        promotion_allowed=False,
    )
    Path(args.output).write_text(_canonical_line(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
