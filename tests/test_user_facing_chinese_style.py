from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_NOTES = ROOT / "docs"

ALLOWED_PHRASES = (
    "Metaphysics Lab",
    "Candidate Envelope v2",
    "Guided Natal Build",
    "Case Revision Integrity",
    "Lock Provenance v2",
    "Visualization P1",
    "GitHub Release",
    "Project Contract",
    "Runtime Schema",
    "Case Schema",
    "AI Distribution Runtime",
    "Capability Manifest",
    "Git tag",
    "Base Case",
)

ALLOWED_WORDS = {
    "AI",
    "Python",
    "SVG",
    "SHA256",
    "main",
    "selector",
    "interpretation",
}

FORBIDDEN_PHRASES = (
    "流程 authority",
    "為 authority",
    "Stable promotion",
    "schema migration",
    "revision identity",
    "revision lineage",
    "revision-aware",
    "prospective lock",
    "blind lock",
    "回填 provenance",
    "保持 readable",
    "仍為 default",
    "material state",
    "deterministic SVG",
    "Fresh-host",
    "focused regression",
    "governance regression",
    "repository regression",
    "clean tree",
    "merged main SHA",
    "軟體與資料治理release",
    "預測效度promotion",
    "capability implementation",
    "capability maturity",
)


def _latest_release_note() -> Path:
    candidates = []
    pattern = re.compile(r"發布說明-v(\d+)\.(\d+)\.(\d+)\.md$")
    for path in RELEASE_NOTES.glob("發布說明-v*.md"):
        match = pattern.fullmatch(path.name)
        if match:
            candidates.append((tuple(int(part) for part in match.groups()), path))
    if not candidates:
        raise AssertionError("no release note found")
    return max(candidates)[1]


def _strip_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", "", text)
    return text


def _remove_allowed_phrases(text: str) -> str:
    for phrase in ALLOWED_PHRASES:
        text = text.replace(phrase, "")
    return text


def test_latest_release_note_uses_natural_zh_tw():
    path = _latest_release_note()
    text = _strip_code(path.read_text(encoding="utf-8"))

    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in text, f"{path}: avoid mixed-language phrase: {phrase}"

    prose = _remove_allowed_phrases(text)
    # Version identifiers are formal tokens, including short forms such as v1/v2
    # and component versions such as 1.5-exp. Do not flag them as prose English.
    prose = re.sub(
        r"(?<![A-Za-z0-9_])v\d+(?:\.\d+)*(?:-[A-Za-z0-9.]+)?(?![A-Za-z0-9_])",
        "",
        prose,
    )
    prose = re.sub(
        r"(?<![A-Za-z0-9_])\d+(?:\.\d+)+(?:-[A-Za-z0-9.]+)?(?![A-Za-z0-9_])",
        "",
        prose,
    )
    prose = re.sub(r"\b[A-Fa-f0-9]{16,}\b", "", prose)

    unexpected = []
    for lineno, line in enumerate(prose.splitlines(), start=1):
        if not re.search(r"[\u3400-\u9fff]", line):
            continue
        words = re.findall(r"\b[A-Za-z][A-Za-z0-9_-]*\b", line)
        words = [word for word in words if word not in ALLOWED_WORDS]
        if words:
            unexpected.append((lineno, words, line.strip()))

    assert not unexpected, (
        f"{path}: unexpected English words in Chinese prose; "
        "use Chinese wording or add a narrowly scoped formal-name exception: "
        + repr(unexpected)
    )
