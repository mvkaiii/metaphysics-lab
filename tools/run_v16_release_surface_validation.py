#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools import run_v15_release_surface_validation

ROOT = Path(__file__).resolve().parents[1]


def run(distribution_dir: Path) -> dict:
    report = dict(run_v15_release_surface_validation.run(Path(distribution_dir)))
    report["release_version"] = "1.6.0"
    report["note"] = (
        "v1.6 deterministic release-surface validation over the three release assets; "
        "preserves the qualified v1.5 contract set while Y1 remains Experimental / Project-derived"
    )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate Metaphysics Lab v1.6 release surface")
    parser.add_argument("--distribution-dir", default="dist/ai")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    distribution = Path(args.distribution_dir)
    if not distribution.is_absolute():
        distribution = ROOT / distribution
    report = run(distribution)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True) if args.json else report)
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
