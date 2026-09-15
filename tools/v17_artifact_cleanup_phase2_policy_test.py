from v17_artifact_cleanup_phase2_policy import select_phase2_cleanup_artifacts


def test_selects_only_exact_phase2_validation_bundle():
    artifacts = [
        {
            "id": 9472509976,
            "name": "phase2c0-local-private-source-bundle",
            "expired": False,
            "head_sha": "6f0311e2ce3685ec763a0c9cc6ef1d7a092393a7",
            "run_name": "Phase 2C0 Final Acceptance",
            "run_path": ".github/workflows/phase2c0-final-acceptance.yml",
            "head_branch": "validation/phase2c0-main-postmerge",
        },
        {
            "id": 9472509976,
            "name": "phase2c0-local-private-source-bundle",
            "expired": False,
            "head_sha": "6f0311e2ce3685ec763a0c9cc6ef1d7a092393a7",
            "run_name": "Phase 2C0 Final Acceptance",
            "run_path": ".github/workflows/phase2c0-final-acceptance.yml",
            "head_branch": "release/v1.7.0-integration",
        },
    ]
    selected = select_phase2_cleanup_artifacts(artifacts)
    assert [item["id"] for item in selected] == [9472509976]


def test_never_selects_current_candidate_or_v160():
    artifacts = [
        {
            "id": 9472509976,
            "name": "phase2c0-local-private-source-bundle",
            "expired": False,
            "head_sha": "7c9c4a390a05cc78460bfcb615db76bc4c1791c7",
            "run_name": "Phase 2C0 Final Acceptance",
            "run_path": ".github/workflows/phase2c0-final-acceptance.yml",
            "head_branch": "validation/phase2c0-main-postmerge",
        },
        {
            "id": 9471797723,
            "name": "phase2c0-local-private-source-bundle",
            "expired": False,
            "head_sha": "c325d754112df71c6747e17262d2e781d2864441",
            "run_name": "Phase 2C0 Final Acceptance",
            "run_path": ".github/workflows/phase2c0-final-acceptance.yml",
            "head_branch": "validation/phase2c0-ci",
        },
    ]
    assert select_phase2_cleanup_artifacts(artifacts) == []
