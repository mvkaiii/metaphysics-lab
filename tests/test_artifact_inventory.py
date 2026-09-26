import unittest
from urllib.parse import parse_qs, urlsplit

from tools.artifact_inventory import collect_inventory, compute_inventory_digest


REPOSITORY = "mvkaiii/metaphysics-lab"
OTHER_SHA = "0123456789abcdef0123456789abcdef01234567"


def _artifact_page(artifacts, total_count=None):
    if total_count is None:
        total_count = len(artifacts)
    return {"total_count": total_count, "artifacts": artifacts}


def _artifact(artifact_id=1001, name="old-validation-snapshot"):
    return {
        "id": artifact_id,
        "name": name,
        "size_in_bytes": 1234,
        "expired": True,
        "digest": "sha256:" + "a" * 64,
        "workflow_run": {
            "id": 5001,
            "head_branch": "ci/old-validation",
            "head_sha": OTHER_SHA,
        },
    }


def _run():
    return {
        "id": 5001,
        "workflow_id": 77,
        "path": ".github/workflows/old-validation.yml",
        "run_attempt": 1,
        "head_branch": "ci/old-validation",
        "head_sha": OTHER_SHA,
    }


class ArtifactInventoryTests(unittest.TestCase):
    def test_collect_inventory_fetches_pages_and_run_provenance(self):
        calls = []
        page_calls = []

        def fetch_json(url):
            calls.append(url)
            parsed = urlsplit(url)
            query = parse_qs(parsed.query)
            if parsed.path.endswith("/actions/artifacts"):
                page = int(query["page"][0])
                page_calls.append(page)
                if page == 1:
                    return _artifact_page(
                        [_artifact(artifact_id=index) for index in range(1000, 1100)],
                        total_count=101,
                    )
                if page == 2:
                    return _artifact_page([_artifact(artifact_id=1100)], total_count=101)
            if url.endswith("/actions/runs/5001"):
                return _run()
            raise AssertionError(url)

        inventory = collect_inventory(fetch_json, REPOSITORY)

        self.assertTrue(inventory["complete"])
        self.assertEqual(inventory["total_bytes"], 101 * 1234)
        self.assertEqual(
            inventory["total_bytes_scope"],
            "repository_artifact_metadata_only_not_account_or_org_billing_quota",
        )
        self.assertEqual(inventory["artifacts"][0]["provenance"]["run_attempt"], 1)
        self.assertEqual(page_calls, [1, 2])
        self.assertEqual(sum("/actions/runs/" in call for call in calls), 1)

    def test_short_page_is_terminal_and_page_is_parsed_as_a_query_parameter(self):
        calls = []

        def fetch_json(url):
            calls.append(url)
            parsed = urlsplit(url)
            query = parse_qs(parsed.query)
            if parsed.path.endswith("/actions/artifacts"):
                self.assertEqual(query["per_page"], ["100"])
                self.assertEqual(query["page"], ["1"])
                return _artifact_page([_artifact()])
            return _run()

        inventory = collect_inventory(fetch_json, REPOSITORY)

        self.assertTrue(inventory["complete"])
        self.assertEqual(len(inventory["artifacts"]), 1)
        self.assertEqual(len(calls), 2)

    def test_duplicate_artifact_across_pages_is_incomplete(self):
        page = [_artifact(artifact_id=index) for index in range(1000, 1100)]

        def fetch_json(url):
            parsed = urlsplit(url)
            if parsed.path.endswith("/actions/artifacts"):
                page_number = int(parse_qs(parsed.query)["page"][0])
                return _artifact_page(page if page_number == 1 else [page[0]], total_count=101)
            return _run()

        inventory = collect_inventory(fetch_json, REPOSITORY)

        self.assertFalse(inventory["complete"])
        self.assertTrue(any("duplicate artifact" in error for error in inventory["errors"]))

    def test_run_id_branch_and_sha_must_match_artifact_workflow_run(self):
        def fetch_json(url):
            if "/actions/artifacts?" in url:
                record = _artifact()
                record["workflow_run"]["head_branch"] = "candidate-branch"
                return _artifact_page([record])
            run = _run()
            run["head_branch"] = "different-branch"
            return run

        inventory = collect_inventory(fetch_json, REPOSITORY)

        self.assertFalse(inventory["complete"])
        self.assertTrue(any("head_branch" in error for error in inventory["errors"]))

    def test_missing_run_metadata_is_incomplete_and_fail_closed(self):
        def fetch_json(url):
            if "actions/artifacts" in url:
                return _artifact_page([_artifact()])
            raise RuntimeError("run endpoint unavailable")

        inventory = collect_inventory(fetch_json, REPOSITORY)

        self.assertFalse(inventory["complete"])
        self.assertTrue(inventory["errors"])
        self.assertIsNone(inventory["artifacts"][0]["provenance"]["run_id"])

    def test_invalid_page_is_incomplete(self):
        inventory = collect_inventory(lambda _url: {"unexpected": []}, REPOSITORY)

        self.assertFalse(inventory["complete"])
        self.assertEqual(inventory["artifacts"], [])
        self.assertTrue(any("invalid artifact page" in error for error in inventory["errors"]))

    def test_missing_total_count_is_incomplete(self):
        inventory = collect_inventory(
            lambda _url: {"artifacts": [_artifact()]}, REPOSITORY
        )

        self.assertFalse(inventory["complete"])
        self.assertTrue(any("total_count" in error for error in inventory["errors"]))

    def test_short_page_cannot_hide_records_reported_by_total_count(self):
        inventory = collect_inventory(
            lambda _url: _artifact_page([_artifact()], total_count=2), REPOSITORY
        )

        self.assertFalse(inventory["complete"])
        self.assertTrue(any("pagination" in error for error in inventory["errors"]))

    def test_total_count_must_remain_stable_across_pages(self):
        page = [_artifact(artifact_id=index) for index in range(1000, 1100)]

        def fetch_json(url):
            parsed = urlsplit(url)
            if parsed.path.endswith("/actions/artifacts"):
                page_number = int(parse_qs(parsed.query)["page"][0])
                return _artifact_page(
                    page if page_number == 1 else [_artifact(artifact_id=1100)],
                    total_count=101 if page_number == 1 else 102,
                )
            return _run()

        inventory = collect_inventory(fetch_json, REPOSITORY)

        self.assertFalse(inventory["complete"])
        self.assertTrue(any("total_count changed" in error for error in inventory["errors"]))

    def test_boolean_total_count_is_invalid(self):
        inventory = collect_inventory(
            lambda _url: _artifact_page([_artifact()], total_count=True), REPOSITORY
        )

        self.assertFalse(inventory["complete"])
        self.assertTrue(any("total_count" in error for error in inventory["errors"]))

    def test_workflow_path_with_ref_suffix_is_validated(self):
        def fetch_json(url):
            if "/actions/artifacts?" in url:
                return _artifact_page([_artifact()])
            run = _run()
            run["path"] += "@main"
            return run

        inventory = collect_inventory(fetch_json, REPOSITORY)

        self.assertTrue(inventory["complete"], inventory["errors"])
        self.assertEqual(
            inventory["artifacts"][0]["provenance"]["workflow_path"],
            ".github/workflows/old-validation.yml@main",
        )

    def test_rerun_artifact_without_attempt_binding_is_incomplete(self):
        def fetch_json(url):
            if "/actions/artifacts?" in url:
                return _artifact_page([_artifact()])
            run = _run()
            run["run_attempt"] = 2
            return run

        inventory = collect_inventory(fetch_json, REPOSITORY)

        self.assertFalse(inventory["complete"])
        self.assertIsNone(inventory["artifacts"][0]["provenance"]["run_attempt"])
        self.assertTrue(any("attempt provenance is ambiguous" in error for error in inventory["errors"]))

    def test_artifact_attempt_binding_must_match_run_attempt(self):
        def fetch_json(url):
            if "/actions/artifacts?" in url:
                record = _artifact()
                record["workflow_run"]["run_attempt"] = 2
                return _artifact_page([record])
            return _run()

        inventory = collect_inventory(fetch_json, REPOSITORY)

        self.assertFalse(inventory["complete"])
        self.assertIsNone(inventory["artifacts"][0]["provenance"]["run_attempt"])
        self.assertTrue(any("run_attempt mismatch" in error for error in inventory["errors"]))

    def test_run_metadata_without_attempt_is_incomplete(self):
        def fetch_json(url):
            if "/actions/artifacts?" in url:
                return _artifact_page([_artifact()])
            run = _run()
            run.pop("run_attempt")
            return run

        inventory = collect_inventory(fetch_json, REPOSITORY)

        self.assertFalse(inventory["complete"])
        self.assertIsNone(inventory["artifacts"][0]["provenance"]["run_attempt"])
        self.assertTrue(any("run_attempt" in error for error in inventory["errors"]))

    def test_run_id_must_match_artifact_workflow_run(self):
        def fetch_json(url):
            if "/actions/artifacts?" in url:
                return _artifact_page([_artifact()])
            run = _run()
            run["id"] = 5002
            return run

        inventory = collect_inventory(fetch_json, REPOSITORY)

        self.assertFalse(inventory["complete"])
        self.assertTrue(any("run id mismatch" in error for error in inventory["errors"]))

    def test_digest_is_deterministic_and_covers_artifact_digest(self):
        artifacts = [_artifact()]
        first = compute_inventory_digest(REPOSITORY, artifacts)
        second = compute_inventory_digest(REPOSITORY, list(reversed(artifacts)))
        changed = _artifact()
        changed["digest"] = "sha256:" + "c" * 64
        changed_digest = compute_inventory_digest(REPOSITORY, [changed])

        self.assertEqual(first, second)
        self.assertNotEqual(first, changed_digest)
        self.assertEqual(len(first), 64)

    def test_sha_mismatch_in_api_and_run_is_recorded_as_incomplete(self):
        def fetch_json(url):
            if "actions/artifacts" in url:
                return _artifact_page([_artifact()])
            result = _run()
            result["head_sha"] = "f" * 40
            return result

        inventory = collect_inventory(fetch_json, REPOSITORY)

        self.assertFalse(inventory["complete"])
        self.assertTrue(any("head_sha" in error for error in inventory["errors"]))


if __name__ == "__main__":
    unittest.main()
