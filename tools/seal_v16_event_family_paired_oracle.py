#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.distribution.event_family_paired_oracle import (
    seal_event_family_paired_oracle,
    verify_event_family_paired_oracle,
)


def _render_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seal or verify a v1.6 paired event-family outcome oracle."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("seal", "verify"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--oracle", required=True, type=Path)
        sub.add_argument("--child-universe", required=True, type=Path)
        sub.add_argument("--receipt", required=True, type=Path)

    args = parser.parse_args()
    oracle = _load(args.oracle)
    universe = _load(args.child_universe)

    if args.command == "seal":
        receipt = seal_event_family_paired_oracle(
            oracle=oracle,
            shared_child_universe=universe,
        )
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_bytes(_render_bytes(receipt))
        return 0

    receipt = _load(args.receipt)
    verified = verify_event_family_paired_oracle(
        oracle=oracle,
        seal_receipt=receipt,
        shared_child_universe=universe,
    )
    sys.stdout.buffer.write(_render_bytes(verified))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
