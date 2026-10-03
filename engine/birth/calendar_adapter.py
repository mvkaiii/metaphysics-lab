from __future__ import annotations

from datetime import datetime
from typing import Optional

from engine.calendar import CalendarResolution, resolve_calendar

from .errors import BirthFoundationError
from .models import BirthInput, ResolvedBirthPlace


def resolve_birth_calendar(
    input: BirthInput,
    location: ResolvedBirthPlace,
    utc_offset_hint: Optional[str] = None,
) -> CalendarResolution:
    if input.birth_time is None or input.birth_time_precision != "exact":
        raise BirthFoundationError(
            "ambiguous_birth_time",
            "birth calendar resolution requires one exact reported civil time",
        )
    civil_datetime = datetime.combine(
        input.birth_date.value,
        input.birth_time.start,
    ).isoformat(timespec="seconds")
    return resolve_calendar(
        civil_datetime,
        location.timezone,
        utc_offset_hint=utc_offset_hint,
    )
