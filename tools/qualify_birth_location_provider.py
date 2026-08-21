#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.birth.errors import BirthFoundationError
from engine.birth.location import NominatimLocationProvider, resolve_birth_place
from engine.birth.models import BirthPlaceInput


PUBLIC_CASES = (
    "台北市, 台灣",
    "高雄市, 台灣",
    "Tokyo, Japan",
    "New York, NY, USA",
    "London, UK",
)


def _rounded(value: object) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), 4)


def build_summary(
    records: Iterable[Mapping[str, object]],
    *,
    provider_name: str,
    provider_version: str,
    generated_at: str,
) -> dict:
    results = []
    for record in records:
        results.append(
            {
                "query": str(record["query"]),
                "status": str(record["status"]),
                "latitude": _rounded(record.get("latitude")),
                "longitude": _rounded(record.get("longitude")),
                "timezone": record.get("timezone"),
                "error_code": record.get("error_code"),
            }
        )
    pass_count = sum(item["status"] == "PASS" for item in results)
    fail_count = len(results) - pass_count
    return {
        "schema_version": "1.0",
        "classification": "public_location_qualification",
        "provider_name": provider_name,
        "provider_version": provider_version,
        "generated_at": generated_at,
        "queries": [item["query"] for item in results],
        "results": results,
        "pass_count": pass_count,
        "fail_count": fail_count,
    }


def qualify(provider: NominatimLocationProvider) -> tuple[dict, bool, bool]:
    records = []
    infrastructure_failure = False
    for query in PUBLIC_CASES:
        try:
            resolved = resolve_birth_place(BirthPlaceInput(query), provider)
            records.append(
                {
                    "query": query,
                    "status": "PASS",
                    "latitude": resolved.latitude,
                    "longitude": resolved.longitude,
                    "timezone": resolved.timezone,
                    "error_code": None,
                }
            )
        except BirthFoundationError as exc:
            if exc.code == "location_provider_unavailable":
                infrastructure_failure = True
            records.append(
                {
                    "query": query,
                    "status": "FAIL",
                    "latitude": None,
                    "longitude": None,
                    "timezone": None,
                    "error_code": exc.code,
                }
            )
            if infrastructure_failure:
                break
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    summary = build_summary(
        records,
        provider_name=provider.name,
        provider_version=provider.version,
        generated_at=now,
    )
    complete_pass = len(records) == len(PUBLIC_CASES) and summary["fail_count"] == 0
    return summary, complete_pass, infrastructure_failure


def main() -> int:
    parser = argparse.ArgumentParser(description="Qualify the public birth-place resolver provider")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--user-agent", default="metaphysics-lab-public-qualification/1.0")
    args = parser.parse_args()

    provider = NominatimLocationProvider(args.user_agent)
    summary, complete_pass, infrastructure_failure = qualify(provider)
    text = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)

    if infrastructure_failure:
        print("LOCATION_PROVIDER_INFRA_FAIL", file=sys.stderr)
        return 2
    if not complete_pass:
        print(
            "LOCATION_PROVIDER_QUALIFICATION_FAIL %d/%d"
            % (summary["pass_count"], len(PUBLIC_CASES)),
            file=sys.stderr,
        )
        return 1
    print("LOCATION_PROVIDER_QUALIFICATION_PASS 5/5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
