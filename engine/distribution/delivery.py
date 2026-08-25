"""Verified flat ZIP delivery bundles for portable Case Markdown.

Markdown remains the canonical Project data. ZIP is only a transport envelope
for hosts where individual Markdown attachments are inconvenient or unreliable.
"""

from __future__ import annotations

import base64
import hashlib
import io
import zipfile
from typing import Any, Mapping

from .errors import DistributionError


_FORMAT_PROFILE = "zip-deflate-flat-markdown-v1"
_DEFAULT_FILENAME = "metaphysics_lab_case.zip"
_FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
_WINDOWS_FORBIDDEN = frozenset('<>:"|?*')
_WINDOWS_RESERVED = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + ["COM%d" % index for index in range(1, 10)]
    + ["LPT%d" % index for index in range(1, 10)]
)


def _payload_mapping(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DistributionError(
            "invalid_delivery_bundle_payload",
            "delivery bundle payload must be a structured mapping",
        )
    return value


def _member_name(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DistributionError(
            "invalid_delivery_bundle_member",
            "delivery bundle member names must be non-empty canonical text",
        )
    if "/" in value or "\\" in value or value in (".", ".."):
        raise DistributionError(
            "invalid_delivery_bundle_member",
            "delivery bundle members must be flat files",
            {"filename": value},
        )
    if not value.lower().endswith(".md"):
        raise DistributionError(
            "invalid_delivery_bundle_member",
            "delivery bundle accepts Markdown files only",
            {"filename": value},
        )
    if value.endswith((".", " ")) or any(ord(char) < 32 for char in value):
        raise DistributionError(
            "invalid_delivery_bundle_member",
            "delivery bundle member name is not cross-platform safe",
            {"filename": value},
        )
    if any(char in _WINDOWS_FORBIDDEN for char in value):
        raise DistributionError(
            "invalid_delivery_bundle_member",
            "delivery bundle member name is not Windows-safe",
            {"filename": value},
        )
    stem = value[:-3].rstrip(". ").upper()
    if stem in _WINDOWS_RESERVED:
        raise DistributionError(
            "invalid_delivery_bundle_member",
            "delivery bundle member name is reserved on Windows",
            {"filename": value},
        )
    return value


def _normalized_files(value: object) -> dict:
    if not isinstance(value, Mapping) or not value:
        raise DistributionError(
            "invalid_delivery_bundle_payload",
            "delivery bundle requires at least one Markdown file",
        )
    normalized = {}
    folded = set()
    for raw_name, raw_content in value.items():
        name = _member_name(raw_name)
        if not isinstance(raw_content, str):
            raise DistributionError(
                "invalid_delivery_bundle_payload",
                "delivery bundle Markdown content must be text",
                {"filename": name},
            )
        key = name.casefold()
        if key in folded:
            raise DistributionError(
                "invalid_delivery_bundle_member",
                "delivery bundle contains a case-insensitive filename collision",
                {"filename": name},
            )
        folded.add(key)
        normalized[name] = raw_content.encode("utf-8")
    return normalized


def _zip_bytes(files: Mapping[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    try:
        with zipfile.ZipFile(
            buffer,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
            allowZip64=False,
        ) as archive:
            for filename in sorted(files):
                info = zipfile.ZipInfo(filename=filename, date_time=_FIXED_ZIP_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 0
                info.external_attr = 0
                archive.writestr(info, files[filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    except (OSError, RuntimeError, ValueError, zipfile.LargeZipFile) as exc:
        raise DistributionError(
            "delivery_bundle_generation_failed",
            "verified delivery ZIP could not be generated",
        ) from exc
    return buffer.getvalue()


def _verify_zip(raw: bytes, files: Mapping[str, bytes]) -> None:
    expected = sorted(files)
    try:
        with zipfile.ZipFile(io.BytesIO(raw), mode="r") as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP CRC verification failed")
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if names != expected:
                raise ValueError("ZIP member list does not match expected files")
            for info in infos:
                if info.is_dir() or info.compress_type != zipfile.ZIP_DEFLATED:
                    raise ValueError("ZIP member profile is invalid")
                if archive.read(info.filename) != files[info.filename]:
                    raise ValueError("ZIP member bytes do not match source Markdown")
    except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        raise DistributionError(
            "delivery_bundle_integrity_failed",
            "generated delivery ZIP failed integrity verification",
        ) from exc


def build_delivery_bundle(payload: Mapping[str, object]) -> dict:
    """Build and re-open a deterministic, cross-platform-oriented Markdown ZIP."""
    request = _payload_mapping(payload)
    files = _normalized_files(request.get("files"))
    raw = _zip_bytes(files)
    _verify_zip(raw, files)
    return {
        "filename": _DEFAULT_FILENAME,
        "media_type": "application/zip",
        "encoding": "base64",
        "format_profile": _FORMAT_PROFILE,
        "content_base64": base64.b64encode(raw).decode("ascii"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
        "members": sorted(files),
        "status": {
            "generated": True,
            "integrity_verified": True,
            "delivered": "unknown",
        },
    }
