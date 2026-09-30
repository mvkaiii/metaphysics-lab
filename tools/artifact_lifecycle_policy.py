"""Fail-closed classification and approval checks for Actions artifacts.

The policy returns a candidate selection only. It has no network or deletion
operation; callers must separately review and approve every inventory snapshot.
Retention values are selection-policy guidance only. ``None`` excludes a class
from cleanup selection; it does not promise indefinite GitHub retention.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Mapping, Sequence


_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
_NAME_SHA = re.compile(r"(?<![0-9a-f])([0-9a-f]{40})(?![0-9a-f])")
_WORKFLOW_PATH = re.compile(r"^\.github/workflows/[^/]+\.ya?ml(?:@[^\r\n]+)?$")
_PROTECTION_FIELDS = (
    "repository",
    "current_candidate_shas",
    "frozen_release_shas",
    "protected_artifact_ids",
    "protected_release_asset_names",
    "protected_evidence_names",
    "protected_evidence_markers",
    "protected_evidence_sha256",
)
_RETENTION_DAYS = {
    "intermediate": 1,
    "failure_log": 3,
    "superseded_validation": 7,
    "current_candidate": None,
    "release_evidence": None,
    "frozen_release": None,
    "unknown": None,
}


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _as_values(value: Any, field: str, errors: List[str]) -> List[Any]:
    if not isinstance(value, (list, tuple, set, frozenset)):
        errors.append("protection.%s must be a collection" % field)
        return []
    return list(value)


def _protection_values(protection: Any) -> tuple:
    errors: List[str] = []
    if not isinstance(protection, Mapping):
        return None, ["protection config is not an object"]
    missing = [field for field in _PROTECTION_FIELDS if field not in protection]
    if missing:
        errors.append("protection config missing fields: %s" % ", ".join(missing))
    repository = protection.get("repository")
    if not isinstance(repository, str) or repository.count("/") != 1 or not all(repository.split("/")):
        errors.append("protection.repository must be owner/repository")

    collections: Dict[str, List[Any]] = {}
    for field in _PROTECTION_FIELDS[1:]:
        collections[field] = _as_values(protection.get(field), field, errors)

    for field in ("current_candidate_shas", "frozen_release_shas"):
        for value in collections[field]:
            if not isinstance(value, str) or not _SHA40.fullmatch(value):
                errors.append("protection.%s contains an invalid SHA" % field)
                break
    for value in collections["protected_artifact_ids"]:
        if not _is_positive_int(value):
            errors.append("protection.protected_artifact_ids contains an invalid id")
            break
    for field in (
        "protected_release_asset_names",
        "protected_evidence_names",
        "protected_evidence_markers",
    ):
        if any(not isinstance(value, str) or not value for value in collections[field]):
            errors.append("protection.%s contains an invalid name" % field)
    for value in collections["protected_evidence_sha256"]:
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            errors.append("protection.protected_evidence_sha256 contains an invalid digest")
            break

    values = dict(collections)
    values["repository"] = repository
    return values, errors


def retention_days_for(classification: str) -> Any:
    """Return suggested retention days; ``None`` excludes a class from selection.

    This helper does not configure GitHub retention or guarantee persistence.
    """

    if classification not in _RETENTION_DAYS:
        raise ValueError("unknown artifact classification: %s" % classification)
    return _RETENTION_DAYS[classification]


def _unknown(reasons: List[str]) -> Dict[str, Any]:
    return {"classification": "unknown_provenance", "protected": True, "reasons": reasons}


def _artifact_errors(artifact: Mapping[str, Any], values: Mapping[str, Any]) -> List[str]:
    errors: List[str] = []
    if not _is_positive_int(artifact.get("id")):
        errors.append("invalid artifact id")
    if not isinstance(artifact.get("name"), str) or not artifact.get("name"):
        errors.append("missing artifact name")
    if not _is_nonnegative_int(artifact.get("size_in_bytes")):
        errors.append("invalid artifact size")
    if not isinstance(artifact.get("expired"), bool):
        errors.append("missing artifact expiration status")
    digest = artifact.get("digest")
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        errors.append("missing or invalid artifact digest")

    provenance = artifact.get("provenance")
    if not isinstance(provenance, Mapping):
        return errors + ["missing provenance"]
    if provenance.get("repository") != values["repository"]:
        errors.append("repository provenance mismatch")
    if not _is_positive_int(provenance.get("workflow_id")):
        errors.append("missing workflow_id provenance")
    path = provenance.get("workflow_path")
    if not isinstance(path, str) or not _WORKFLOW_PATH.fullmatch(path):
        errors.append("missing workflow_path provenance")
    if not _is_positive_int(provenance.get("run_id")):
        errors.append("missing run_id provenance")
    if not _is_positive_int(provenance.get("run_attempt")):
        errors.append("missing run_attempt provenance")
    head_sha = provenance.get("head_sha")
    if not isinstance(head_sha, str) or not _SHA40.fullmatch(head_sha):
        errors.append("missing head_sha provenance")
    if not isinstance(provenance.get("head_branch"), str) or not provenance.get("head_branch"):
        errors.append("missing head_branch provenance")
    top_level_sha = artifact.get("head_sha")
    if top_level_sha is not None and top_level_sha != head_sha:
        errors.append("top-level head_sha conflicts with provenance")

    artifact_name = artifact.get("name")
    if isinstance(artifact_name, str) and isinstance(head_sha, str):
        named_shas = _NAME_SHA.findall(artifact_name.lower())
        if any(named_sha != head_sha for named_sha in named_shas):
            errors.append("artifact filename SHA conflicts with run head_sha")
    return errors


def classify_artifact(artifact: Any, protection: Any) -> Dict[str, Any]:
    """Classify an artifact; invalid config or provenance is always protected."""

    values, config_errors = _protection_values(protection)
    if config_errors:
        return _unknown(config_errors)
    if not isinstance(artifact, Mapping):
        return _unknown(["artifact record is not an object"])

    artifact_id = artifact.get("id")
    name = artifact.get("name")
    digest = artifact.get("digest")
    if artifact_id in values["protected_artifact_ids"]:
        return {"classification": "protected_evidence", "protected": True, "reasons": ["explicit protected artifact id"]}
    if name in values["protected_release_asset_names"]:
        return {"classification": "protected_release_asset", "protected": True, "reasons": ["protected release asset name"]}
    if name in values["protected_evidence_names"]:
        return {"classification": "protected_evidence", "protected": True, "reasons": ["protected evidence name"]}
    if digest in values["protected_evidence_sha256"]:
        return {"classification": "protected_evidence", "protected": True, "reasons": ["protected evidence digest"]}
    if isinstance(name, str):
        markers = sorted(
            marker for marker in values["protected_evidence_markers"] if marker.lower() in name.lower()
        )
        if markers:
            return {
                "classification": "protected_evidence",
                "protected": True,
                "reasons": ["protected evidence marker: %s" % ", ".join(markers)],
            }

    errors = _artifact_errors(artifact, values)
    if errors:
        return _unknown(errors)
    head_sha = artifact["provenance"]["head_sha"]
    if head_sha in values["frozen_release_shas"]:
        return {"classification": "frozen_release", "protected": True, "reasons": ["frozen release provenance"]}
    if head_sha in values["current_candidate_shas"]:
        return {"classification": "current_candidate", "protected": True, "reasons": ["current semantic candidate provenance"]}
    if artifact["expired"] is not True:
        return {"classification": "active", "protected": True, "reasons": ["artifact is not expired"]}
    return {"classification": "eligible", "protected": False, "reasons": ["expired artifact with complete provenance"]}


def _canonical_artifact(artifact: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(artifact, Mapping):
        raise ValueError("inventory contains a non-object artifact")
    provenance = artifact.get("provenance")
    if not isinstance(provenance, Mapping):
        provenance = {}
    return {
        "id": artifact.get("id"),
        "name": artifact.get("name"),
        "size_in_bytes": artifact.get("size_in_bytes"),
        "expired": artifact.get("expired"),
        "digest": artifact.get("digest"),
        "provenance": dict(provenance),
    }


def compute_inventory_digest(repository: str, artifacts: Sequence[Mapping[str, Any]]) -> str:
    """Hash a canonical, order-independent inventory snapshot."""

    canonical_artifacts = [_canonical_artifact(artifact) for artifact in artifacts]
    canonical_artifacts.sort(key=lambda row: (str(row["id"]), str(row["name"] or "")))
    payload = {"repository": repository, "artifacts": canonical_artifacts}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _append_reason(reasons: List[str], reason: str) -> None:
    if reason not in reasons:
        reasons.append(reason)


def select_cleanup_candidates(inventory: Any, protection: Any, approval: Any) -> Dict[str, Any]:
    """Return candidate IDs only when inventory and explicit approval agree."""

    blocked: List[str] = []
    result: Dict[str, Any] = {
        "selection_allowed": False,
        "candidate_ids": [],
        "blocked_reasons": blocked,
        "inventory_sha256": inventory.get("inventory_sha256") if isinstance(inventory, Mapping) else None,
    }
    values, config_errors = _protection_values(protection)
    for error in config_errors:
        _append_reason(blocked, error)
    if not isinstance(inventory, Mapping):
        _append_reason(blocked, "inventory is not an object")
        return result
    if inventory.get("repository") != (values or {}).get("repository"):
        _append_reason(blocked, "inventory repository mismatch")
    if inventory.get("complete") is not True:
        _append_reason(blocked, "inventory is not complete")
    if not isinstance(inventory.get("errors"), list):
        _append_reason(blocked, "inventory errors field is invalid")
    elif inventory["errors"]:
        _append_reason(blocked, "inventory contains errors")

    artifacts = inventory.get("artifacts")
    if not isinstance(artifacts, list):
        _append_reason(blocked, "inventory artifacts field is invalid")
        artifacts = []
    records_by_id: Dict[int, Mapping[str, Any]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, Mapping):
            _append_reason(blocked, "inventory contains a non-object artifact")
            continue
        artifact_id = artifact.get("id")
        if not _is_positive_int(artifact_id):
            _append_reason(blocked, "inventory contains an invalid artifact id")
            continue
        if artifact_id in records_by_id:
            _append_reason(blocked, "duplicate artifact id: %s" % artifact_id)
        records_by_id[artifact_id] = artifact

    try:
        expected_digest = compute_inventory_digest(inventory.get("repository"), artifacts)
    except (TypeError, ValueError):
        expected_digest = None
        _append_reason(blocked, "inventory digest cannot be computed")
    if not isinstance(inventory.get("inventory_sha256"), str) or inventory.get("inventory_sha256") != expected_digest:
        _append_reason(blocked, "inventory digest mismatch")
    if not isinstance(inventory.get("total_bytes"), int) or isinstance(inventory.get("total_bytes"), bool):
        _append_reason(blocked, "inventory total_bytes is invalid")
    else:
        measured_bytes = sum(
            artifact.get("size_in_bytes", 0)
            for artifact in artifacts
            if isinstance(artifact, Mapping) and _is_nonnegative_int(artifact.get("size_in_bytes"))
        )
        if inventory["total_bytes"] != measured_bytes:
            _append_reason(blocked, "inventory total_bytes mismatch")

    if not isinstance(approval, Mapping) or not approval:
        _append_reason(blocked, "approval manifest is missing")
        return result
    if approval.get("repository") != (values or {}).get("repository"):
        _append_reason(blocked, "approval repository mismatch")
    if approval.get("inventory_sha256") != inventory.get("inventory_sha256"):
        _append_reason(blocked, "approval digest mismatch")
    candidate_ids = approval.get("candidate_ids")
    entries = approval.get("entries")
    if not isinstance(candidate_ids, list) or not candidate_ids:
        _append_reason(blocked, "approval contains no candidates")
        candidate_ids = []
    valid_candidate_ids = [value for value in candidate_ids if _is_positive_int(value)]
    if len(valid_candidate_ids) != len(candidate_ids):
        _append_reason(blocked, "approval contains an invalid candidate id")
    if len(set(valid_candidate_ids)) != len(valid_candidate_ids):
        _append_reason(blocked, "approval contains duplicate candidate ids")
    if not isinstance(entries, list) or not entries:
        _append_reason(blocked, "approval entries are missing")
        entries = []
    entries_by_id: Dict[int, Mapping[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            _append_reason(blocked, "approval contains a non-object entry")
            continue
        entry_id = entry.get("artifact_id")
        if not _is_positive_int(entry_id):
            _append_reason(blocked, "approval contains an invalid entry id")
            continue
        if entry_id in entries_by_id:
            _append_reason(blocked, "duplicate approval entry id: %s" % entry_id)
        entries_by_id[entry_id] = entry
    if set(valid_candidate_ids) != set(entries_by_id):
        _append_reason(blocked, "approval candidate ids and entries differ")

    for artifact_id in sorted(set(valid_candidate_ids)):
        artifact = records_by_id.get(artifact_id)
        entry = entries_by_id.get(artifact_id)
        if artifact is None:
            _append_reason(blocked, "approval references unknown artifact id: %s" % artifact_id)
            continue
        if entry is None:
            continue
        for field in ("name", "size_in_bytes", "digest", "provenance"):
            if entry.get(field) != artifact.get(field):
                _append_reason(blocked, "approval %s mismatch for artifact id: %s" % (field, artifact_id))
        if entry.get("approved") is not True:
            _append_reason(blocked, "artifact id %s is not approved" % artifact_id)
        reason = entry.get("approval_reason")
        if not isinstance(reason, str) or not reason.strip():
            _append_reason(blocked, "artifact id %s has no approval reason" % artifact_id)
        classification = classify_artifact(artifact, protection)
        if classification["protected"] or classification["classification"] != "eligible":
            _append_reason(
                blocked,
                "artifact id %s is not eligible: %s (%s)"
                % (artifact_id, classification["classification"], "; ".join(classification["reasons"])),
            )

    if blocked:
        return result
    result["selection_allowed"] = True
    result["candidate_ids"] = sorted(valid_candidate_ids)
    return result
