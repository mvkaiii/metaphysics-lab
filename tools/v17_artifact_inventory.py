"""Read-only GitHub Actions artifact inventory and cleanup decision report.

The command intentionally has no delete operation.  It enriches each artifact
with workflow-run provenance, then delegates all cleanup selection to the
fail-closed lifecycle policy.
"""

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple
from urllib.parse import quote
from urllib.request import Request, urlopen

try:
    from tools.v17_artifact_lifecycle_policy import (
        ArtifactLifecyclePolicy,
        InventoryValidationError,
        classify_artifact,
        select_cleanup_candidates,
    )
except ImportError:  # pragma: no cover - supports direct script execution.
    from v17_artifact_lifecycle_policy import (  # type: ignore
        ArtifactLifecyclePolicy,
        InventoryValidationError,
        classify_artifact,
        select_cleanup_candidates,
    )


API_ROOT = "https://api.github.com"
CURRENT_CANDIDATE_SHA = "7c9c4a390a05cc78460bfcb615db76bc4c1791c7"
FROZEN_V160_SHA = "c325d754112df71c6747e17262d2e781d2864441"
RELEASE_ASSET_NAMES = frozenset(
    {
        "Metaphysics-Lab-v1.6.0-User-Package.zip",
        "Metaphysics-Lab-v1.7.0-User-Package.zip",
        "metaphysics_lab.py",
        "metaphysics_core.md",
        "project_instructions.txt",
    }
)
PAGE_SIZE = 100
JsonOpener = Callable[..., Any]


def default_policy(
    repository: str,
    protected_evidence_names: Sequence[str] = (),
) -> ArtifactLifecyclePolicy:
    return ArtifactLifecyclePolicy(
        repository=repository,
        current_candidate_sha=CURRENT_CANDIDATE_SHA,
        frozen_release_shas=frozenset({FROZEN_V160_SHA}),
        protected_artifact_ids=frozenset(),
        protected_release_asset_names=RELEASE_ASSET_NAMES,
        protected_evidence_names=frozenset(protected_evidence_names),
    )


def normalize_artifact(
    artifact: Mapping[str, Any],
    workflow_run: Mapping[str, Any],
    *,
    repository: str,
) -> Dict[str, Any]:
    """Create the policy's normalized artifact record from two API responses."""

    api_workflow_run = artifact.get("workflow_run")
    run_id = workflow_run.get("id")
    if isinstance(api_workflow_run, Mapping) and api_workflow_run.get("id") is not None:
        if run_id != api_workflow_run.get("id"):
            run_id = None

    return {
        "id": artifact.get("id"),
        "name": artifact.get("name"),
        "size_in_bytes": artifact.get("size_in_bytes"),
        "expired": artifact.get("expired"),
        "provenance": {
            "repository": repository,
            "workflow_id": workflow_run.get("workflow_id"),
            "workflow_path": workflow_run.get("path"),
            "run_id": run_id,
            "run_attempt": workflow_run.get("run_attempt"),
            "head_sha": workflow_run.get("head_sha"),
            "head_branch": workflow_run.get("head_branch"),
        },
    }


def summarize_inventory(
    artifacts: Sequence[Mapping[str, Any]],
    approvals: Mapping[int, Mapping[str, Any]],
    *,
    policy: ArtifactLifecyclePolicy,
    snapshot_complete: bool,
) -> Dict[str, Any]:
    """Return a deterministic report; never performs a deletion."""

    classification_counts = Counter(
        classify_artifact(
            artifact,
            approvals.get(artifact.get("id"))
            if isinstance(artifact, Mapping)
            else None,
            policy=policy,
        )
        for artifact in artifacts
    )
    total_bytes = sum(
        artifact.get("size_in_bytes", 0)
        for artifact in artifacts
        if isinstance(artifact, Mapping)
        and isinstance(artifact.get("size_in_bytes"), int)
        and not isinstance(artifact.get("size_in_bytes"), bool)
        and artifact.get("size_in_bytes") >= 0
    )

    cleanup_candidates = []
    cleanup_decision = "read_only_no_approval_manifest"
    if snapshot_complete is not True:
        cleanup_decision = "blocked_incomplete_snapshot"
    elif approvals:
        try:
            cleanup_candidates = select_cleanup_candidates(
                artifacts,
                approvals,
                policy=policy,
                snapshot_complete=True,
            )
            cleanup_decision = (
                "candidates_available" if cleanup_candidates else "no_eligible_candidates"
            )
        except InventoryValidationError:
            cleanup_decision = "blocked_invalid_snapshot"

    return {
        "repository": policy.repository,
        "snapshot_complete": snapshot_complete is True,
        "artifact_count": len(artifacts),
        "total_bytes": total_bytes,
        "classification_counts": dict(sorted(classification_counts.items())),
        "cleanup_decision": cleanup_decision,
        "cleanup_candidate_ids": [item["id"] for item in cleanup_candidates],
        "cleanup_candidate_bytes": sum(
            item.get("size_in_bytes", 0) for item in cleanup_candidates
        ),
    }


def collect_inventory(
    repository: str,
    token: str,
    *,
    opener: JsonOpener = urlopen,
) -> Tuple[Sequence[Mapping[str, Any]], bool]:
    """Fetch a complete artifact inventory and enrich it with run metadata."""

    raw_artifacts = _fetch_all_artifacts(repository, token, opener=opener)
    run_cache: Dict[int, Mapping[str, Any]] = {}
    records = []
    complete = True
    for artifact in raw_artifacts:
        workflow_run = artifact.get("workflow_run") if isinstance(artifact, Mapping) else None
        run_id = workflow_run.get("id") if isinstance(workflow_run, Mapping) else None
        if not _is_positive_int(run_id):
            complete = False
            run = {}
        else:
            if run_id not in run_cache:
                try:
                    run_cache[run_id] = _fetch_run(
                        repository, run_id, token, opener=opener
                    )
                except Exception:
                    complete = False
                    run_cache[run_id] = {}
            run = run_cache[run_id]
            if not run:
                complete = False
        records.append(normalize_artifact(artifact, run, repository=repository))
    return records, complete


def _fetch_all_artifacts(
    repository: str,
    token: str,
    *,
    opener: JsonOpener,
) -> Sequence[Mapping[str, Any]]:
    all_artifacts = []
    page = 1
    while True:
        payload = _fetch_json(
            "%s/repos/%s/actions/artifacts?per_page=%d&page=%d"
            % (API_ROOT, quote(repository, safe="/"), PAGE_SIZE, page),
            token,
            opener=opener,
        )
        artifacts = payload.get("artifacts") if isinstance(payload, Mapping) else None
        if not isinstance(artifacts, list):
            raise InventoryValidationError("artifact API returned an invalid page")
        all_artifacts.extend(artifacts)
        if len(artifacts) < PAGE_SIZE:
            return all_artifacts
        page += 1


def _fetch_run(
    repository: str,
    run_id: int,
    token: str,
    *,
    opener: JsonOpener,
) -> Mapping[str, Any]:
    return _fetch_json(
        "%s/repos/%s/actions/runs/%d"
        % (API_ROOT, quote(repository, safe="/"), run_id),
        token,
        opener=opener,
    )


def _fetch_json(url: str, token: str, *, opener: JsonOpener) -> Mapping[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with opener(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise InventoryValidationError("GitHub API returned a non-object response")
    return payload


def _load_approvals(path: Optional[Path]) -> Mapping[int, Mapping[str, Any]]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("approvals") if isinstance(payload, Mapping) else payload
    if not isinstance(entries, list):
        raise InventoryValidationError("approval manifest must contain a list")
    approvals = {}
    for entry in entries:
        if not isinstance(entry, Mapping) or not _is_positive_int(entry.get("artifact_id")):
            raise InventoryValidationError("approval manifest contains an invalid entry")
        if entry["artifact_id"] in approvals:
            raise InventoryValidationError("approval manifest contains duplicate IDs")
        approvals[entry["artifact_id"]] = entry
    return approvals


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--approval-manifest", type=Path)
    parser.add_argument("--protected-evidence-name", action="append", default=[])
    args = parser.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not args.repo or not token:
        parser.error("--repo/GITHUB_REPOSITORY and GITHUB_TOKEN/GH_TOKEN are required")

    try:
        records, complete = collect_inventory(args.repo, token)
        approvals = _load_approvals(args.approval_manifest)
        report = summarize_inventory(
            records,
            approvals,
            policy=default_policy(args.repo, args.protected_evidence_name),
            snapshot_complete=complete,
        )
    except Exception as exc:
        print("inventory blocked: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if complete else 2


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
