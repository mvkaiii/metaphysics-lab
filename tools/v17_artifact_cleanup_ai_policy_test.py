from v17_artifact_cleanup_ai_policy import select_ai_distribution_cleanup_artifacts


def test_selects_only_exact_ai_distribution_with_matching_suffix_sha():
    sha = "64c00db9d08a5aa007cee570ef503ba9874b6824"
    artifacts = [
        {
            "id": 10319914504,
            "name": f"lin-tianji-v1.5-rebuilt-ai-distribution-{sha}",
            "head_sha": sha,
            "size_in_bytes": 807950,
        },
        {
            "id": 1,
            "name": f"lin-tianji-v1.5-rebuilt-ai-distribution-{sha}",
            "head_sha": "0" * 40,
            "size_in_bytes": 1,
        },
        {
            "id": 2,
            "name": f"lin-tianji-v1.5-package-{sha}",
            "head_sha": sha,
            "size_in_bytes": 1,
        },
    ]
    selected = select_ai_distribution_cleanup_artifacts(artifacts)
    assert [item["id"] for item in selected] == [10319914504]


def test_never_selects_current_candidate_or_v160():
    current = "7c9c4a390a05cc78460bfcb615db76bc4c1791c7"
    v160 = "c325d754112df71c6747e17262d2e781d2864441"
    artifacts = [
        {
            "id": 1,
            "name": f"lin-tianji-v1.7-ai-distribution-{current}",
            "head_sha": current,
            "size_in_bytes": 1,
        },
        {
            "id": 2,
            "name": f"lin-tianji-v1.6-ai-distribution-{v160}",
            "head_sha": v160,
            "size_in_bytes": 1,
        },
    ]
    assert select_ai_distribution_cleanup_artifacts(artifacts) == []


def test_rejects_non_hex_or_wrong_length_sha_suffix():
    artifacts = [
        {
            "id": 1,
            "name": "lin-tianji-v1.7-ai-distribution-not-a-sha",
            "head_sha": "not-a-sha",
            "size_in_bytes": 1,
        },
        {
            "id": 2,
            "name": "lin-tianji-v1.7-ai-distribution-1234",
            "head_sha": "1234",
            "size_in_bytes": 1,
        },
    ]
    assert select_ai_distribution_cleanup_artifacts(artifacts) == []
