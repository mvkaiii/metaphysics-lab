from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Callable, Dict, Optional

from engine.birth.reconciliation import ConflictSeverity, ReconciliationStatus

from .errors import NatalFoundationError
from .models import ExternalNatalView, ProjectNatalView, ResolvedField, ResolvedNatalView, SourcedValue


EquivalentCallback = Callable[[Any, Any], bool]

_BLOCKING_EXACT = frozenset((
    "bazi.pillars.year",
    "bazi.pillars.month",
    "bazi.pillars.day",
    "bazi.pillars.hour",
    "birth.effective_hour_branch",
    "ziwei.ming_palace",
    "ziwei.body_palace",
    "ziwei.five_element_bureau",
    "bazi.decadal_direction",
))


def _invalid(message: str, details: Optional[Dict[str, Any]] = None) -> NatalFoundationError:
    return NatalFoundationError("invalid_natal_reconciliation", message, details or {})


def _is_blocking_path(path: str) -> bool:
    if path in _BLOCKING_EXACT:
        return True
    if path.startswith("ziwei.major_stars.") and path.endswith(".palace"):
        return True
    if path.startswith("ziwei.transformation_required_stars.") and path.endswith(".palace"):
        return True
    if path.startswith("ziwei.birth_transformations."):
        return True
    if path.startswith("ziwei.decadal_cycles.") and path.endswith(".palace"):
        return True
    return False


def _severity_for(path: str, status: str) -> str:
    if status != ReconciliationStatus.CONFLICT.value:
        return ConflictSeverity.INFO.value
    if _is_blocking_path(path):
        return ConflictSeverity.BLOCKING.value
    return ConflictSeverity.CAUTION.value


def compare_scalar(
    path: str,
    external: Optional[SourcedValue[Any]],
    project: Optional[SourcedValue[Any]],
    *,
    equivalent: Optional[EquivalentCallback] = None,
) -> ResolvedField:
    if not isinstance(path, str) or not path.strip():
        raise _invalid("path must be a non-empty string")
    if external is not None and not isinstance(external, SourcedValue):
        raise _invalid("external must be SourcedValue or None", {"path": path})
    if project is not None and not isinstance(project, SourcedValue):
        raise _invalid("project must be SourcedValue or None", {"path": path})

    if external is None and project is None:
        return ResolvedField(
            path=path,
            status=ReconciliationStatus.NOT_COMPARABLE.value,
            severity=ConflictSeverity.INFO.value,
            selected_source="none",
            selected_value=None,
            external_value=None,
            project_value=None,
            reason="both_missing",
        )
    if external is None:
        return ResolvedField(
            path=path,
            status=ReconciliationStatus.NOT_COMPARABLE.value,
            severity=ConflictSeverity.INFO.value,
            selected_source="project",
            selected_value=project.value,
            external_value=None,
            project_value=project,
            reason="external_missing",
        )
    if project is None:
        return ResolvedField(
            path=path,
            status=ReconciliationStatus.NOT_COMPARABLE.value,
            severity=ConflictSeverity.INFO.value,
            selected_source="external",
            selected_value=external.value,
            external_value=external,
            project_value=None,
            reason="project_missing",
        )

    if external.value == project.value:
        return ResolvedField(
            path=path,
            status=ReconciliationStatus.MATCH.value,
            severity=ConflictSeverity.INFO.value,
            selected_source="external",
            selected_value=external.value,
            external_value=external,
            project_value=project,
            reason="matched",
        )

    if equivalent is not None:
        try:
            is_equivalent = bool(equivalent(external.value, project.value))
        except Exception as exc:
            raise _invalid(
                "equivalence callback failed",
                {"path": path, "error_type": type(exc).__name__},
            ) from exc
        if is_equivalent:
            return ResolvedField(
                path=path,
                status=ReconciliationStatus.EQUIVALENT.value,
                severity=ConflictSeverity.INFO.value,
                selected_source="external",
                selected_value=external.value,
                external_value=external,
                project_value=project,
                reason="materially_equivalent",
            )

    status = ReconciliationStatus.CONFLICT.value
    return ResolvedField(
        path=path,
        status=status,
        severity=_severity_for(path, status),
        selected_source="none",
        selected_value=None,
        external_value=external,
        project_value=project,
        reason="value_conflict",
    )


def _flatten_generic(prefix: str, value: Any, target: Dict[str, Any]) -> None:
    if isinstance(value, Mapping):
        for key in sorted(value.keys(), key=str):
            child = "%s.%s" % (prefix, key) if prefix else str(key)
            _flatten_generic(child, value[key], target)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, item in enumerate(value):
            child = "%s.%d" % (prefix, index)
            _flatten_generic(child, item, target)
        return
    target[prefix] = value


def _flatten_identity_records(
    prefix: str,
    records: Any,
    identity_key: str,
    target: Dict[str, Any],
) -> None:
    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
        _flatten_generic(prefix, records, target)
        return
    for record in records:
        if not isinstance(record, Mapping) or identity_key not in record:
            _flatten_generic(prefix, records, target)
            return
    identities = [str(record[identity_key]) for record in records]
    if len(set(identities)) != len(identities):
        raise _invalid("duplicate record identities during reconciliation", {"path": prefix})
    for record in sorted(records, key=lambda item: str(item[identity_key])):
        identity = str(record[identity_key])
        for key in sorted(record.keys(), key=str):
            if key == identity_key:
                continue
            _flatten_generic("%s.%s.%s" % (prefix, identity, key), record[key], target)


def _flatten_ziwei(ziwei: Mapping[str, Any]) -> Dict[str, Any]:
    flattened: Dict[str, Any] = {}
    for key in sorted(ziwei.keys(), key=str):
        value = ziwei[key]
        prefix = "ziwei.%s" % key
        if key == "stars":
            _flatten_identity_records(prefix, value, "star", flattened)
        elif key == "palaces":
            _flatten_identity_records(prefix, value, "name", flattened)
        elif key == "decadal_cycles":
            _flatten_identity_records(prefix, value, "index", flattened)
        elif key in ("major_stars", "transformation_required_stars"):
            _flatten_identity_records(prefix, value, "star", flattened)
        else:
            _flatten_generic(prefix, value, flattened)
    return flattened


def _external_fields(view: ExternalNatalView) -> Dict[str, SourcedValue[Any]]:
    raw: Dict[str, Any] = {}
    _flatten_generic("birth", view.birth, raw)
    _flatten_generic("bazi", view.bazi, raw)
    raw.update(_flatten_ziwei(view.ziwei))
    return {path: SourcedValue(value, view.source) for path, value in raw.items()}


def _project_fields(view: ProjectNatalView) -> Dict[str, SourcedValue[Any]]:
    raw: Dict[str, Any] = {}
    _flatten_generic("birth", view.birth, raw)
    time_raw: Dict[str, Any] = {}
    _flatten_generic("birth", view.time_basis, time_raw)
    raw.update(time_raw)
    _flatten_generic("bazi", view.bazi, raw)
    raw.update(_flatten_ziwei(view.ziwei))
    return {path: SourcedValue(value, view.source) for path, value in raw.items()}


def reconcile_natal(
    external: Optional[ExternalNatalView],
    project: Optional[ProjectNatalView],
    *,
    project_maturity: str,
) -> ResolvedNatalView:
    if external is not None and not isinstance(external, ExternalNatalView):
        raise _invalid("external must be ExternalNatalView or None")
    if project is not None and not isinstance(project, ProjectNatalView):
        raise _invalid("project must be ProjectNatalView or None")
    if not isinstance(project_maturity, str) or not project_maturity.strip():
        raise _invalid("project_maturity must be a non-empty string")

    external_fields = {} if external is None else _external_fields(external)
    project_fields = {} if project is None else _project_fields(project)
    paths = sorted(set(external_fields) | set(project_fields))
    fields = tuple(
        compare_scalar(path, external_fields.get(path), project_fields.get(path))
        for path in paths
    )
    return ResolvedNatalView(fields)
