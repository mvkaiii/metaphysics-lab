import copy
import json
import unittest
from pathlib import Path

from tools.artifact_lifecycle_policy import (
    classify_artifact,
    compute_inventory_digest,
    retention_days_for,
    select_cleanup_candidates,
)


CURRENT_SHA = "7c9c4a390a05cc78460bfcb615db76bc4c1791c7"
FROZEN_SHA = "c325d754112df71c6747e17262d2e781d2864441"
OTHER_SHA = "0123456789abcdef0123456789abcdef01234567"
FROZEN_V170_SHA = "1123456789abcdef0123456789abcdef01234567"
REPOSITORY = "mvkaiii/metaphysics-lab"
PROTECTION_CONFIG_PATH = Path(__file__).parents[1] / "config" / "artifact-protection.json"


PROTECTION = {
    "repository": REPOSITORY,
    "current_candidate_shas": [CURRENT_SHA],
    "frozen_release_shas": [FROZEN_SHA, FROZEN_V170_SHA],
    "protected_artifact_ids": [9001],
    "protected_release_asset_names": ["metaphysics_lab.py"],
    "protected_evidence_names": ["sealed-v1.7-evidence"],
    "protected_evidence_markers": ["sandbox", "qualification", "evidence"],
    "protected_evidence_sha256": ["sha256:" + "a" * 64],
}


def artifact(
    artifact_id=1001,
    name="old-validation-snapshot",
    head_sha=OTHER_SHA,
    expired=True,
):
    return {
        "id": artifact_id,
        "name": name,
        "size_in_bytes": 1234,
        "expired": expired,
        "digest": "sha256:" + "b" * 64,
        "provenance": {
            "repository": REPOSITORY,
            "workflow_id": 77,
            "workflow_path": ".github/workflows/old-validation.yml",
            "run_id": 5001,
            "run_attempt": 1,
            "head_sha": head_sha,
            "head_branch": "ci/old-validation",
        },
    }


def approval(inventory, records):
    return {
        "repository": REPOSITORY,
        "inventory_sha256": inventory["inventory_sha256"],
        "candidate_ids": [record["id"] for record in records],
        "entries": [
            {
                "artifact_id": record["id"],
                "name": record["name"],
                "size_in_bytes": record["size_in_bytes"],
                "digest": record["digest"],
                "provenance": copy.deepcopy(record["provenance"]),
                "approval_reason": "explicitly reviewed superseded validation snapshot",
                "approved": True,
            }
            for record in records
        ],
    }


def inventory(records, complete=True):
    return {
        "repository": REPOSITORY,
        "complete": complete,
        "artifacts": records,
        "errors": [],
        "total_bytes": sum(record["size_in_bytes"] for record in records),
        "inventory_sha256": compute_inventory_digest(REPOSITORY, records),
    }


class ArtifactLifecyclePolicyTests(unittest.TestCase):
    def test_repository_protection_config_pins_current_and_frozen_release_identities(self):
        self.assertTrue(PROTECTION_CONFIG_PATH.is_file(), "artifact protection config is missing")
        protection = json.loads(PROTECTION_CONFIG_PATH.read_text(encoding="utf-8"))

        self.assertEqual(protection["repository"], REPOSITORY)
        self.assertEqual(
            set(protection["current_candidate_shas"]),
            {
                "872c60b2e959ea48d25524b74686e488f576ec6f",
                "933cdc735de345e1bb7cf45eb679beb46b10a237",
                "270ee223f779f6621c0c74434799886f1df4af92",
            },
        )
        self.assertEqual(
            set(protection["frozen_release_shas"]),
            {
                "872c60b2e959ea48d25524b74686e488f576ec6f",
                "24760aa8766eb2691c8878f2cd8b97f0b37f8964",
                "c325d754112df71c6747e17262d2e781d2864441",
            },
        )
        self.assertTrue(
            {
                "Metaphysics-Lab-v1.7.1-User-Package.zip",
                "Metaphysics-Lab-v1.7.0-User-Package.zip",
                "Metaphysics-Lab-v1.6.0-User-Package.zip",
                "metaphysics_lab.py",
                "metaphysics_core.md",
                "project_instructions.txt",
            }.issubset(set(protection["protected_release_asset_names"]))
        )

    def test_repository_protection_config_protects_current_hosted_evidence(self):
        protection = json.loads(PROTECTION_CONFIG_PATH.read_text(encoding="utf-8"))
        evidence = (
            (10900492481, "lin-tianji-v1.7-ai-distribution-933cdc735de345e1bb7cf45eb679beb46b10a237", "sha256:cc43e3b0f85947035740fc3e579f09a9ff8f7df03510f7b737500378b2dd2fb5"),
            (10900567224, "lin-tianji-v1.6-ai-distribution-933cdc735de345e1bb7cf45eb679beb46b10a237", "sha256:8250e963c38753c7b35d8841c22572087d582a9d9c27ccbe286883be655d9fbe"),
            (10901001174, "lin-tianji-v1.5-ai-distribution-933cdc735de345e1bb7cf45eb679beb46b10a237", "sha256:8250e963c38753c7b35d8841c22572087d582a9d9c27ccbe286883be655d9fbe"),
            (10900802188, "lin-tianji-v1.5-rebuilt-ai-distribution-933cdc735de345e1bb7cf45eb679beb46b10a237", "sha256:8250e963c38753c7b35d8841c22572087d582a9d9c27ccbe286883be655d9fbe"),
        )
        for artifact_id, name, digest in evidence:
            record = artifact(artifact_id=artifact_id, name=name, head_sha="933cdc735de345e1bb7cf45eb679beb46b10a237")
            record["digest"] = digest
            result = classify_artifact(record, protection)
            self.assertTrue(result["protected"], (artifact_id, result))

    def test_retention_classes_are_explicit_and_protected_never_expire(self):
        self.assertEqual(retention_days_for("intermediate"), 1)
        self.assertEqual(retention_days_for("failure_log"), 3)
        self.assertEqual(retention_days_for("superseded_validation"), 7)
        for protected in ("current_candidate", "release_evidence", "frozen_release", "unknown"):
            self.assertIsNone(retention_days_for(protected))

    def test_current_candidate_and_frozen_release_are_protected(self):
        for value, expected in (
            (CURRENT_SHA, "current_candidate"),
            (FROZEN_SHA, "frozen_release"),
            (FROZEN_V170_SHA, "frozen_release"),
        ):
            result = classify_artifact(artifact(head_sha=value), PROTECTION)
            self.assertEqual(result["classification"], expected)
            self.assertTrue(result["protected"])

    def test_current_candidate_may_also_be_a_frozen_release(self):
        protection = copy.deepcopy(PROTECTION)
        protection["current_candidate_shas"].append(FROZEN_SHA)

        result = classify_artifact(artifact(head_sha=FROZEN_SHA), protection)

        self.assertEqual(result["classification"], "frozen_release")
        self.assertTrue(result["protected"])

    def test_workflow_path_with_ref_suffix_is_valid_provenance(self):
        record = artifact()
        record["provenance"]["workflow_path"] += "@main"

        result = classify_artifact(record, PROTECTION)

        self.assertEqual(result["classification"], "eligible")
        self.assertFalse(result["protected"])

    def test_release_evidence_and_release_asset_are_protected(self):
        self.assertEqual(
            classify_artifact(artifact(name="sealed-v1.7-evidence"), PROTECTION)["classification"],
            "protected_evidence",
        )
        self.assertEqual(
            classify_artifact(artifact(name="metaphysics_lab.py"), PROTECTION)["classification"],
            "protected_release_asset",
        )

    def test_protected_evidence_digest_is_protected(self):
        record = artifact()
        record["digest"] = PROTECTION["protected_evidence_sha256"][0]

        result = classify_artifact(record, PROTECTION)

        self.assertEqual(result["classification"], "protected_evidence")
        self.assertTrue(result["protected"])

    def test_unknown_provenance_is_protected(self):
        record = artifact()
        del record["provenance"]["run_attempt"]

        result = classify_artifact(record, PROTECTION)

        self.assertEqual(result["classification"], "unknown_provenance")
        self.assertTrue(result["protected"])

    def test_filename_sha_conflicting_with_run_sha_is_protected(self):
        record = artifact(name="snapshot-" + CURRENT_SHA, head_sha=OTHER_SHA)

        result = classify_artifact(record, PROTECTION)

        self.assertEqual(result["classification"], "unknown_provenance")
        self.assertTrue(result["protected"])
        self.assertTrue(any("filename" in reason for reason in result["reasons"]))

    def test_expired_approved_artifact_is_selectable(self):
        record = artifact()
        snapshot = inventory([record])

        result = select_cleanup_candidates(snapshot, PROTECTION, approval(snapshot, [record]))

        self.assertTrue(result["selection_allowed"])
        self.assertEqual(result["candidate_ids"], [record["id"]])
        self.assertEqual(result["blocked_reasons"], [])

    def test_empty_approval_cannot_select(self):
        record = artifact()
        snapshot = inventory([record])

        result = select_cleanup_candidates(snapshot, PROTECTION, {})

        self.assertFalse(result["selection_allowed"])
        self.assertEqual(result["candidate_ids"], [])
        self.assertTrue(any("approval" in reason for reason in result["blocked_reasons"]))

    def test_stale_digest_cannot_select(self):
        record = artifact()
        snapshot = inventory([record])
        manifest = approval(snapshot, [record])
        manifest["inventory_sha256"] = "0" * 64

        result = select_cleanup_candidates(snapshot, PROTECTION, manifest)

        self.assertFalse(result["selection_allowed"])
        self.assertTrue(any("digest" in reason for reason in result["blocked_reasons"]))

    def test_incomplete_snapshot_cannot_select(self):
        record = artifact()
        snapshot = inventory([record], complete=False)
        manifest = approval(snapshot, [record])

        result = select_cleanup_candidates(snapshot, PROTECTION, manifest)

        self.assertFalse(result["selection_allowed"])
        self.assertTrue(any("complete" in reason for reason in result["blocked_reasons"]))

    def test_provenance_mismatch_cannot_select(self):
        record = artifact()
        snapshot = inventory([record])
        manifest = approval(snapshot, [record])
        manifest["entries"][0]["provenance"]["run_attempt"] = 2

        result = select_cleanup_candidates(snapshot, PROTECTION, manifest)

        self.assertFalse(result["selection_allowed"])
        self.assertTrue(any("provenance" in reason for reason in result["blocked_reasons"]))
        self.assertEqual(snapshot["inventory_sha256"], compute_inventory_digest(REPOSITORY, [record]))

    def test_duplicate_ids_cannot_select(self):
        first = artifact()
        second = artifact(name="different")
        snapshot = inventory([first, second])

        result = select_cleanup_candidates(snapshot, PROTECTION, approval(snapshot, [first, second]))

        self.assertFalse(result["selection_allowed"])
        self.assertTrue(any("duplicate" in reason for reason in result["blocked_reasons"]))

    def test_foreign_repository_cannot_select(self):
        record = artifact()
        record["provenance"]["repository"] = "other/repo"
        snapshot = inventory([record])

        result = select_cleanup_candidates(snapshot, PROTECTION, approval(snapshot, [record]))

        self.assertFalse(result["selection_allowed"])
        self.assertTrue(any("repository" in reason for reason in result["blocked_reasons"]))

    def test_malformed_inventory_and_approval_fail_closed_without_crashing(self):
        result = select_cleanup_candidates(
            {"repository": REPOSITORY, "complete": True, "artifacts": [None], "errors": [], "inventory_sha256": "bad"},
            PROTECTION,
            {"repository": REPOSITORY, "inventory_sha256": "bad", "candidate_ids": [{}], "entries": [None]},
        )

        self.assertFalse(result["selection_allowed"])
        self.assertEqual(result["candidate_ids"], [])
        self.assertTrue(result["blocked_reasons"])


if __name__ == "__main__":
    unittest.main()
