from __future__ import annotations

from datetime import date
from importlib.metadata import PackageNotFoundError, version
from typing import Protocol

from lunar_python import Solar

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


class LunarProviderUnsupportedDate(ValueError):
    pass


class LunarProviderFailure(RuntimeError):
    pass


class LunarCalendarProvider(Protocol):
    metadata: LunarProviderMetadata

    def convert(self, civil_date: date) -> LunarDate:
        ...


class LunarPythonProvider:
    def __init__(self) -> None:
        try:
            installed = version("lunar_python")
        except PackageNotFoundError as exc:
            raise LunarProviderFailure("lunar-python package is not installed") from exc
        if installed != EXPECTED_LUNAR_VERSION:
            raise LunarProviderFailure(
                f"expected lunar-python {EXPECTED_LUNAR_VERSION}, got {installed}"
            )
        self.metadata = LunarProviderMetadata(
            name="lunar-python",
            version=installed,
            source_revision=LUNAR_SOURCE_REVISION,
        )

    def convert(self, civil_date: date) -> LunarDate:
        try:
            lunar = Solar.fromYmd(
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
