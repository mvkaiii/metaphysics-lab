import re

CURRENT_CANDIDATE = "7c9c4a390a05cc78460bfcb615db76bc4c1791c7"
V160_TAG_SHA = "c325d754112df71c6747e17262d2e781d2864441"
AI_DISTRIBUTION_PATTERN = re.compile(
    r"^lin-tianji-v1\.(5|6|7)-(?:rebuilt-)?ai-distribution-([0-9a-f]{40})$"
)


def select_ai_distribution_cleanup_artifacts(artifacts):
    selected = []
    for artifact in artifacts:
        head_sha = artifact.get("head_sha")
        if head_sha in {CURRENT_CANDIDATE, V160_TAG_SHA}:
            continue
        match = AI_DISTRIBUTION_PATTERN.fullmatch(artifact.get("name", ""))
        if match is None:
            continue
        if match.group(2) != head_sha:
            continue
        selected.append(artifact)
    return selected
