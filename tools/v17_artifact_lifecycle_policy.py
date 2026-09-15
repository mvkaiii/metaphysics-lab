"""Fail-closed policy for GitHub Actions artifact retention and cleanup.

This module deliberately has no GitHub client and performs no deletion.  A
caller must provide a complete, already-enriched inventory snapshot and an
explicit per-artifact approval record before an item can be selected.
"""

from dataclasses import dataclass
from typing import Any, FrozenSet, Mapping, Optional, Sequence


SHA_LENGTH = 40
RETENTION_DAYS = {
    "intermediate": 1,
    "failure_log": 3,
    "superseded_validation": 7,
    "current_candidate": None,
    "release_evidence": None,
    "frozen_release": None,
    "unknown": None,
}

_PROVENANCE_FIELDS = frozenset(
    {
        "repository",
        "workflow_id",
        "workflow_path",
        "run_id",
        "run_attempt",
        "head_sha",
        "head_branch",
    }
)
_APPROVAL_FIELDS = frozenset(
    {
        "artifact_id",
        "name",
        "size_in_bytes",
        "repository",
        "workflow_id",
        "workflow_path",
        "run_id",
        "run_attempt",
        "head_sha",
        "approval_reason",
        "approved",
    }
)


class InventoryValidationError(ValueError):
    """Raised when a cleanup decision cannot safely use the inventory."""


@dataclass(frozen=True)
class ArtifactLifecyclePolicy:
    repository: str
    current_candidate_sha: str
    frozen_release_shas: FrozenSet[str]
    protected_artifact_ids: FrozenSet[int]
    protected_release_asset_names: FrozenSet[str]
    protected_evidence_names: FrozenSet[str]

    def __post_init__(self):
        if not self.repository:
            raise InventoryValidationError("repository is required")
        if not _is_sha(self.current_candidate_sha):
            raise InventoryValidationError("current candidate SHA is invalid")
        if any(not _is_sha(sha) for sha in self.frozen_release_shas):
            raise InventoryValidationError("frozen release SHA is invalid")
        if any(not _is_positive_int(value) for value in self.protected_artifact_ids):
            raise InventoryValidationError("protected artifact ID is invalid")


def retention_days_for(artifact_class: str) -> Optional[int]:
    """Return the approved retention period; protected classes never expire."""

    if artifact_class not in RETENTION_DAYS:
        raise ValueError("unknown artifact class: %s" % artifact_class)
    return RETENTION_DAYS[artifact_class]


def classify_artifact(
    artifact: Mapping[str, Any],
    approval: Optional[Mapping[str, Any]],
    *,
    policy: ArtifactLifecyclePolicy,
) -> str:
    """Classify one artifact without making a mutation or network call."""

    if not isinstance(artifact, Mapping):
        return "unknown_provenance"

    artifact_id = artifact.get("id")
    name = artifact.get("name")
    if artifact_id in policy.protected_artifact_ids:
        return "protected_artifact"
    if name in policy.protected_release_asset_names:
        return "protected_release_asset"
    if name in policy.protected_evidence_names:
        return "protected_evidence"
    if isinstance(name, str) and any(
        marker in name.lower() for marker in ("evidence", "sandbox", "qualification")
    ):
        return "protected_evidence"

    provenance = artifact.get("provenance")
    observed_head_sha = artifact.get("head_sha")
    if isinstance(provenance, Mapping):
        observed_head_sha = provenance.get("head_sha", observed_head_sha)
    if observed_head_sha == policy.current_candidate_sha:
        return "current_candidate"
    if observed_head_sha in policy.frozen_release_shas:
        return "frozen_release"

    if not _has_complete_provenance(artifact, policy):
        return "unknown_provenance"
    if artifact.get("expired") is not True:
        return "not_expired"
    if not _approval_matches(artifact, approval, policy):
        return "not_approved"
    return "eligible"


def select_cleanup_candidates(
    artifacts: Sequence[Mapping[str, Any]],
    approvals: Mapping[int, Mapping[str, Any]],
    *,
    policy: ArtifactLifecyclePolicy,
    snapshot_complete: bool,
):
    """Select only explicitly approved, expired, provenance-verified artifacts.

    ``snapshot_complete`` is mandatory because deleting from a partial page can
    bypass a protected artifact that was not fetched.  The returned list is a
    decision only; this function never calls a delete endpoint.
    """

    if snapshot_complete is not True:
        raise InventoryValidationError("complete inventory snapshot is required")
    if not isinstance(approvals, Mapping):
        raise InventoryValidationError("approval manifest must be a mapping")

    seen_ids = set()
    selected = []
    for artifact in artifacts:
        artifact_id = artifact.get("id") if isinstance(artifact, Mapping) else None
        if artifact_id in seen_ids:
            raise InventoryValidationError("duplicate artifact ID in snapshot")
        if _is_positive_int(artifact_id):
            seen_ids.add(artifact_id)
        approval = approvals.get(artifact_id)
        if (
            classify_artifact(artifact, approval, policy=policy)
            == "eligible"
        ):
            selected.append(artifact)
    return selected


def _has_complete_provenance(
    artifact: Mapping[str, Any], policy: ArtifactLifecyclePolicy
) -> bool:
    if not _is_positive_int(artifact.get("id")):
        return False
    if not isinstance(artifact.get("name"), str) or not artifact["name"]:
        return False
    if not _is_nonnegative_int(artifact.get("size_in_bytes")):
        return False
    if not isinstance(artifact.get("expired"), bool):
        return False

    provenance = artifact.get("provenance")
    if not isinstance(provenance, Mapping):
        return False
    if not _PROVENANCE_FIELDS.issubset(provenance):
        return False
    if provenance.get("repository") != policy.repository:
        return False
    if not _is_positive_int(provenance.get("workflow_id")):
        return False
    if not _is_positive_int(provenance.get("run_id")):
        return False
    if not _is_positive_int(provenance.get("run_attempt")):
        return False
    workflow_path = provenance.get("workflow_path")
    if (
        not isinstance(workflow_path, str)
        or not workflow_path.startswith(".github/workflows/")
        or not workflow_path.endswith((".yml", ".yaml"))
    ):
        return False
    if not isinstance(provenance.get("head_branch"), str) or not provenance["head_branch"]:
        return False
    return _is_sha(provenance.get("head_sha"))


def _approval_matches(
    artifact: Mapping[str, Any],
    approval: Optional[Mapping[str, Any]],
    policy: ArtifactLifecyclePolicy,
) -> bool:
    if not isinstance(approval, Mapping):
        return False
    if not _APPROVAL_FIELDS.issubset(approval):
        return False
    if approval.get("approved") is not True:
        return False
    reason = approval.get("approval_reason")
    if not isinstance(reason, str) or not reason.strip():
        return False

    provenance = artifact["provenance"]
    expected = {
        "artifact_id": artifact.get("id"),
        "name": artifact.get("name"),
        "size_in_bytes": artifact.get("size_in_bytes"),
        "repository": policy.repository,
        "workflow_id": provenance.get("workflow_id"),
        "workflow_path": provenance.get("workflow_path"),
        "run_id": provenance.get("run_id"),
        "run_attempt": provenance.get("run_attempt"),
        "head_sha": provenance.get("head_sha"),
    }
    return all(approval.get(key) == value for key, value in expected.items())


def _is_sha(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == SHA_LENGTH
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
