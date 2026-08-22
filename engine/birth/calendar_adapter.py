from __future__ import annotations

from datetime import datetime

from engine.calendar import CalendarResolution, resolve_calendar

from .errors import BirthFoundationError
from .models import BirthInput, ResolvedBirthPlace


def resolve_birth_calendar(
    input: BirthInput,
    location: ResolvedBirthPlace,
) -> CalendarResolution:
    if not input.birth_time.is_exact:
        raise BirthFoundationError(
            "ambiguous_birth_time",
            "birth calendar resolution requires one exact reported civil time",
        )
    civil_datetime = datetime.combine(
        input.birth_date.value,
        input.birth_time.start,
    ).isoformat(timespec="seconds")
    return resolve_calendar(civil_datetime, location.timezone)
