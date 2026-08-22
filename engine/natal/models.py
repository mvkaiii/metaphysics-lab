from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Generic, Mapping, Optional, Tuple, TypeVar

from .errors import NatalFoundationError


T = TypeVar("T")

_ALLOWED_STATUSES = frozenset(("MATCH", "EQUIVALENT", "CONFLICT", "NOT_COMPARABLE"))
_ALLOWED_SEVERITIES = frozenset(("INFO", "CAUTION", "BLOCKING"))
_ALLOWED_SELECTED_SOURCES = frozenset(("external", "project", "none"))


def _invalid(message: str, details: Optional[Mapping[str, Any]] = None) -> NatalFoundationError:
    return NatalFoundationError("invalid_natal_model", message, details)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


def _serialize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_serialize(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [_serialize(item) for item in sorted(value, key=repr)]
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _serialize(to_dict())
    return value


def _require_text(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise _invalid("%s must be a non-empty string" % field_name, {"field": field_name})


@dataclass(frozen=True)
class NatalSource:
    source_type: str
    source_name: str
    source_version: str
    rule_profile: str
    rule_version: str
    maturity: str
    validation_status: str

    def __post_init__(self) -> None:
        for field_name in (
            "source_type",
            "source_name",
            "source_version",
            "rule_profile",
            "rule_version",
            "maturity",
            "validation_status",
        ):
            _require_text(field_name, getattr(self, field_name))

    def to_dict(self) -> dict:
        return {
            "source_type": self.source_type,
            "source_name": self.source_name,
            "source_version": self.source_version,
            "rule_profile": self.rule_profile,
            "rule_version": self.rule_version,
            "maturity": self.maturity,
            "validation_status": self.validation_status,
        }


@dataclass(frozen=True)
class SourcedValue(Generic[T]):
    value: T
    source: NatalSource
    notes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source, NatalSource):
            raise _invalid("source must be NatalSource")
        notes = tuple(self.notes)
        if any(not isinstance(note, str) or not note.strip() for note in notes):
            raise _invalid("notes must contain non-empty strings")
        object.__setattr__(self, "value", _freeze(self.value))
        object.__setattr__(self, "notes", notes)

    def to_dict(self) -> dict:
        return {
            "value": _serialize(self.value),
            "source": self.source.to_dict(),
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ExternalNatalView:
    birth: Mapping[str, Any]
    bazi: Mapping[str, Any]
    ziwei: Mapping[str, Any]
    source: NatalSource

    def __post_init__(self) -> None:
        if not isinstance(self.source, NatalSource):
            raise _invalid("source must be NatalSource")
        for field_name in ("birth", "bazi", "ziwei"):
            value = getattr(self, field_name)
            if not isinstance(value, Mapping):
                raise _invalid("%s must be a mapping" % field_name, {"field": field_name})
            object.__setattr__(self, field_name, _freeze(value))

    def to_dict(self) -> dict:
        return {
            "birth": _serialize(self.birth),
            "bazi": _serialize(self.bazi),
            "ziwei": _serialize(self.ziwei),
            "source": self.source.to_dict(),
        }


@dataclass(frozen=True)
class ProjectNatalView:
    birth: Mapping[str, Any]
    time_basis: Mapping[str, Any]
    bazi: Mapping[str, Any]
    ziwei: Mapping[str, Any]
    source: NatalSource

    def __post_init__(self) -> None:
        if not isinstance(self.source, NatalSource):
            raise _invalid("source must be NatalSource")
        for field_name in ("birth", "time_basis", "bazi", "ziwei"):
            value = getattr(self, field_name)
            if not isinstance(value, Mapping):
                raise _invalid("%s must be a mapping" % field_name, {"field": field_name})
            object.__setattr__(self, field_name, _freeze(value))

    def to_dict(self) -> dict:
        return {
            "birth": _serialize(self.birth),
            "time_basis": _serialize(self.time_basis),
            "bazi": _serialize(self.bazi),
            "ziwei": _serialize(self.ziwei),
            "source": self.source.to_dict(),
        }


@dataclass(frozen=True)
class ResolvedField:
    path: str
    status: str
    severity: str
    selected_source: str
    selected_value: Any
    external_value: Optional[SourcedValue[Any]]
    project_value: Optional[SourcedValue[Any]]
    reason: str

    def __post_init__(self) -> None:
        _require_text("path", self.path)
        _require_text("reason", self.reason)
        if self.status not in _ALLOWED_STATUSES:
            raise _invalid("unknown reconciliation status", {"status": self.status})
        if self.severity not in _ALLOWED_SEVERITIES:
            raise _invalid("unknown conflict severity", {"severity": self.severity})
        if self.selected_source not in _ALLOWED_SELECTED_SOURCES:
            raise _invalid("unknown selected source", {"selected_source": self.selected_source})
        if self.external_value is not None and not isinstance(self.external_value, SourcedValue):
            raise _invalid("external_value must be SourcedValue or None")
        if self.project_value is not None and not isinstance(self.project_value, SourcedValue):
            raise _invalid("project_value must be SourcedValue or None")

        selected = None
        if self.selected_source == "external":
            if self.external_value is None:
                raise _invalid("selected external source requires external_value")
            selected = self.external_value.value
        elif self.selected_source == "project":
            if self.project_value is None:
                raise _invalid("selected project source requires project_value")
            selected = self.project_value.value
        elif self.selected_value is not None:
            raise _invalid("selected_source none requires selected_value None")

        if self.selected_source != "none" and _serialize(self.selected_value) != _serialize(selected):
            raise _invalid(
                "selected_value must match selected source value",
                {"selected_source": self.selected_source},
            )
        object.__setattr__(self, "selected_value", _freeze(self.selected_value))

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "status": self.status,
            "severity": self.severity,
            "selected_source": self.selected_source,
            "selected_value": _serialize(self.selected_value),
            "external_value": None if self.external_value is None else self.external_value.to_dict(),
            "project_value": None if self.project_value is None else self.project_value.to_dict(),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ResolvedNatalView:
    fields: Tuple[ResolvedField, ...]

    def __post_init__(self) -> None:
        fields = tuple(self.fields)
        if any(not isinstance(field, ResolvedField) for field in fields):
            raise _invalid("resolved fields must contain ResolvedField values")
        paths = tuple(field.path for field in fields)
        if len(set(paths)) != len(paths):
            raise _invalid("resolved field paths must be unique")
        object.__setattr__(self, "fields", fields)

    def to_dict(self) -> dict:
        return {"fields": [field.to_dict() for field in self.fields]}


@dataclass(frozen=True)
class NormalizedNatalChart:
    identity: str
    external: Optional[ExternalNatalView]
    project: Optional[ProjectNatalView]
    resolved: ResolvedNatalView
    validation: Mapping[str, Any]
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        _require_text("identity", self.identity)
        if self.external is not None and not isinstance(self.external, ExternalNatalView):
            raise _invalid("external must be ExternalNatalView or None")
        if self.project is not None and not isinstance(self.project, ProjectNatalView):
            raise _invalid("project must be ProjectNatalView or None")
        if not isinstance(self.resolved, ResolvedNatalView):
            raise _invalid("resolved must be ResolvedNatalView")
        if not isinstance(self.validation, Mapping):
            raise _invalid("validation must be a mapping")
        if not isinstance(self.provenance, Mapping):
            raise _invalid("provenance must be a mapping")
        object.__setattr__(self, "validation", _freeze(self.validation))
        object.__setattr__(self, "provenance", _freeze(self.provenance))

    def to_dict(self) -> dict:
        return {
            "identity": self.identity,
            "external": None if self.external is None else self.external.to_dict(),
            "project": None if self.project is None else self.project.to_dict(),
            "resolved": self.resolved.to_dict(),
            "validation": _serialize(self.validation),
            "provenance": _serialize(self.provenance),
        }
