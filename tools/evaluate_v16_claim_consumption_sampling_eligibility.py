from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.distribution.claim_consumption_sampling_eligibility import (
    build_sampling_eligibility_receipt,
    build_sampling_frame,
    validate_claim_universe_lock,
    validate_sampling_frame,
    validate_sampling_protocol,
    validate_sampling_source_manifest,
    verify_oracle_identity_against_sampling_frame,
    verify_sampling_eligibility_receipt,
)


def _load(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _canonical_line(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _emit(value: object, output: str | None, *, require_output: bool) -> None:
    if require_output and not output:
        raise ValueError("this private-artifact mode requires explicit --output")
    rendered = _canonical_line(value)
    if output:
        Path(output).write_bytes(rendered)
    else:
        sys.stdout.buffer.write(rendered)


def _add_protocol(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--protocol", required=True)


def _add_source(parser: argparse.ArgumentParser) -> None:
    _add_protocol(parser)
    parser.add_argument("--source-manifest", required=True)


def _add_claim_lock(parser: argparse.ArgumentParser) -> None:
    _add_source(parser)
    parser.add_argument("--claim-universe-lock", required=True)


def _add_frame_inputs(parser: argparse.ArgumentParser) -> None:
    _add_claim_lock(parser)
    parser.add_argument("--frame", required=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate v1.6 complete-census sampling eligibility S1")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate-protocol")
    _add_protocol(p)
    p.add_argument("--output")

    p = sub.add_parser("validate-source-manifest")
    _add_source(p)
    p.add_argument("--output")

    p = sub.add_parser("validate-claim-universe-lock")
    _add_claim_lock(p)
    p.add_argument("--output")

    p = sub.add_parser("build-frame")
    _add_claim_lock(p)
    p.add_argument("--locked-at", required=True)
    p.add_argument("--output")

    p = sub.add_parser("validate-frame")
    _add_frame_inputs(p)
    p.add_argument("--output")

    p = sub.add_parser("seal-receipt")
    _add_frame_inputs(p)
    p.add_argument("--sealed-at", required=True)
    p.add_argument("--output")

    p = sub.add_parser("verify-receipt")
    p.add_argument("--receipt", required=True)
    p.add_argument("--output")

    p = sub.add_parser("verify-oracle-identity")
    p.add_argument("--frame", required=True)
    p.add_argument("--oracle", required=True)
    p.add_argument("--output")

    args = parser.parse_args()
    if args.command == "validate-protocol":
        _emit(validate_sampling_protocol(_load(args.protocol)), args.output, require_output=False)
    elif args.command == "validate-source-manifest":
        _emit(
            validate_sampling_source_manifest(_load(args.source_manifest), _load(args.protocol)),
            args.output,
            require_output=True,
        )
    elif args.command == "validate-claim-universe-lock":
        _emit(
            validate_claim_universe_lock(
                _load(args.claim_universe_lock), _load(args.source_manifest), _load(args.protocol)
            ),
            args.output,
            require_output=True,
        )
    elif args.command == "build-frame":
        _emit(
            build_sampling_frame(
                _load(args.source_manifest),
                _load(args.claim_universe_lock),
                _load(args.protocol),
                args.locked_at,
            ),
            args.output,
            require_output=True,
        )
    elif args.command == "validate-frame":
        _emit(
            validate_sampling_frame(
                _load(args.frame),
                _load(args.source_manifest),
                _load(args.claim_universe_lock),
                _load(args.protocol),
            ),
            args.output,
            require_output=True,
        )
    elif args.command == "seal-receipt":
        _emit(
            build_sampling_eligibility_receipt(
                _load(args.frame),
                _load(args.source_manifest),
                _load(args.claim_universe_lock),
                _load(args.protocol),
                args.sealed_at,
            ),
            args.output,
            require_output=True,
        )
    elif args.command == "verify-receipt":
        _emit(verify_sampling_eligibility_receipt(_load(args.receipt)), args.output, require_output=False)
    else:
        _emit(
            verify_oracle_identity_against_sampling_frame(_load(args.frame), _load(args.oracle)),
            args.output,
            require_output=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
