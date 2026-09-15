import unittest

from tools.v17_artifact_inventory import (
    default_policy,
    normalize_artifact,
    summarize_inventory,
)


CURRENT_CANDIDATE = "7c9c4a390a05cc78460bfcb615db76bc4c1791c7"
OTHER_SHA = "0123456789abcdef0123456789abcdef01234567"
REPOSITORY = "mvkaiii/metaphysics-lab"


def make_api_artifact(*, name="old-validation-snapshot", artifact_id=1001):
    return {
        "id": artifact_id,
        "name": name,
        "size_in_bytes": 1234,
        "expired": True,
        "workflow_run": {
            "id": 5001,
            "head_branch": "ci/old-validation",
            "head_sha": OTHER_SHA,
        },
    }


def make_run():
    return {
        "id": 5001,
        "workflow_id": 77,
        "path": ".github/workflows/old-validation.yml",
        "run_attempt": 1,
        "head_branch": "ci/old-validation",
        "head_sha": OTHER_SHA,
    }


def approval_for(record):
    provenance = record["provenance"]
    return {
        "artifact_id": record["id"],
        "name": record["name"],
        "size_in_bytes": record["size_in_bytes"],
        "repository": provenance["repository"],
        "workflow_id": provenance["workflow_id"],
        "workflow_path": provenance["workflow_path"],
        "run_id": provenance["run_id"],
        "run_attempt": provenance["run_attempt"],
        "head_sha": provenance["head_sha"],
        "approval_reason": "explicitly reviewed superseded validation snapshot",
        "approved": True,
    }


class ArtifactInventoryTests(unittest.TestCase):
    def test_normalize_artifact_requires_enriched_workflow_provenance(self):
        record = normalize_artifact(
            make_api_artifact(),
            make_run(),
            repository=REPOSITORY,
        )
        self.assertEqual(record["id"], 1001)
        self.assertEqual(record["provenance"]["workflow_id"], 77)
        self.assertEqual(
            record["provenance"]["workflow_path"],
            ".github/workflows/old-validation.yml",
        )
        self.assertEqual(record["provenance"]["run_attempt"], 1)

    def test_summary_selects_only_approved_candidate_from_complete_snapshot(self):
        record = normalize_artifact(
            make_api_artifact(),
            make_run(),
            repository=REPOSITORY,
        )
        summary = summarize_inventory(
            [record],
            {record["id"]: approval_for(record)},
            policy=default_policy(REPOSITORY),
            snapshot_complete=True,
        )
        self.assertEqual(summary["artifact_count"], 1)
        self.assertEqual(summary["total_bytes"], 1234)
        self.assertEqual(summary["cleanup_candidate_ids"], [1001])
        self.assertEqual(summary["cleanup_decision"], "candidates_available")

    def test_incomplete_snapshot_has_no_cleanup_candidates(self):
        record = normalize_artifact(
            make_api_artifact(),
            make_run(),
            repository=REPOSITORY,
        )
        summary = summarize_inventory(
            [record],
            {record["id"]: approval_for(record)},
            policy=default_policy(REPOSITORY),
            snapshot_complete=False,
        )
        self.assertEqual(summary["cleanup_candidate_ids"], [])
        self.assertEqual(summary["cleanup_decision"], "blocked_incomplete_snapshot")

    def test_evidence_like_name_is_protected_by_default(self):
        record = normalize_artifact(
            make_api_artifact(name="v1.7-sandbox-evidence"),
            make_run(),
            repository=REPOSITORY,
        )
        summary = summarize_inventory(
            [record],
            {record["id"]: approval_for(record)},
            policy=default_policy(REPOSITORY),
            snapshot_complete=True,
        )
        self.assertEqual(summary["cleanup_candidate_ids"], [])
        self.assertEqual(summary["classification_counts"]["protected_evidence"], 1)


if __name__ == "__main__":
    unittest.main()
