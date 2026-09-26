"""Build a deterministic capability qualification matrix from the manifest.

The capability manifest remains the only source of implementation, maturity,
and routing truth.  This module records evidence metadata and gaps; it never
promotes a capability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Optional


INDEX_SCHEMA_VERSION = "1.0"
INDEX_CLASSIFICATION = "capability_qualification_evidence_index"
MATRIX_SCHEMA_VERSION = "1.0"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_STATUSES = frozenset(
    {
        "not_started",
        "needs_verification",
        "partial",
        "recorded",
        "blocked",
        "not_applicable_with_rationale",
    }
)
_PROMOTION_DECISIONS = frozenset(
    {"not_decided", "needs_human_decision", "blocked", "not_applicable_with_rationale"}
)
_LIST_FIELDS = frozenset(
    {
        "deterministic_contract",
        "boundary_cases",
        "fixture_refs",
        "regression_refs",
        "reference_qualification",
        "prospective_evidence",
        "failure_modes",
        "known_limitations",
        "promotion_criteria",
        "evidence_refs",
    }
)
_ENTRY_FIELDS = frozenset(
    {
        "capability_id",
        "scope",
        "profile_id",
        "rule_version",
        "evidence_status",
        "evidence_refs",
        "deterministic_contract",
        "boundary_cases",
        "fixture_refs",
        "regression_refs",
        "reference_qualification",
        "prospective_evidence",
        "failure_modes",
        "known_limitations",
        "promotion_criteria",
        "promotion_decision",
    }
)
_TOP_LEVEL_FIELDS = frozenset(
    {"schema_version", "classification", "source_commit", "entries"}
)
_EVIDENCE_REF_FIELDS = frozenset(
    {
        "path",
        "sha256",
        "kind",
        "status",
        "source_commit",
        "scope",
        "profile_id",
        "rule_version",
    }
)


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _nonblank(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _safe_relative_path(value: object) -> Optional[Path]:
    if not isinstance(value, str) or not value or "\x00" in value:
        return None
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    return candidate


def _canonical_file_bytes(repo_root: Path, relative: Path, source_commit: str) -> Optional[bytes]:
    """Read bytes from the requested Git commit, never from the worktree."""
    spec = "%s:%s" % (source_commit, relative.as_posix())
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "show", spec],
            check=False,
            capture_output=True,
        )
    except OSError:
        completed = None
    if completed is not None and completed.returncode == 0:
        return completed.stdout
    return None


def _commit_exists(repo_root: Path, source_commit: str) -> bool:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "cat-file", "-e", "%s^{commit}" % source_commit],
            check=False,
            capture_output=True,
        )
    except OSError:
        return False
    return completed.returncode == 0


def _supported_scopes(capability: Mapping[str, object]) -> set[str]:
    values = capability.get("supported_scopes")
    if isinstance(values, list) and values:
        return {value for value in values if _nonblank(value)}
    return {"default"}


def _profile_rule_versions(capability: Mapping[str, object]) -> dict[str, str]:
    profiles = capability.get("supported_profiles")
    if isinstance(profiles, list) and profiles:
        result = {}
        for profile in profiles:
            if isinstance(profile, Mapping):
                profile_id = profile.get("profile_id")
                rule_version = profile.get("rule_version") or capability.get("rule_version")
            else:
                profile_id = profile
                rule_version = capability.get("rule_version")
            if _nonblank(profile_id) and _nonblank(rule_version):
                result[str(profile_id)] = str(rule_version)
        if result:
            return result
    profile_id = capability.get("profile_id") or "default"
    return {str(profile_id): str(capability.get("rule_version"))}


def _manifest_errors(manifest: object) -> list[str]:
    if not isinstance(manifest, Mapping):
        return ["manifest must be an object"]
    if not _nonblank(manifest.get("manifest_version")):
        return ["manifest_version must be non-blank text"]
    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, Mapping):
        return ["manifest capabilities must be an object"]
    errors = []
    for capability_id, capability in capabilities.items():
        if not isinstance(capability_id, str) or not isinstance(capability, Mapping):
            errors.append("manifest capability entries must be string/object pairs")
            continue
        if capability.get("id") != capability_id:
            errors.append("manifest capability id mismatch: %s" % capability_id)
        for field in ("implementation", "maturity", "routing", "rule_version"):
            if not _nonblank(capability.get(field)):
                errors.append("manifest capability %s missing %s" % (capability_id, field))
        scopes = capability.get("supported_scopes")
        if scopes is not None and (
            not isinstance(scopes, list)
            or not scopes
            or any(not _nonblank(scope) for scope in scopes)
            or len(set(scopes)) != len(scopes)
        ):
            errors.append("manifest capability %s has invalid supported_scopes" % capability_id)
        profiles = capability.get("supported_profiles")
        if profiles is not None:
            if not isinstance(profiles, list) or not profiles:
                errors.append("manifest capability %s has invalid supported_profiles" % capability_id)
            else:
                profile_ids = []
                for profile in profiles:
                    if isinstance(profile, Mapping):
                        profile_id = profile.get("profile_id")
                        profile_rule = profile.get("rule_version") or capability.get("rule_version")
                    else:
                        profile_id = profile
                        profile_rule = capability.get("rule_version")
                    if not _nonblank(profile_id) or not _nonblank(profile_rule):
                        errors.append(
                            "manifest capability %s has invalid supported_profiles entry"
                            % capability_id
                        )
                    profile_ids.append(profile_id)
                valid_profile_ids = [
                    profile_id for profile_id in profile_ids if isinstance(profile_id, str)
                ]
                if len(valid_profile_ids) != len(set(valid_profile_ids)):
                    errors.append(
                        "manifest capability %s has duplicate supported_profiles"
                        % capability_id
                    )
    return errors


def _validate_evidence_ref(
    entry_key: str,
    ref: object,
    repo_root: Path,
    source_commit: str,
    scope: object,
    profile_id: object,
    rule_version: object,
) -> list[str]:
    if not isinstance(ref, Mapping):
        return ["%s evidence_refs entries must be objects" % entry_key]
    errors = []
    unknown = sorted(set(ref) - _EVIDENCE_REF_FIELDS)
    if unknown:
        errors.append("%s evidence ref unknown fields: %s" % (entry_key, ", ".join(unknown)))
    for field in sorted(_EVIDENCE_REF_FIELDS - set(ref)):
        errors.append("%s evidence ref missing field: %s" % (entry_key, field))
    relative = _safe_relative_path(ref.get("path"))
    if relative is None:
        errors.append("%s evidence ref path must be a safe relative path" % entry_key)
    digest = ref.get("sha256")
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        errors.append("%s evidence ref sha256 must be lowercase hex" % entry_key)
    if not _nonblank(ref.get("status")):
        errors.append("%s evidence ref status must be non-blank text" % entry_key)
    if not _nonblank(ref.get("kind")):
        errors.append("%s evidence ref kind must be non-blank text" % entry_key)
    if ref.get("source_commit") != source_commit:
        errors.append("%s evidence ref source_commit does not match index" % entry_key)
    if ref.get("scope") != scope:
        errors.append("%s evidence ref scope does not match entry" % entry_key)
    if ref.get("profile_id") != profile_id:
        errors.append("%s evidence ref profile_id does not match entry" % entry_key)
    if ref.get("rule_version") != rule_version:
        errors.append("%s evidence ref rule_version does not match entry" % entry_key)
    if relative is not None and isinstance(digest, str) and _SHA256_RE.fullmatch(digest):
        payload = _canonical_file_bytes(repo_root, relative, source_commit)
        if payload is None:
            errors.append("%s evidence ref path is unavailable: %s" % (entry_key, relative))
        elif hashlib.sha256(payload).hexdigest() != digest:
            errors.append("%s evidence ref sha256 mismatch: %s" % (entry_key, relative))
    return errors


def validate_evidence_index(
    manifest: Mapping[str, object],
    evidence_index: Mapping[str, object],
    repo_root: Path,
) -> list[str]:
    """Return deterministic validation errors without changing either input."""
    errors = _manifest_errors(manifest)
    if not isinstance(evidence_index, Mapping):
        return sorted(errors + ["evidence index must be an object"])

    unknown_top_level = sorted(set(evidence_index) - _TOP_LEVEL_FIELDS)
    errors.extend("evidence index unknown field: %s" % field for field in unknown_top_level)
    if evidence_index.get("schema_version") != INDEX_SCHEMA_VERSION:
        errors.append("unsupported evidence index schema_version")
    if evidence_index.get("classification") != INDEX_CLASSIFICATION:
        errors.append("unsupported evidence index classification")
    source_commit = evidence_index.get("source_commit")
    if not isinstance(source_commit, str) or not _COMMIT_RE.fullmatch(source_commit):
        errors.append("source_commit must be a 40-character lowercase commit SHA")
        source_commit = "0" * 40
    elif not _commit_exists(Path(repo_root), source_commit):
        errors.append("source_commit is not available as a commit in the repository")

    manifest_version = manifest.get("manifest_version") if isinstance(manifest, Mapping) else None
    entries = evidence_index.get("entries")
    if not isinstance(entries, list):
        return sorted(errors + ["evidence index entries must be a list"])
    capabilities = manifest.get("capabilities", {}) if isinstance(manifest, Mapping) else {}
    seen = set()
    for position, entry in enumerate(entries):
        prefix = "entry[%d]" % position
        if not isinstance(entry, Mapping):
            errors.append("%s must be an object" % prefix)
            continue
        unknown = sorted(set(entry) - _ENTRY_FIELDS)
        errors.extend("%s unknown field: %s" % (prefix, field) for field in unknown)
        required = _ENTRY_FIELDS - {"evidence_refs"}
        missing = sorted(field for field in required if field not in entry)
        errors.extend("%s missing field: %s" % (prefix, field) for field in missing)

        capability_id = entry.get("capability_id")
        scope = entry.get("scope")
        profile_id = entry.get("profile_id")
        key = (capability_id, scope, profile_id)
        entry_key = "%s:%s:%s" % (capability_id, scope, profile_id)
        if key in seen:
            errors.append("duplicate evidence entry: %s" % entry_key)
        seen.add(key)
        if capability_id not in capabilities:
            errors.append("unknown capability: %s" % capability_id)
            capability = None
        else:
            capability = capabilities[capability_id]
        for name, value in (("scope", scope), ("profile_id", profile_id)):
            if not _nonblank(value):
                errors.append("%s %s must be non-blank text" % (prefix, name))
        expected_rule_version = None
        if capability is not None:
            supported_scopes = _supported_scopes(capability)
            profile_rule_versions = _profile_rule_versions(capability)
            if _nonblank(scope) and scope not in supported_scopes:
                errors.append("%s scope is not supported by manifest" % entry_key)
            if _nonblank(profile_id) and profile_id not in profile_rule_versions:
                errors.append("%s profile_id is not supported by manifest" % entry_key)
            expected_rule_version = profile_rule_versions.get(profile_id)
            if expected_rule_version is not None and entry.get("rule_version") != expected_rule_version:
                errors.append("%s profile rule_version does not match manifest" % entry_key)
        if entry.get("evidence_status") not in _STATUSES:
            errors.append("%s evidence_status is unsupported" % entry_key)
        if entry.get("promotion_decision") not in _PROMOTION_DECISIONS:
            errors.append("%s promotion_decision is not fail-closed" % entry_key)
        for field in _LIST_FIELDS:
            if field in entry and not isinstance(entry[field], list):
                errors.append("%s %s must be a list" % (entry_key, field))
        refs = entry.get("evidence_refs", [])
        if isinstance(refs, list):
            for ref in refs:
                errors.extend(
                    _validate_evidence_ref(
                        entry_key,
                        ref,
                        Path(repo_root),
                        source_commit,
                        scope,
                        profile_id,
                        expected_rule_version or entry.get("rule_version"),
                    )
                )

    if manifest_version is not None and evidence_index.get("schema_version") == INDEX_SCHEMA_VERSION:
        # The matrix is currently coupled to the manifest contract, not to a
        # mutable copy of its maturity or routing fields.
        if not _nonblank(manifest_version):
            errors.append("manifest_version cannot be blank")
    return sorted(set(errors))


def build_matrix(
    manifest: Mapping[str, object],
    evidence_index: Mapping[str, object],
    repo_root: Path,
) -> dict:
    """Build a sorted matrix while taking capability truth only from manifest."""
    errors = validate_evidence_index(manifest, evidence_index, repo_root)
    if errors:
        raise ValueError("invalid capability evidence index:\n- " + "\n- ".join(errors))

    capabilities = manifest["capabilities"]
    rows = []
    for entry in evidence_index["entries"]:
        capability = capabilities[entry["capability_id"]]
        rule_version = _profile_rule_versions(capability)[entry["profile_id"]]
        row = {
            "capability_id": entry["capability_id"],
            "scope": entry["scope"],
            "profile_id": entry["profile_id"],
            "implementation": capability["implementation"],
            "maturity": capability["maturity"],
            "routing": capability["routing"],
            "rule_version": rule_version,
            "module": capability.get("module"),
            "dependencies": capability.get("dependencies", []),
            "evidence_status": entry["evidence_status"],
            "evidence_refs": entry.get("evidence_refs", []),
            "deterministic_contract": entry["deterministic_contract"],
            "boundary_cases": entry["boundary_cases"],
            "fixture_refs": entry["fixture_refs"],
            "regression_refs": entry["regression_refs"],
            "reference_qualification": entry["reference_qualification"],
            "prospective_evidence": entry["prospective_evidence"],
            "failure_modes": entry["failure_modes"],
            "known_limitations": entry["known_limitations"],
            "promotion_criteria": entry["promotion_criteria"],
            "promotion_decision": entry["promotion_decision"],
        }
        rows.append(row)
    rows.sort(key=lambda row: (row["capability_id"], row["scope"], row["profile_id"]))
    return {
        "matrix_schema_version": MATRIX_SCHEMA_VERSION,
        "manifest_version": manifest["manifest_version"],
        "source_commit": evidence_index["source_commit"],
        "entries": rows,
    }


def initialize_evidence_index(manifest: Mapping[str, object], source_commit: str) -> dict:
    """Create a gap-visible, non-promoting index skeleton from one manifest."""
    if not isinstance(source_commit, str) or not _COMMIT_RE.fullmatch(source_commit):
        raise ValueError("source_commit must be a 40-character lowercase commit SHA")
    entries = []
    for capability_id in sorted(manifest["capabilities"]):
        capability = manifest["capabilities"][capability_id]
        for scope in sorted(_supported_scopes(capability)):
            for profile_id, rule_version in sorted(_profile_rule_versions(capability).items()):
                entries.append(
                    {
                        "capability_id": capability_id,
                        "scope": scope,
                        "profile_id": profile_id,
                        "rule_version": rule_version,
                        "evidence_status": "needs_verification",
                        "evidence_refs": [],
                        "deterministic_contract": [],
                        "boundary_cases": [],
                        "fixture_refs": [],
                        "regression_refs": [],
                        "reference_qualification": [],
                        "prospective_evidence": [],
                        "failure_modes": [],
                        "known_limitations": [],
                        "promotion_criteria": [],
                        "promotion_decision": "not_decided",
                    }
                )
    return {
        "schema_version": INDEX_SCHEMA_VERSION,
        "classification": INDEX_CLASSIFICATION,
        "source_commit": source_commit,
        "entries": entries,
    }


def render_matrix_markdown(matrix: Mapping[str, object]) -> str:
    rows = matrix["entries"]
    lines = [
        "# Capability Qualification Matrix",
        "",
        "> Generated from the canonical capability manifest. This document records evidence and gaps; it does not promote capabilities.",
        "",
        "- Matrix schema: `%s`" % matrix["matrix_schema_version"],
        "- Manifest version: `%s`" % matrix["manifest_version"],
        "- Source commit: `%s`" % matrix["source_commit"],
        "",
        "| Capability | Scope | Profile | Implementation | Maturity | Routing | Rule | Evidence | Promotion |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| `{capability_id}` | `{scope}` | `{profile_id}` | `{implementation}` | `{maturity}` | `{routing}` | `{rule_version}` | `{evidence_status}` | `{promotion_decision}` |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "Evidence references and known limitations remain in `qualification/capabilities/evidence-index.v1.json`. A `recorded` or `PASS` source result is not a Stable promotion decision.",
            "",
        ]
    )
    return "\n".join(lines)


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object: %s" % path)
    return value


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_json(value) + b"\n")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--index", type=Path, default=None)
    parser.add_argument("--init-index", type=Path, default=None)
    parser.add_argument("--source-commit", default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from engine.distribution.manifest import load_capability_manifest

    manifest = load_capability_manifest(repo_root / "engine")
    if args.init_index is not None:
        if not args.source_commit:
            parser.error("--init-index requires --source-commit")
        _write_json(args.init_index, initialize_evidence_index(manifest, args.source_commit))
        print("wrote evidence index: %s" % args.init_index)
        return 0

    index_path = args.index or repo_root / "qualification" / "capabilities" / "evidence-index.v1.json"
    matrix = build_matrix(manifest, _read_json(index_path), repo_root)
    rendered = render_matrix_markdown(matrix)
    output = args.output or repo_root / "docs" / "qualification" / "capability-matrix.md"
    if args.check:
        try:
            current = output.read_text(encoding="utf-8")
        except OSError as exc:
            print("matrix output unavailable: %s" % exc)
            return 1
        if current != rendered:
            print("capability matrix is out of date")
            return 1
        print("capability matrix is up to date")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8", newline="\n")
    print("wrote capability matrix: %s" % output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
