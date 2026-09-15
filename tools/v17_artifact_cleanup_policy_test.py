from v17_artifact_cleanup_policy import select_cleanup_artifacts


def test_selects_only_exact_expired_allowlist():
    artifacts = [
        {"id": 9796463855, "name": "python39-ready-runtime-cbef8d9", "expired": True, "head_sha": "fc7824840b7e4fd065e59041d016dd63234f54fb"},
        {"id": 9796460218, "name": "python39-ready-runtime-cbef8d9", "expired": True, "head_sha": "fc7824840b7e4fd065e59041d016dd63234f54fb"},
        {"id": 123, "name": "python39-ready-runtime-cbef8d9", "expired": False, "head_sha": "fc7824840b7e4fd065e59041d016dd63234f54fb"},
        {"id": 456, "name": "release-evidence", "expired": True, "head_sha": "7c9c4a390a05cc78460bfcb615db76bc4c1791c7"},
    ]
    selected = select_cleanup_artifacts(artifacts)
    assert [item["id"] for item in selected] == [9796463855, 9796460218]


def test_never_selects_current_candidate_or_v160():
    artifacts = [
        {"id": 9796463855, "name": "python39-ready-runtime-cbef8d9", "expired": True, "head_sha": "7c9c4a390a05cc78460bfcb615db76bc4c1791c7"},
        {"id": 9796460218, "name": "python39-ready-runtime-cbef8d9", "expired": True, "head_sha": "c325d754112df71c6747e17262d2e781d2864441"},
    ]
    assert select_cleanup_artifacts(artifacts) == []
