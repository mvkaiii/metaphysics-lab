from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.distribution.claim_consumption_case_intake import (
    ELIGIBLE_STATUS,
    build_intake_registry,
    validate_intake_registry,
    validate_intake_registry_successor,
)


def _load(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_private(value: object, output: str | None) -> None:
    if not output:
        raise ValueError("private registry build requires explicit --output")
    Path(output).write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _summary(registry: dict) -> dict:
    records = registry["records"]
    return {
        "schema_version": "v1.6-claim-consumption-prospective-case-intake-verification.v1",
        "status": "VALID",
        "record_count": len(records),
        "eligible_for_s1_source_count": sum(row["eligibility_status"] == ELIGIBLE_STATUS for row in records),
        "registry_digest": registry["registry_digest"],
        "promotion_allowed": False,
    }


def _emit_summary(value: object) -> None:
    sys.stdout.write(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate v1.6 prospective private case intake registry")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build")
    build.add_argument("--records", required=True)
    build.add_argument("--locked-at", required=True)
    build.add_argument("--previous-registry")
    build.add_argument("--output")

    validate = sub.add_parser("validate")
    validate.add_argument("--registry", required=True)

    successor = sub.add_parser("validate-successor")
    successor.add_argument("--previous", required=True)
    successor.add_argument("--current", required=True)

    args = parser.parse_args()
    if args.command == "build":
        previous = _load(args.previous_registry) if args.previous_registry else None
        previous_digest = None
        if previous is not None:
            previous = validate_intake_registry(previous)
            previous_digest = previous["registry_digest"]
        registry = build_intake_registry(_load(args.records), args.locked_at, previous_registry_digest=previous_digest)
        if previous is not None:
            validate_intake_registry_successor(registry, previous)
        _write_private(registry, args.output)
        return 0
    if args.command == "validate":
        registry = validate_intake_registry(_load(args.registry))
        _emit_summary(_summary(registry))
        return 0
    current = validate_intake_registry_successor(_load(args.current), _load(args.previous))
    _emit_summary(_summary(current))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
