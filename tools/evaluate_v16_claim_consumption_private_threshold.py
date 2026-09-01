from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.distribution.claim_consumption_private_threshold import (
    evaluate_claim_consumption_private_threshold,
)


def _load(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _canonical_line(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate v1.6 claim-consumption private threshold gate")
    parser.add_argument("--policy", required=True)
    parser.add_argument("--sampling-receipt", required=True)
    parser.add_argument("--oracle-receipt", required=True)
    parser.add_argument("--evaluation-identity-receipt", required=True)
    parser.add_argument("--q1-report", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    report = evaluate_claim_consumption_private_threshold(
        _load(args.policy),
        _load(args.sampling_receipt),
        _load(args.oracle_receipt),
        _load(args.evaluation_identity_receipt),
        _load(args.q1_report),
    )
    rendered = _canonical_line(report)
    if args.output:
        Path(args.output).write_bytes(rendered)
    else:
        import sys

        sys.stdout.buffer.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
