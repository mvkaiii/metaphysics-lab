#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.distribution.claim_consumption_qualification import (
    evaluate_claim_consumption_qualification,
)


def _report_bytes(report: object) -> bytes:
    return (
        json.dumps(
            report,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate v1.6 Claim Consumption qualification input."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    report = evaluate_claim_consumption_qualification(payload)
    rendered = _report_bytes(report)

    if args.output is None:
        sys.stdout.buffer.write(rendered)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
