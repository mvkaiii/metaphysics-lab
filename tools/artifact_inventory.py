"""Read-only GitHub Actions artifact inventory collection.

``total_bytes`` sums repository artifact metadata sizes only; it is not an
account or organization billing-quota measurement.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.artifact_lifecycle_policy import compute_inventory_digest


API_ROOT = "https://api.github.com"
PAGE_SIZE = 100
TOTAL_BYTES_SCOPE = "repository_artifact_metadata_only_not_account_or_org_billing_quota"
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_WORKFLOW_PATH = re.compile(r"^\.github/workflows/[^/]+\.ya?ml(?:@[^\r\n]+)?$")


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _normalise_artifact(
    raw_artifact: Mapping[str, Any],
    repository: str,
    run: Optional[Mapping[str, Any]],
    run_attempt: Optional[int] = None,
    run_attempt_source: Optional[str] = None,
) -> Dict[str, Any]:
    run_payload = run if isinstance(run, Mapping) else {}
    return {
        "id": raw_artifact.get("id"),
        "name": raw_artifact.get("name"),
        "size_in_bytes": raw_artifact.get("size_in_bytes"),
        "expired": raw_artifact.get("expired"),
        "digest": raw_artifact.get("digest"),
        "provenance": {
            "repository": repository,
            "workflow_id": run_payload.get("workflow_id"),
            "workflow_path": run_payload.get("path"),
            "run_id": run_payload.get("id"),
            "run_attempt": run_attempt,
            "run_attempt_source": run_attempt_source,
            "head_sha": run_payload.get("head_sha"),
            "head_branch": run_payload.get("head_branch"),
        },
    }


def _validate_raw_artifact(raw_artifact: Mapping[str, Any]) -> List[str]:
    errors: List[str] = []
    if not _is_positive_int(raw_artifact.get("id")):
        errors.append("invalid artifact id")
    if not isinstance(raw_artifact.get("name"), str) or not raw_artifact.get("name"):
        errors.append("missing artifact name")
    if not _is_nonnegative_int(raw_artifact.get("size_in_bytes")):
        errors.append("invalid size_in_bytes")
    if not isinstance(raw_artifact.get("expired"), bool):
        errors.append("missing artifact expiration status")
    digest = raw_artifact.get("digest")
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        errors.append("missing or invalid artifact digest")
    return errors


def collect_inventory(
    fetch_json: Callable[[str], Mapping[str, Any]], repository: str
) -> Dict[str, Any]:
    """Collect all pages and verify artifact metadata against each workflow run."""

    errors: List[str] = []
    artifacts: List[Dict[str, Any]] = []
    if not isinstance(repository, str) or repository.count("/") != 1 or not all(repository.split("/")):
        errors.append("repository must be owner/repository")
        return {
            "repository": repository,
            "complete": False,
            "artifacts": [],
            "errors": errors,
            "total_bytes": 0,
            "total_bytes_scope": TOTAL_BYTES_SCOPE,
            "inventory_sha256": compute_inventory_digest(str(repository), []),
        }

    encoded_repository = quote(repository, safe="/")
    seen_artifact_ids = set()
    run_cache: Dict[int, Optional[Mapping[str, Any]]] = {}
    expected_total_count: Optional[int] = None
    page = 1
    while True:
        page_url = "%s/repos/%s/actions/artifacts?per_page=%d&page=%d" % (
            API_ROOT,
            encoded_repository,
            PAGE_SIZE,
            page,
        )
        try:
            payload = fetch_json(page_url)
        except Exception as exc:  # pragma: no cover - API transport failures
            errors.append("artifact page %d unavailable: %s" % (page, exc))
            break
        page_artifacts = payload.get("artifacts") if isinstance(payload, Mapping) else None
        if not isinstance(page_artifacts, list):
            errors.append("invalid artifact page %d: artifacts must be a list" % page)
            break
        page_total_count = payload.get("total_count")
        if not _is_nonnegative_int(page_total_count):
            errors.append("invalid or missing total_count on page %d" % page)
        elif expected_total_count is None:
            expected_total_count = page_total_count
        elif page_total_count != expected_total_count:
            errors.append("total_count changed between artifact pages")
        if _is_nonnegative_int(page_total_count) and len(page_artifacts) > page_total_count:
            errors.append("artifact page %d exceeds its total_count" % page)

        duplicate_count = 0
        for raw_artifact in page_artifacts:
            if not isinstance(raw_artifact, Mapping):
                errors.append("invalid artifact record on page %d" % page)
                continue
            artifact_id = raw_artifact.get("id")
            if _is_positive_int(artifact_id) and artifact_id in seen_artifact_ids:
                errors.append("duplicate artifact id across pages: %s" % artifact_id)
                duplicate_count += 1
                continue
            if _is_positive_int(artifact_id):
                seen_artifact_ids.add(artifact_id)
            for error in _validate_raw_artifact(raw_artifact):
                errors.append("artifact %s: %s" % (artifact_id, error))

            workflow_run = raw_artifact.get("workflow_run")
            if not isinstance(workflow_run, Mapping) or not _is_positive_int(workflow_run.get("id")):
                errors.append("missing workflow run metadata for artifact %s" % artifact_id)
                artifacts.append(_normalise_artifact(raw_artifact, repository, None))
                continue

            run_id = workflow_run["id"]
            if run_id not in run_cache:
                run_url = "%s/repos/%s/actions/runs/%s" % (API_ROOT, encoded_repository, run_id)
                try:
                    run_result = fetch_json(run_url)
                except Exception as exc:
                    errors.append("run metadata unavailable for artifact %s: %s" % (artifact_id, exc))
                    run_result = None
                run_cache[run_id] = run_result if isinstance(run_result, Mapping) else None
            run = run_cache[run_id]
            if run is None:
                artifacts.append(_normalise_artifact(raw_artifact, repository, None))
                continue

            if run.get("id") != run_id:
                errors.append("run id mismatch for artifact %s" % artifact_id)
            for field in ("head_sha", "head_branch"):
                artifact_value = workflow_run.get(field)
                run_value = run.get(field)
                if not isinstance(artifact_value, str) or not artifact_value:
                    errors.append("missing %s in artifact workflow_run for %s" % (field, artifact_id))
                elif artifact_value != run_value:
                    errors.append("%s mismatch for artifact %s" % (field, artifact_id))
            if not _is_positive_int(run.get("id")) or not _is_positive_int(run.get("workflow_id")):
                errors.append("invalid run or workflow id in metadata for artifact %s" % artifact_id)
            normalized_attempt: Optional[int] = None
            attempt_source: Optional[str] = None
            run_attempt_number = run.get("run_attempt")
            if not _is_positive_int(run_attempt_number):
                errors.append("missing or invalid run_attempt in metadata for artifact %s" % artifact_id)
            elif "run_attempt" in workflow_run:
                artifact_attempt = workflow_run.get("run_attempt")
                if not _is_positive_int(artifact_attempt):
                    errors.append("invalid run_attempt in artifact workflow_run for %s" % artifact_id)
                elif artifact_attempt != run_attempt_number:
                    errors.append("run_attempt mismatch for artifact %s" % artifact_id)
                else:
                    normalized_attempt = artifact_attempt
                    attempt_source = "artifact_workflow_run"
            elif run_attempt_number == 1:
                normalized_attempt = 1
                attempt_source = "single_attempt_run_metadata"
            else:
                errors.append(
                    "attempt provenance is ambiguous after workflow rerun for artifact %s"
                    % artifact_id
                )
            if not isinstance(run.get("path"), str) or not _WORKFLOW_PATH.fullmatch(run.get("path", "")):
                errors.append("missing or invalid workflow path in metadata for artifact %s" % artifact_id)
            if not isinstance(run.get("head_sha"), str) or not _SHA40.fullmatch(run.get("head_sha", "")):
                errors.append("missing or invalid head_sha in metadata for artifact %s" % artifact_id)
            if not isinstance(run.get("head_branch"), str) or not run.get("head_branch"):
                errors.append("missing or invalid head_branch in metadata for artifact %s" % artifact_id)
            artifacts.append(
                _normalise_artifact(
                    raw_artifact,
                    repository,
                    run,
                    normalized_attempt,
                    attempt_source,
                )
            )

        if page_artifacts and duplicate_count == len(page_artifacts):
            errors.append("repeated artifact page detected at page %d" % page)
            break
        if len(page_artifacts) < PAGE_SIZE:
            break
        page += 1

    if expected_total_count is not None and len(seen_artifact_ids) != expected_total_count:
        errors.append(
            "artifact pagination count mismatch: expected %d records, observed %d unique ids"
            % (expected_total_count, len(seen_artifact_ids))
        )

    total_bytes = 0
    for artifact in artifacts:
        size = artifact.get("size_in_bytes")
        if _is_nonnegative_int(size):
            total_bytes += size

    try:
        inventory_sha256 = compute_inventory_digest(repository, artifacts)
    except (TypeError, ValueError):
        errors.append("inventory digest could not be computed")
        inventory_sha256 = None
    return {
        "repository": repository,
        "complete": not errors,
        "artifacts": artifacts,
        "errors": errors,
        "total_bytes": total_bytes,
        "total_bytes_scope": TOTAL_BYTES_SCOPE,
        "inventory_sha256": inventory_sha256,
    }


def _fetch_json_from_github(token: str) -> Callable[[str], Mapping[str, Any]]:
    def fetch_json(url: str) -> Mapping[str, Any]:
        request = Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer %s" % token,
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "metaphysics-lab-artifact-inventory",
            },
        )
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    return fetch_json


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/repository")
    args = parser.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        parser.error("GITHUB_TOKEN or GH_TOKEN is required")
    inventory = collect_inventory(_fetch_json_from_github(token), args.repo)
    print(json.dumps(inventory, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if inventory["complete"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
