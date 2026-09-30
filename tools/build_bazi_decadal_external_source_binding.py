"""Build an exact raw-byte source binding for Bazi decadal qualification.

This tool performs no network access and no metaphysics calculation. It hashes
an already acquired source file byte-for-byte and emits the source-binding
object accepted by the pre-oracle sealer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Optional, Sequence


def sha256_file(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"source file does not exist: {path}")
    if path.stat().st_size <= 0:
        raise ValueError("source file must not be empty")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_external_source_binding(
    path: Path,
    *,
    provider: str,
    source_url: str,
    timezone: str,
    published_precision_seconds: int,
    source_file_label: Optional[str] = None,
) -> dict:
    if not isinstance(provider, str) or not provider:
        raise ValueError("provider must be non-empty")
    if not isinstance(source_url, str) or not source_url.startswith("https://"):
        raise ValueError("source_url must be an https URL")
    if not isinstance(timezone, str) or not timezone:
        raise ValueError("timezone must be non-empty")
    if (
        isinstance(published_precision_seconds, bool)
        or not isinstance(published_precision_seconds, int)
        or published_precision_seconds <= 0
    ):
        raise ValueError("published_precision_seconds must be a positive integer")
    label = source_file_label or path.name
    if not isinstance(label, str) or not label:
        raise ValueError("source_file_label must be non-empty")
    return {
        "provider": provider,
        "role": "astronomical_input",
        "source_url": source_url,
        "source_file_label": label,
        "source_sha256": sha256_file(path),
        "timezone": timezone,
        "published_precision_seconds": published_precision_seconds,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--timezone", required=True)
    parser.add_argument("--published-precision-seconds", required=True, type=int)
    parser.add_argument("--source-file-label")
    args = parser.parse_args(argv)
    try:
        payload = build_external_source_binding(
            args.file,
            provider=args.provider,
            source_url=args.source_url,
            timezone=args.timezone,
            published_precision_seconds=args.published_precision_seconds,
            source_file_label=args.source_file_label,
        )
    except (OSError, ValueError) as exc:
        print(f"build_bazi_decadal_external_source_binding: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
