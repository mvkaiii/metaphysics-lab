"""Render a validated visualization chart to deterministic SVG or text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from renderers.svg.bazi_decadal import render_bazi_decadal_svg, render_bazi_decadal_text


def _output(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError("output exists; pass --overwrite to replace it: %s" % path)
    if not path.parent.exists():
        raise FileNotFoundError("output directory does not exist: %s" % path.parent)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--text-output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        chart = json.loads(args.input.read_text(encoding="utf-8"))
        _output(args.output, render_bazi_decadal_svg(chart), args.overwrite)
        if args.text_output is not None:
            _output(args.text_output, render_bazi_decadal_text(chart), args.overwrite)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("render_visualization: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
