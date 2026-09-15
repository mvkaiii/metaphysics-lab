CURRENT_CANDIDATE = "7c9c4a390a05cc78460bfcb615db76bc4c1791c7"
V160_TAG_SHA = "c325d754112df71c6747e17262d2e781d2864441"

# Third-round cleanup batch 1: exact expired helper/runtime/workspace artifacts.
# Each entry is artifact_id: (exact_name, exact_workflow_head_sha).
ALLOWLIST = {
    9796463855: ("python39-ready-runtime-cbef8d9", "fc7824840b7e4fd065e59041d016dd63234f54fb"),
    9796460218: ("python39-ready-runtime-cbef8d9", "fc7824840b7e4fd065e59041d016dd63234f54fb"),
    9796357784: ("python39-runtime-cbef8d9", "023fbd827974078d5e15b7eced418ba8d86646d5"),
    9796371478: ("python39-runtime-cbef8d9", "76af364df161f3b08dc07e299b9e610d9be2ec09"),
    9796375980: ("python39-runtime-cbef8d9", "76af364df161f3b08dc07e299b9e610d9be2ec09"),
    9796736454: ("git-history-cbef8d9", "2c8822bab7b8df532e800af18afe834f995d594d"),
    9796730677: ("git-history-cbef8d9", "2c8822bab7b8df532e800af18afe834f995d594d"),
    9826218413: ("intake-workspace-b82741a", "5ce7f9a3863d81a81139e204cad7c519eff17307"),
    9809723718: ("s1-workspace-c9420d3", "fbefc5f5f00979037feaed874ab7365f4b211dd5"),
    9802266974: ("metaphysics-lab-q1-frozen-workspace", "e7a8fca2b3b4e4286bdf6a44a5c8d539cb129b47"),
    9796270292: ("metaphysics-lab-local-snapshot-cbef8d9", "da4c04aefebdc9123c4716a473711cb95a39e436"),
}


def select_cleanup_artifacts(artifacts):
    selected = []
    for artifact in artifacts:
        artifact_id = artifact.get("id")
        expected = ALLOWLIST.get(artifact_id)
        if expected is None or artifact.get("expired") is not True:
            continue
        if artifact.get("head_sha") in {CURRENT_CANDIDATE, V160_TAG_SHA}:
            continue
        expected_name, expected_sha = expected
        if artifact.get("name") != expected_name or artifact.get("head_sha") != expected_sha:
            continue
        selected.append(artifact)
    return selected
