CURRENT_CANDIDATE = "7c9c4a390a05cc78460bfcb615db76bc4c1791c7"
V160_TAG_SHA = "c325d754112df71c6747e17262d2e781d2864441"
RUN_NAME = "Phase 2C0 Final Acceptance"
RUN_PATH = ".github/workflows/phase2c0-final-acceptance.yml"
ARTIFACT_NAME = "phase2c0-local-private-source-bundle"

# Exact old validation/TDD provenance captured from GitHub on 2026-09-15.
# artifact_id: (workflow head SHA, workflow head branch)
ALLOWLIST = {
    9472509976: ("6f0311e2ce3685ec763a0c9cc6ef1d7a092393a7", "validation/phase2c0-main-postmerge"),
    9471797723: ("2ef43c7e72ef9f4c048ad016e2072ce94320071c", "validation/phase2c0-ci"),
    9471740460: ("8e22b9d1be5a5ed377b27f1f4a7cb1bc4244b69c", "validation/phase2c0-ci"),
    9471857418: ("215a12d2585997b644a203a3bbee1aca136d058c", "validation/phase2c0-feature-final"),
    9471759305: ("c7421ed7243031153e3200ea770d304d226f9282", "validation/phase2c0-ci"),
    9472311556: ("a2a1e44fe03d32ff5434883a568fb5a7568a9fdc", "validation/phase2c0-design-postmerge"),
    9471483673: ("3a99a4400e1bcf43d804440358da7b443a4fa008", "validation/phase2c0-ci"),
}


def select_phase2_cleanup_artifacts(artifacts):
    selected = []
    for artifact in artifacts:
        artifact_id = artifact.get("id")
        expected = ALLOWLIST.get(artifact_id)
        if expected is None:
            continue
        if artifact.get("head_sha") in {CURRENT_CANDIDATE, V160_TAG_SHA}:
            continue
        expected_sha, expected_branch = expected
        if artifact.get("name") != ARTIFACT_NAME:
            continue
        if artifact.get("head_sha") != expected_sha:
            continue
        if artifact.get("run_name") != RUN_NAME or artifact.get("run_path") != RUN_PATH:
            continue
        if artifact.get("head_branch") != expected_branch:
            continue
        selected.append(artifact)
    return selected
