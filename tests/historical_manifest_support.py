from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import subprocess
import tempfile

from engine.distribution.manifest import capability_manifest_digest, load_capability_manifest


ROOT = Path(__file__).resolve().parents[1]
_REGISTRY_FILES = (
    "birth/capabilities.py",
    "bazi/capabilities.py",
    "distribution/capabilities.py",
    "historical/capabilities.py",
    "natal/capabilities.py",
    "ziwei/capabilities.py",
)


@lru_cache(maxsize=None)
def historical_capability_manifest_digest(commit: str) -> str:
    """Recompute a frozen candidate manifest from that candidate's Git tree."""

    with tempfile.TemporaryDirectory() as directory:
        engine_root = Path(directory) / "engine"
        for relative in _REGISTRY_FILES:
            completed = subprocess.run(
                ["git", "-C", str(ROOT), "show", "%s:engine/%s" % (commit, relative)],
                check=False,
                capture_output=True,
            )
            if completed.returncode != 0:
                raise AssertionError(
                    "historical capability registry is unavailable for %s: %s"
                    % (commit, relative)
                )
            target = engine_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(completed.stdout)
        return capability_manifest_digest(load_capability_manifest(engine_root))
