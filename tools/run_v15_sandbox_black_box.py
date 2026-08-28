#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

RUBRIC = (
    "temporal_ownership_pass",
    "specificity_pass",
    "calibration_narrowing_pass",
    "cutoff_contamination_pass",
    "experimental_ceiling_pass",
    "natural_language_pass",
    "algorithm_disclosure_pass",
    "strategy_forecast_separation_pass",
)


def run(distribution_dir):
    root = Path(distribution_dir)
    expected = {"metaphysics_lab.py", "metaphysics_core.md", "project_instructions.txt"}
    actual = {path.name for path in root.iterdir() if path.is_file()}
    if actual != expected:
        raise ValueError("black-box release asset set mismatch")
    core = (root / "metaphysics_core.md").read_text(encoding="utf-8")
    instructions = (root / "project_instructions.txt").read_text(encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(root / "metaphysics_lab.py"), "runtime-info"],
        text=True, capture_output=True, check=False,
    )
    runtime = json.loads(completed.stdout) if completed.returncode == 0 and completed.stdout.strip() else {}
    joined = core + "\n" + instructions
    checks = {
        "temporal_ownership_pass": all(token in joined for token in ("時間窗", "時間")),
        "specificity_pass": all(token in joined for token in ("event_family", "matched_if", "not_matched_if")),
        "calibration_narrowing_pass": "不得" in joined and "事件校準" in joined,
        "cutoff_contamination_pass": all(token in joined for token in ("known_before_lock", "clean prospective denominator")),
        "experimental_ceiling_pass": "Experimental" in joined or "experimental" in joined,
        "natural_language_pass": all(token in joined for token in ("台灣繁體中文", "白話")),
        "algorithm_disclosure_pass": "演算法權重" in joined or "權重" in joined,
        "strategy_forecast_separation_pass": "策略" in joined and "預測" in joined,
    }
    runtime_ok = bool(runtime.get("ok"))
    rows = [{"rubric": key, "status": "PASS" if value and runtime_ok else "FAIL"} for key, value in checks.items()]
    digest = hashlib.sha256((core + instructions + json.dumps(runtime, sort_keys=True)).encode("utf-8")).hexdigest()
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "rubric": rows,
        "runtime_ok": runtime_ok,
        "distribution_digest": digest,
        "note": "deterministic black-box contract harness over the three release assets; no source-module imports",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--distribution-dir", default="dist/ai")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    dist = Path(args.distribution_dir)
    if not dist.is_absolute():
        dist = root / dist
    report = run(dist)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True) if args.json else report)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
