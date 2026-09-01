#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.distribution.bakeoff import evaluate_bakeoff, validate_bakeoff_fixture


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def build_report(payload: object) -> dict:
    fixture = validate_bakeoff_fixture(payload)
    report = evaluate_bakeoff(fixture)
    report["fixture_sha256"] = _sha256(fixture)
    report["report_sha256"] = _sha256(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate deterministic v1.6 interpretation bake-off fixture")
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    report = build_report(payload)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
