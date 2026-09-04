#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

RELEASE_VERSION = "1.6.0"
USER_PACKAGE_NAME = "Metaphysics-Lab-v1.6.0-User-Package.zip"
USER_ASSETS = (
    "metaphysics_core.md",
    "metaphysics_lab.py",
    "project_instructions.txt",
)
_FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def _validated_assets(distribution_dir: Path):
    root = Path(distribution_dir)
    if not root.is_dir():
        raise ValueError("distribution directory is missing")
    entries = [path for path in root.iterdir()]
    if any(path.is_symlink() or not path.is_file() for path in entries):
        raise ValueError("distribution directory must contain regular files only")
    names = {path.name for path in entries}
    expected = set(USER_ASSETS)
    if names != expected:
        raise ValueError("distribution asset set mismatch: expected=%s actual=%s" % (sorted(expected), sorted(names)))
    result = []
    for name in USER_ASSETS:
        raw = (root / name).read_bytes()
        if not raw:
            raise ValueError("distribution asset is empty: %s" % name)
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("distribution asset is not UTF-8: %s" % name) from exc
        result.append((name, raw))
    return result


def render_user_package(distribution_dir: Path) -> bytes:
    assets = _validated_assets(Path(distribution_dir))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in assets:
            info = zipfile.ZipInfo(name, date_time=_FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return buffer.getvalue()


def verify_user_package(package_bytes: bytes, distribution_dir: Path) -> dict:
    expected_assets = dict(_validated_assets(Path(distribution_dir)))
    with zipfile.ZipFile(io.BytesIO(package_bytes), "r") as archive:
        members = archive.namelist()
        if sorted(members) != sorted(USER_ASSETS):
            raise ValueError("user package member set mismatch")
        if any("/" in name or "\\" in name for name in members):
            raise ValueError("user package must be flat")
        for name in USER_ASSETS:
            if archive.read(name) != expected_assets[name]:
                raise ValueError("user package member differs from distribution asset: %s" % name)
    return {
        "integrity_verified": True,
        "release_version": RELEASE_VERSION,
        "members": list(USER_ASSETS),
        "sha256": hashlib.sha256(package_bytes).hexdigest(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build deterministic Metaphysics Lab user package")
    parser.add_argument("--distribution-dir", default="dist/ai")
    parser.add_argument("--output", default=USER_PACKAGE_NAME)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    distribution = Path(args.distribution_dir)
    if not distribution.is_absolute():
        distribution = root / distribution
    package = render_user_package(distribution)
    report = verify_user_package(package, distribution)
    if not args.verify:
        output = Path(args.output)
        if not output.is_absolute():
            output = root / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(package)
        report["output"] = str(output)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
