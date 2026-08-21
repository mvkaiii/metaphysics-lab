from __future__ import annotations

from types import MappingProxyType

from .common import PALACE_NAMES, validate_palace
from .errors import ZiweiPhase2AError
from .models import PalaceStemIndex, StarLocationIndex

LEGAL_STEMS = tuple("甲乙丙丁戊己庚辛壬癸")


def build_star_location_index(records, chart_identity, provenance):
    materialized = {}
    for record in records:
        try:
            validate_palace(record.palace)
        except ValueError as exc:
            raise ZiweiPhase2AError(
                "invalid_palace",
                str(exc),
                {"palace": record.palace},
            ) from exc
        if not record.star:
            raise ZiweiPhase2AError("missing_star_location", "star must not be empty")
        if record.star in materialized:
            raise ZiweiPhase2AError(
                "duplicate_star_location",
                "duplicate star input",
                {"star": record.star},
            )
        materialized[record.star] = record.palace
    return StarLocationIndex(
        chart_identity,
        MappingProxyType(materialized),
        "validated",
        provenance,
    )


def build_palace_stem_index(records, chart_identity, provenance):
    materialized = {}
    for record in records:
        try:
            validate_palace(record.palace)
        except ValueError as exc:
            raise ZiweiPhase2AError(
                "invalid_palace",
                str(exc),
                {"palace": record.palace},
            ) from exc
        if record.palace in materialized:
            raise ZiweiPhase2AError(
                "duplicate_palace_stem",
                "duplicate palace stem input",
                {"palace": record.palace},
            )
        if record.heavenly_stem not in LEGAL_STEMS:
            raise ZiweiPhase2AError(
                "invalid_palace_stem_index",
                "invalid palace heavenly stem",
                {"stem": record.heavenly_stem},
            )
        materialized[record.palace] = record.heavenly_stem
    if len(materialized) != 12 or set(materialized) != set(PALACE_NAMES):
        raise ZiweiPhase2AError(
            "invalid_palace_stem_index",
            "all twelve canonical palaces are required",
        )
    return PalaceStemIndex(
        chart_identity,
        MappingProxyType(materialized),
        "validated",
        provenance,
    )
