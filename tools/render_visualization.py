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


def _preflight_output(path: Path, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError("output exists; pass --overwrite to replace it: %s" % path)
    if not path.parent.exists():
        raise FileNotFoundError("output directory does not exist: %s" % path.parent)


def _output(path: Path, content: str) -> None:
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
        svg_content = render_bazi_decadal_svg(chart)
        text_content = (
            render_bazi_decadal_text(chart) if args.text_output is not None else None
        )
        targets = [args.output]
        if args.text_output is not None:
            targets.append(args.text_output)
        for target in targets:
            _preflight_output(target, args.overwrite)
        _output(args.output, svg_content)
        if args.text_output is not None and text_content is not None:
            _output(args.text_output, text_content)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("render_visualization: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
