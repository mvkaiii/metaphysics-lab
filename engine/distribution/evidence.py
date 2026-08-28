"""Compatibility wrapper for Phase 3.5 structural evidence authority.

Formal prospective evidence normalization is owned by
``engine.distribution.structural_interpretation``.  This module preserves the
legacy public import surface without retaining a second semantic authority.
"""

from __future__ import annotations

from .structural_interpretation import interpret_structural_evidence
from .structural_policy import BAZI_TEN_GOD_MAPPING, MAPPING_PROFILE, ZIWEI_PALACE_MAPPING


def build_evidence_features(
    forecast_context,
    target_scope,
    mapping_profile=MAPPING_PROFILE,
):
    """Return the v2 structural interpretation through the legacy wrapper."""

    interpreted = interpret_structural_evidence(
        forecast_context,
        target_scope,
        mapping_profile=mapping_profile,
    )
    return {
        "features": interpreted["features"],
        "target_scope": interpreted["target_scope"],
        "mapping_profile": interpreted["mapping_profile_version"],
        "source_context_digest": interpreted["source_context_digest"],
        "interpretation_digest": interpreted["interpretation_digest"],
    }
