from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from engine.calendar.models import (
    CalendarContext,
    CalendarInput,
    CalendarPolicies,
    LunarDate,
    LunarProviderMetadata,
    NormalizedTime,
    ProviderBundle,
    TimezoneProviderMetadata,
    ValidationCheck,
    ValidationMetadata,
)
from tests.ziwei_phase2a_fixtures import (
    CHART,
    PROVENANCE,
    SYNTHETIC_PALACE_STEM_RECORDS,
    SYNTHETIC_STAR_RECORDS,
)


def calendar_context(
    gregorian_date=date(2023, 7, 30),
    local_hour=1,
    local_minute=30,
    hour_branch="丑",
    lunar_year=2023,
    lunar_month=6,
    lunar_day=13,
    is_leap_month=False,
    calendar_status="validated",
    metaphysics_day_boundary_applied=False,
    timezone_name="Asia/Taipei",
):
    zone = ZoneInfo(timezone_name)
    local = datetime(
        gregorian_date.year,
        gregorian_date.month,
        gregorian_date.day,
        local_hour,
        local_minute,
        tzinfo=zone,
    )
    offset = local.strftime("%z")
    offset = offset[:3] + ":" + offset[3:]
    providers = ProviderBundle(
        LunarProviderMetadata("lunar-python", "1.4.8", "000c8a3"),
        TimezoneProviderMetadata("zoneinfo", "stdlib", "2026.3", "python-stdlib"),
    )
    calendar_check = ValidationCheck(calendar_status, "calendar-v1")
    timezone_check = ValidationCheck("validated", "iana-tz-v1")
    validation = ValidationMetadata(
        calendar_check,
        timezone_check,
        calendar_status,
        "1900-2100",
        "fixture-boundary" if calendar_status == "boundary_conflict" else None,
        (),
    )
    return CalendarContext(
        "1.0",
        "1.0",
        CalendarInput(local.strftime("%Y-%m-%dT%H:%M:%S"), timezone_name),
        NormalizedTime(
            local,
            local.astimezone(timezone.utc),
            offset,
            gregorian_date,
            timezone_name,
            hour_branch,
        ),
        LunarDate(lunar_year, lunar_month, lunar_day, is_leap_month),
        providers,
        validation,
        CalendarPolicies(
            "IANA timezone",
            "civil midnight",
            "local civil hour",
            metaphysics_day_boundary_applied,
        ),
    )
