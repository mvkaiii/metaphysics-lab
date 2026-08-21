from __future__ import annotations

from .lunar import (
    LunarCalendarProvider,
    LunarProviderFailure,
    LunarProviderUnsupportedDate,
    LunarPythonProvider,
    calendar_validation_for,
)
from .models import (
    CalendarContext,
    CalendarInput,
    CalendarPolicies,
    CalendarResolution,
    CalendarResolverException,
    ProviderBundle,
    ResolverError,
    ValidationCheck,
    ValidationMetadata,
    combine_validation_status,
)
from .timezone import (
    PinnedTzdataProvider,
    TIMEZONE_PROFILE,
    normalize_local_time,
)

SCHEMA_VERSION = "1.0"
RESOLVER_VERSION = "1.0.0"


def resolve_calendar(
    civil_datetime: str,
    timezone_name: str,
    utc_offset_hint: str | None = None,
    *,
    lunar_provider: LunarCalendarProvider | None = None,
    timezone_provider: PinnedTzdataProvider | None = None,
) -> CalendarResolution:
    try:
        active_timezone_provider = (
            timezone_provider if timezone_provider is not None else PinnedTzdataProvider()
        )
        normalized = normalize_local_time(
            civil_datetime,
            timezone_name,
            utc_offset_hint,
            provider=active_timezone_provider,
        )
        active_lunar_provider = (
            lunar_provider if lunar_provider is not None else LunarPythonProvider()
        )
        lunar = active_lunar_provider.convert(normalized.gregorian_date)
        calendar_validation = calendar_validation_for(normalized.gregorian_date)
        timezone_validation = ValidationCheck("validated", TIMEZONE_PROFILE)
        overall_status = combine_validation_status(
            calendar_validation.check.status,
            timezone_validation.status,
        )
        context = CalendarContext(
            schema_version=SCHEMA_VERSION,
            resolver_version=RESOLVER_VERSION,
            input=CalendarInput(
                civil_datetime=civil_datetime,
                timezone=timezone_name,
                utc_offset_hint=utc_offset_hint,
            ),
            normalized_time=normalized,
            lunar=lunar,
            providers=ProviderBundle(
                lunar_calendar=active_lunar_provider.metadata,
                timezone_database=active_timezone_provider.metadata,
            ),
            validation=ValidationMetadata(
                calendar_conversion=calendar_validation.check,
                timezone_normalization=timezone_validation,
                overall_status=overall_status,
                validated_range=calendar_validation.validated_range,
                boundary_id=calendar_validation.boundary_id,
                notes=calendar_validation.notes,
            ),
            policies=CalendarPolicies(
                timezone_basis="IANA legal local civil time",
                lunar_date_boundary="local civil midnight (00:00)",
                hour_branch_basis="local civil clock; 子=23:00-00:59",
                metaphysics_day_boundary_applied=False,
            ),
        )
        return CalendarResolution.success(context)
    except CalendarResolverException as exc:
        return CalendarResolution.failure(exc.error)
    except LunarProviderUnsupportedDate as exc:
        return CalendarResolution.failure(
            ResolverError(
                "provider_unsupported_date",
                "lunar calendar provider does not support the requested date",
                {"civil_datetime": civil_datetime, "reason": str(exc)},
            )
        )
    except LunarProviderFailure as exc:
        return CalendarResolution.failure(
            ResolverError(
                "provider_failure",
                "lunar calendar provider failed",
                {"civil_datetime": civil_datetime, "reason": str(exc)},
            )
        )
