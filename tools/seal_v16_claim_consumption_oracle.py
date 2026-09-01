#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.distribution.claim_consumption_oracle_seal import (
    build_public_oracle_seal_receipt,
    join_sealed_oracle_with_candidate,
    seal_claim_consumption_oracle,
    verify_oracle_seal,
)


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _render_bytes(value: object) -> bytes:
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


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_render_bytes(value))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seal, verify, or join v1.6 Claim Consumption oracle data."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    seal_parser = subparsers.add_parser("seal")
    seal_parser.add_argument("--oracle", required=True, type=Path)
    seal_parser.add_argument("--sealed-at", required=True)
    seal_parser.add_argument("--seal-out", required=True, type=Path)
    seal_parser.add_argument("--receipt-out", type=Path)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--oracle", required=True, type=Path)
    verify_parser.add_argument("--seal", required=True, type=Path)
    verify_parser.add_argument("--output", type=Path)

    join_parser = subparsers.add_parser("join")
    join_parser.add_argument("--oracle", required=True, type=Path)
    join_parser.add_argument("--seal", required=True, type=Path)
    join_parser.add_argument("--candidate-output", required=True, type=Path)
    join_parser.add_argument("--output", required=True, type=Path)
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    if args.mode == "seal":
        oracle = _load_json(args.oracle)
        seal = seal_claim_consumption_oracle(oracle, args.sealed_at)
        _write(args.seal_out, seal)
        if args.receipt_out is not None:
            _write(args.receipt_out, build_public_oracle_seal_receipt(seal))
        return 0

    if args.mode == "verify":
        oracle = _load_json(args.oracle)
        seal = _load_json(args.seal)
        verification = verify_oracle_seal(oracle, seal)
        if args.output is None:
            sys.stdout.buffer.write(_render_bytes(verification))
        else:
            _write(args.output, verification)
        return 0

    if args.mode == "join":
        oracle = _load_json(args.oracle)
        seal = _load_json(args.seal)
        candidate_output = _load_json(args.candidate_output)
        joined = join_sealed_oracle_with_candidate(oracle, seal, candidate_output)
        _write(args.output, joined)
        return 0

    raise AssertionError("unreachable parser mode")


if __name__ == "__main__":
    raise SystemExit(main())
