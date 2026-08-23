"""Project-level subject identity and registry helpers.

The registry stores only display/discovery metadata. Birth data and Case facts stay
inside per-subject Case files. Subject IDs are opaque random identifiers and are
never derived from PII.
"""

from __future__ import annotations

import json
import re
import secrets
from typing import Mapping, Optional

from .errors import DistributionError


_REGISTRY_SCHEMA_VERSION = "1.0"
_SUBJECT_ID_RE = re.compile(r"^subj_([0-9a-f]{12,})$")
_SHORT_ID_RE = re.compile(r"^[0-9A-F]{6,}$")
_SUBJECTS_START = "<!-- subjects:start -->"
_SUBJECTS_END = "<!-- subjects:end -->"
_FORBIDDEN_FILENAME_CHARS_RE = re.compile(r"[/\\:*?\"<>|]+")
_WHITESPACE_RE = re.compile(r"\s+")
_HYPHEN_RE = re.compile(r"-+")


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise DistributionError("invalid_payload", "%s must be a structured mapping" % field, {"field": field})
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DistributionError("invalid_subject_display_name", "%s must be non-empty text" % field, {"field": field})
    return value.strip()


def normalize_filename_label(value: object) -> str:
    text = _text(value, "subject_display_name")
    text = _WHITESPACE_RE.sub("-", text)
    text = _FORBIDDEN_FILENAME_CHARS_RE.sub("-", text)
    text = _HYPHEN_RE.sub("-", text).strip("- .")
    if not text:
        text = "Subject"
    return text[:32]


def _subject_hex(subject_id: str) -> str:
    match = _SUBJECT_ID_RE.fullmatch(subject_id)
    if not match:
        raise DistributionError(
            "invalid_subject_id",
            "subject_id must be an opaque subj_ identifier with at least 12 hexadecimal characters",
            {"subject_id": subject_id},
        )
    return match.group(1)


def subject_short_id(subject_id: str, existing_subjects) -> str:
    body = _subject_hex(subject_id).upper()
    existing_short = {
        str(item.get("subject_short_id", "")).upper()
        for item in existing_subjects
        if isinstance(item, Mapping)
    }
    for length in range(6, len(body) + 1, 2):
        candidate = body[:length]
        if candidate not in existing_short:
            return candidate
    raise DistributionError(
        "subject_short_id_collision",
        "subject short id cannot be made unique within the current registry",
        {"subject_id": subject_id},
    )


def _validate_subject_entry(value: object) -> dict:
    raw = _mapping(value, "subject")
    subject_id = str(raw.get("subject_id", ""))
    _subject_hex(subject_id)
    short_id = str(raw.get("subject_short_id", ""))
    if not _SHORT_ID_RE.fullmatch(short_id):
        raise DistributionError("subject_registry_mismatch", "subject_short_id is malformed")
    display_name = _text(raw.get("subject_display_name"), "subject_display_name")
    filename_label = str(raw.get("filename_label", ""))
    if filename_label != normalize_filename_label(filename_label):
        raise DistributionError("subject_registry_mismatch", "filename_label is not normalized")
    status = str(raw.get("status", "active"))
    if status not in ("active", "archived"):
        raise DistributionError("subject_registry_mismatch", "subject status must be active or archived")
    if not _subject_hex(subject_id).upper().startswith(short_id):
        raise DistributionError("subject_registry_mismatch", "subject_short_id does not match subject_id")
    return {
        "subject_id": subject_id,
        "subject_short_id": short_id,
        "subject_display_name": display_name,
        "filename_label": filename_label,
        "status": status,
    }


def _empty_registry() -> dict:
    return {"registry_schema_version": _REGISTRY_SCHEMA_VERSION, "subjects": []}


def parse_subject_registry(value: Optional[object]) -> dict:
    if value in (None, ""):
        return _empty_registry()
    if not isinstance(value, str):
        raise DistributionError("subject_registry_mismatch", "registry_markdown must be Markdown text")
    lines = value.splitlines()
    if len(lines) < 4 or lines[0] != "---":
        raise DistributionError("subject_registry_mismatch", "subject registry is missing front matter")
    try:
        end_front = lines.index("---", 1)
    except ValueError as exc:
        raise DistributionError("subject_registry_mismatch", "subject registry front matter is not terminated") from exc
    metadata = {}
    for line in lines[1:end_front]:
        if ": " not in line:
            raise DistributionError("subject_registry_mismatch", "subject registry front matter is malformed")
        key, val = line.split(": ", 1)
        metadata[key] = val
    if metadata.get("registry_schema_version") != _REGISTRY_SCHEMA_VERSION:
        raise DistributionError(
            "subject_registry_mismatch",
            "unsupported subject registry schema",
            {"registry_schema_version": metadata.get("registry_schema_version")},
        )
    try:
        start = lines.index(_SUBJECTS_START)
        end = lines.index(_SUBJECTS_END)
    except ValueError as exc:
        raise DistributionError("subject_registry_mismatch", "subject registry markers are missing") from exc
    if end <= start + 2 or lines[start + 1] != "```json" or lines[end - 1] != "```":
        raise DistributionError("subject_registry_mismatch", "subject registry JSON block is malformed")
    raw_json = "\n".join(lines[start + 2:end - 1])
    try:
        parsed = json.loads(raw_json)
    except (TypeError, ValueError) as exc:
        raise DistributionError("subject_registry_mismatch", "subject registry JSON cannot be parsed") from exc
    if not isinstance(parsed, Mapping) or not isinstance(parsed.get("subjects"), list):
        raise DistributionError("subject_registry_mismatch", "subject registry must contain a subjects list")
    subjects = [_validate_subject_entry(item) for item in parsed["subjects"]]
    ids = [item["subject_id"] for item in subjects]
    shorts = [item["subject_short_id"] for item in subjects]
    if len(ids) != len(set(ids)) or len(shorts) != len(set(shorts)):
        raise DistributionError("subject_registry_mismatch", "subject registry contains duplicate subject or short ids")
    return {"registry_schema_version": _REGISTRY_SCHEMA_VERSION, "subjects": subjects}


def render_subject_registry(registry: Mapping[str, object]) -> str:
    raw = _mapping(registry, "registry")
    subjects = raw.get("subjects")
    if not isinstance(subjects, list):
        raise DistributionError("subject_registry_mismatch", "registry subjects must be a list")
    normalized = [_validate_subject_entry(item) for item in subjects]
    payload = json.dumps({"subjects": normalized}, ensure_ascii=False, sort_keys=True, indent=2)
    return (
        "---\n"
        "registry_schema_version: %s\n"
        "---\n"
        "# 命主索引\n\n"
        "%s\n"
        "```json\n%s\n```\n"
        "%s\n" % (_REGISTRY_SCHEMA_VERSION, _SUBJECTS_START, payload, _SUBJECTS_END)
    )


def validate_subject_registry(payload: Mapping[str, object]) -> dict:
    payload = _mapping(payload, "payload")
    registry = parse_subject_registry(payload.get("registry_markdown"))
    return {
        "registry_schema_version": registry["registry_schema_version"],
        "subject_count": len(registry["subjects"]),
        "subjects": list(registry["subjects"]),
    }


def _new_subject_id(existing_ids) -> str:
    for _ in range(16):
        candidate = "subj_" + secrets.token_hex(6)
        if candidate not in existing_ids:
            return candidate
    raise DistributionError("duplicate_subject_identity", "unable to create a unique subject_id")


def create_subject_identity(payload: Mapping[str, object]) -> dict:
    payload = _mapping(payload, "payload")
    display_name = _text(payload.get("subject_display_name"), "subject_display_name")
    registry = parse_subject_registry(payload.get("registry_markdown"))
    existing_ids = {item["subject_id"] for item in registry["subjects"]}
    subject_id = _new_subject_id(existing_ids)
    identity = {
        "subject_id": subject_id,
        "subject_short_id": subject_short_id(subject_id, registry["subjects"]),
        "subject_display_name": display_name,
        "filename_label": normalize_filename_label(display_name),
        "status": "active",
    }
    updated = {
        "registry_schema_version": _REGISTRY_SCHEMA_VERSION,
        "subjects": list(registry["subjects"]) + [identity],
    }
    return {"identity": identity, "registry_markdown": render_subject_registry(updated)}


def rename_subject(payload: Mapping[str, object]) -> dict:
    payload = _mapping(payload, "payload")
    subject_id = str(payload.get("subject_id", ""))
    _subject_hex(subject_id)
    new_display = _text(payload.get("new_subject_display_name"), "new_subject_display_name")
    registry = parse_subject_registry(payload.get("registry_markdown"))
    matches = [item for item in registry["subjects"] if item["subject_id"] == subject_id]
    if len(matches) != 1:
        raise DistributionError(
            "ambiguous_subject_reference",
            "subject_id must identify exactly one persisted registry subject",
            {"subject_id": subject_id, "matches": len(matches)},
        )
    updated_subjects = []
    updated_identity = None
    for item in registry["subjects"]:
        current = dict(item)
        if current["subject_id"] == subject_id:
            current["subject_display_name"] = new_display
            current["filename_label"] = normalize_filename_label(new_display)
            updated_identity = current
        updated_subjects.append(current)
    updated_registry = {
        "registry_schema_version": _REGISTRY_SCHEMA_VERSION,
        "subjects": updated_subjects,
    }
    return {
        "identity": updated_identity,
        "registry_markdown": render_subject_registry(updated_registry),
    }
