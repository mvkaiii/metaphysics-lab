from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ZiweiNatalProfile:
    """Versioned rule identity for the Project-native Ziwei natal builder."""

    profile_id: str = "ziwei-natal-true-solar-common-v1"
    rule_version: str = "1.0-exp"
    time_basis: str = "true_solar"
    star_catalog: str = "ziwei-core-stars-v1"
    brightness_profile: str = "ziwei-brightness-common-v1"
    decadal_profile: str = "ziwei-decadal-common-v1"
