import unittest

from tools.v17_artifact_lifecycle_policy import (
    ArtifactLifecyclePolicy,
    InventoryValidationError,
    retention_days_for,
    select_cleanup_candidates,
)


CURRENT_CANDIDATE = "7c9c4a390a05cc78460bfcb615db76bc4c1791c7"
FROZEN_V160 = "c325d754112df71c6747e17262d2e781d2864441"
OTHER_SHA = "0123456789abcdef0123456789abcdef01234567"
REPOSITORY = "mvkaiii/metaphysics-lab"


POLICY = ArtifactLifecyclePolicy(
    repository=REPOSITORY,
    current_candidate_sha=CURRENT_CANDIDATE,
    frozen_release_shas=frozenset({FROZEN_V160}),
    protected_artifact_ids=frozenset({9001}),
    protected_release_asset_names=frozenset(
        {
            "Metaphysics-Lab-v1.7.0-User-Package.zip",
            "metaphysics_lab.py",
            "metaphysics_core.md",
            "project_instructions.txt",
        }
    ),
    protected_evidence_names=frozenset({"v1.7-sealed-sandbox-evidence"}),
)


def make_artifact(
    *,
    artifact_id=1001,
    name="old-validation-snapshot",
    head_sha=OTHER_SHA,
    expired=True,
    workflow_path=".github/workflows/old-validation.yml",
    run_id=5001,
    run_attempt=1,
):
    return {
        "id": artifact_id,
        "name": name,
        "size_in_bytes": 1234,
        "expired": expired,
        "provenance": {
            "repository": REPOSITORY,
            "workflow_id": 77,
            "workflow_path": workflow_path,
            "run_id": run_id,
            "run_attempt": run_attempt,
            "head_sha": head_sha,
            "head_branch": "ci/old-validation",
        },
    }


def approval_for(artifact):
    provenance = artifact["provenance"]
    return {
        "artifact_id": artifact["id"],
        "name": artifact["name"],
        "size_in_bytes": artifact["size_in_bytes"],
        "repository": provenance["repository"],
        "workflow_path": provenance["workflow_path"],
        "workflow_id": provenance["workflow_id"],
        "run_id": provenance["run_id"],
        "run_attempt": provenance["run_attempt"],
        "head_sha": provenance["head_sha"],
        "approval_reason": "explicitly reviewed superseded validation snapshot",
        "approved": True,
    }


class ArtifactLifecyclePolicyTests(unittest.TestCase):
    def test_retention_policy_has_short_lived_classes_and_no_expiry_for_protected(self):
        self.assertEqual(retention_days_for("intermediate"), 1)
        self.assertEqual(retention_days_for("failure_log"), 3)
        self.assertEqual(retention_days_for("superseded_validation"), 7)
        for protected in (
            "current_candidate",
            "release_evidence",
            "frozen_release",
            "unknown",
        ):
            with self.subTest(protected=protected):
                self.assertIsNone(retention_days_for(protected))

    def test_exact_expired_approved_artifact_is_selected(self):
        artifact = make_artifact()
        selected = select_cleanup_candidates(
            [artifact],
            {artifact["id"]: approval_for(artifact)},
            policy=POLICY,
            snapshot_complete=True,
        )
        self.assertEqual(selected, [artifact])

    def test_current_candidate_is_always_protected(self):
        artifact = make_artifact(head_sha=CURRENT_CANDIDATE)
        self.assertEqual(
            select_cleanup_candidates(
                [artifact],
                {artifact["id"]: approval_for(artifact)},
                policy=POLICY,
                snapshot_complete=True,
            ),
            [],
        )

    def test_frozen_release_is_always_protected(self):
        artifact = make_artifact(head_sha=FROZEN_V160)
        self.assertEqual(
            select_cleanup_candidates(
                [artifact],
                {artifact["id"]: approval_for(artifact)},
                policy=POLICY,
                snapshot_complete=True,
            ),
            [],
        )

    def test_release_asset_name_is_protected_even_with_old_provenance(self):
        artifact = make_artifact(name="metaphysics_lab.py")
        self.assertEqual(
            select_cleanup_candidates(
                [artifact],
                {artifact["id"]: approval_for(artifact)},
                policy=POLICY,
                snapshot_complete=True,
            ),
            [],
        )

    def test_release_evidence_name_is_protected(self):
        artifact = make_artifact(name="v1.7-sealed-sandbox-evidence")
        self.assertEqual(
            select_cleanup_candidates(
                [artifact],
                {artifact["id"]: approval_for(artifact)},
                policy=POLICY,
                snapshot_complete=True,
            ),
            [],
        )

    def test_unknown_or_incomplete_provenance_is_not_selected(self):
        artifact = make_artifact()
        del artifact["provenance"]["workflow_path"]
        self.assertEqual(
            select_cleanup_candidates(
                [artifact],
                {artifact["id"]: approval_for(make_artifact())},
                policy=POLICY,
                snapshot_complete=True,
            ),
            [],
        )

    def test_approval_mismatch_is_not_selected(self):
        artifact = make_artifact()
        approval = approval_for(artifact)
        approval["run_id"] += 1
        self.assertEqual(
            select_cleanup_candidates(
                [artifact],
                {artifact["id"]: approval},
                policy=POLICY,
                snapshot_complete=True,
            ),
            [],
        )

    def test_nonexpired_artifact_is_not_selected(self):
        artifact = make_artifact(expired=False)
        self.assertEqual(
            select_cleanup_candidates(
                [artifact],
                {artifact["id"]: approval_for(artifact)},
                policy=POLICY,
                snapshot_complete=True,
            ),
            [],
        )

    def test_incomplete_snapshot_fails_closed(self):
        artifact = make_artifact()
        with self.assertRaises(InventoryValidationError):
            select_cleanup_candidates(
                [artifact],
                {artifact["id"]: approval_for(artifact)},
                policy=POLICY,
                snapshot_complete=False,
            )

    def test_duplicate_ids_fail_closed(self):
        first = make_artifact(artifact_id=1001)
        second = make_artifact(artifact_id=1001, name="different")
        with self.assertRaises(InventoryValidationError):
            select_cleanup_candidates(
                [first, second],
                {first["id"]: approval_for(first)},
                policy=POLICY,
                snapshot_complete=True,
            )


if __name__ == "__main__":
    unittest.main()
