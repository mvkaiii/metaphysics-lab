from __future__ import annotations

import importlib
from datetime import date
from typing import Protocol

from engine.vendor.manifest import bundled_dependency

from .models import (
    CalendarValidationDecision,
    LunarDate,
    LunarProviderMetadata,
    ValidationCheck,
)

EXPECTED_LUNAR_VERSION = "1.4.8"
LUNAR_SOURCE_REVISION = "000c8a3d74eed098d6256a28fdd51b869324c559"
CALENDAR_PROFILE = "hko-gregorian-lunar-1901-2100-v1"
VALIDATED_START = date(1901, 1, 1)
VALIDATED_END = date(2100, 12, 31)
VALIDATED_RANGE = "1901-01-01/2100-12-31"
CONFLICT_START = date(2057, 9, 28)
CONFLICT_END = date(2057, 10, 27)
CAUTION_BOUNDARIES = {
    date(2089, 9, 4): "hko-new-moon-2089-09-04-caution",
    date(2097, 8, 7): "hko-new-moon-2097-08-07-caution",
}
CONFLICT_BOUNDARY_ID = "hko-new-moon-2057-09-28-conflict"
_PRIVATE_LUNAR_MODULE = "_metaphysics_lab_vendor.lunar_python"


class LunarProviderUnsupportedDate(ValueError):
    pass


class LunarProviderFailure(RuntimeError):
    pass


class LunarCalendarProvider(Protocol):
    metadata: LunarProviderMetadata

    def convert(self, civil_date: date) -> LunarDate:
        ...


def _load_private_solar():
    """Load Solar only from the Project-private vendor namespace."""
    try:
        module = importlib.import_module(_PRIVATE_LUNAR_MODULE)
    except (ImportError, ModuleNotFoundError) as exc:
        raise LunarProviderFailure("bundled lunar-python provider is unavailable") from exc
    solar = getattr(module, "Solar", None)
    if solar is None:
        raise LunarProviderFailure("bundled lunar-python provider does not export Solar")
    return solar


class LunarPythonProvider:
    def __init__(self) -> None:
        try:
            metadata = bundled_dependency("lunar-python")
        except (KeyError, RuntimeError, ValueError) as exc:
            raise LunarProviderFailure("bundled lunar-python metadata is unavailable") from exc
        actual_version = str(metadata.get("version", ""))
        actual_revision = str(metadata.get("source_revision", ""))
        if actual_version != EXPECTED_LUNAR_VERSION or actual_revision != LUNAR_SOURCE_REVISION:
            raise LunarProviderFailure(
                "bundled lunar-python metadata does not match the pinned profile"
            )
        if metadata.get("runtime_authority") != "bundled" or metadata.get("bundled") is not True:
            raise LunarProviderFailure("lunar-python runtime authority is not bundled")
        self._solar = _load_private_solar()
        self.metadata = LunarProviderMetadata(
            name="lunar-python",
            version=actual_version,
            source_revision=actual_revision,
        )

    def convert(self, civil_date: date) -> LunarDate:
        try:
            lunar = self._solar.fromYmd(
                civil_date.year,
                civil_date.month,
                civil_date.day,
            ).getLunar()
            return LunarDate.from_provider_values(
                lunar.getYear(),
                lunar.getMonth(),
                lunar.getDay(),
            )
        except (ValueError, IndexError) as exc:
            raise LunarProviderUnsupportedDate(civil_date.isoformat()) from exc
        except LunarProviderUnsupportedDate:
            raise
        except Exception as exc:
            raise LunarProviderFailure(
                f"lunar-python failed for {civil_date.isoformat()}"
            ) from exc


def calendar_validation_for(civil_date: date) -> CalendarValidationDecision:
    if CONFLICT_START <= civil_date <= CONFLICT_END:
        return CalendarValidationDecision(
            check=ValidationCheck("boundary_conflict", CALENDAR_PROFILE),
            validated_range=VALIDATED_RANGE,
            boundary_id=CONFLICT_BOUNDARY_ID,
            notes=(
                "lunar-python 1.4.8 and the HKO validation oracle are known to differ in this boundary window.",
            ),
        )
    if civil_date in CAUTION_BOUNDARIES:
        return CalendarValidationDecision(
            check=ValidationCheck("boundary_caution", CALENDAR_PROFILE),
            validated_range=VALIDATED_RANGE,
            boundary_id=CAUTION_BOUNDARIES[civil_date],
            notes=(
                "HKO marks this new-moon boundary as astronomically sensitive; no current provider mismatch was observed.",
            ),
        )
    if not (VALIDATED_START <= civil_date <= VALIDATED_END):
        return CalendarValidationDecision(
            check=ValidationCheck("out_of_validated_range", CALENDAR_PROFILE),
            validated_range=VALIDATED_RANGE,
            boundary_id=None,
            notes=(
                "The runtime provider may compute this date, but it is outside the Project HKO exhaustive validated range.",
            ),
        )
    return CalendarValidationDecision(
        check=ValidationCheck("validated", CALENDAR_PROFILE),
        validated_range=VALIDATED_RANGE,
        boundary_id=None,
        notes=(),
    )
