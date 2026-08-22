from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Dict

from engine.bazi.calendar import GAN, ZHI

from .errors import NatalFoundationError
from .models import ExternalNatalView, NatalSource


_PILLAR_NAMES = ("year", "month", "day", "hour")


def _schema_error(message: str, details: Dict[str, Any] | None = None) -> NatalFoundationError:
    return NatalFoundationError("invalid_natal_schema", message, details or {})


def _require_mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise _schema_error("%s must be a mapping" % path, {"path": path})
    return value


def _require_text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _schema_error("%s must be a non-empty string" % path, {"path": path})
    return value


def _require_records(value: Any, path: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise _schema_error("%s must be a sequence of records" % path, {"path": path})
    return value


def _validate_birth(birth: Mapping[str, Any]) -> None:
    if "reported_datetime" in birth:
        _require_text(birth["reported_datetime"], "birth.reported_datetime")
    if "place_label" in birth:
        _require_text(birth["place_label"], "birth.place_label")


def _validate_pillar(value: Any, path: str) -> None:
    text = _require_text(value, path)
    if len(text) != 2 or text[0] not in GAN or text[1] not in ZHI:
        raise _schema_error("%s must be one valid stem-branch pair" % path, {"path": path, "value": text})


def _validate_bazi(bazi: Mapping[str, Any]) -> None:
    if "pillars" not in bazi:
        return
    pillars = _require_mapping(bazi["pillars"], "bazi.pillars")
    if set(pillars.keys()) != set(_PILLAR_NAMES):
        raise _schema_error(
            "bazi.pillars must contain exactly year/month/day/hour when provided",
            {"path": "bazi.pillars", "keys": sorted(str(key) for key in pillars.keys())},
        )
    for name in _PILLAR_NAMES:
        _validate_pillar(pillars[name], "bazi.pillars.%s" % name)


def _validate_palaces(value: Any) -> None:
    records = _require_records(value, "ziwei.palaces")
    names = []
    for index, raw in enumerate(records):
        path = "ziwei.palaces[%d]" % index
        record = _require_mapping(raw, path)
        name = _require_text(record.get("name"), path + ".name")
        names.append(name)
        if "branch" in record:
            branch = _require_text(record["branch"], path + ".branch")
            if branch not in ZHI:
                raise _schema_error("invalid earthly branch", {"path": path + ".branch", "value": branch})
        if "heavenly_stem" in record:
            stem = _require_text(record["heavenly_stem"], path + ".heavenly_stem")
            if stem not in GAN:
                raise _schema_error("invalid heavenly stem", {"path": path + ".heavenly_stem", "value": stem})
    if len(set(names)) != len(names):
        raise _schema_error("ziwei.palaces contains duplicate palace names", {"path": "ziwei.palaces"})


def _validate_stars(value: Any) -> None:
    records = _require_records(value, "ziwei.stars")
    identities = []
    for index, raw in enumerate(records):
        path = "ziwei.stars[%d]" % index
        record = _require_mapping(raw, path)
        star = _require_text(record.get("star"), path + ".star")
        identities.append(star)
        if "palace" in record:
            _require_text(record["palace"], path + ".palace")
        if "brightness" in record and record["brightness"] is not None:
            _require_text(record["brightness"], path + ".brightness")
    if len(set(identities)) != len(identities):
        raise _schema_error("ziwei.stars contains duplicate star identities", {"path": "ziwei.stars"})


def _validate_transformations(value: Any) -> None:
    transformations = _require_mapping(value, "ziwei.birth_transformations")
    allowed = {"祿", "權", "科", "忌"}
    unknown = set(transformations.keys()) - allowed
    if unknown:
        raise _schema_error(
            "ziwei.birth_transformations contains unknown transformation types",
            {"path": "ziwei.birth_transformations", "unknown": sorted(str(item) for item in unknown)},
        )
    for key, star in transformations.items():
        _require_text(star, "ziwei.birth_transformations.%s" % key)


def _validate_decadal_cycles(value: Any) -> None:
    records = _require_records(value, "ziwei.decadal_cycles")
    seen = set()
    for index, raw in enumerate(records):
        path = "ziwei.decadal_cycles[%d]" % index
        record = _require_mapping(raw, path)
        cycle_index = record.get("index")
        if not isinstance(cycle_index, int) or isinstance(cycle_index, bool) or cycle_index < 1:
            raise _schema_error("decadal cycle index must be a positive integer", {"path": path + ".index"})
        if cycle_index in seen:
            raise _schema_error("duplicate decadal cycle index", {"path": path + ".index", "index": cycle_index})
        seen.add(cycle_index)
        if "palace" in record:
            _require_text(record["palace"], path + ".palace")
        for age_key in ("start_age", "end_age"):
            if age_key in record:
                age = record[age_key]
                if not isinstance(age, (int, float)) or isinstance(age, bool) or age < 0:
                    raise _schema_error("%s must be a non-negative number" % (path + "." + age_key))
        if "start_age" in record and "end_age" in record and record["end_age"] < record["start_age"]:
            raise _schema_error("decadal cycle end_age must not precede start_age", {"path": path})


def _validate_ziwei(ziwei: Mapping[str, Any]) -> None:
    for key in ("ming_palace", "body_palace", "five_element_bureau"):
        if key in ziwei:
            _require_text(ziwei[key], "ziwei.%s" % key)
    if "palaces" in ziwei:
        _validate_palaces(ziwei["palaces"])
    if "stars" in ziwei:
        _validate_stars(ziwei["stars"])
    if "birth_transformations" in ziwei:
        _validate_transformations(ziwei["birth_transformations"])
    if "decadal_cycles" in ziwei:
        _validate_decadal_cycles(ziwei["decadal_cycles"])


def import_external_natal(payload: Mapping[str, object], source: NatalSource) -> ExternalNatalView:
    """Validate and freeze an already-structured external natal payload.

    PDF, image, OCR, Markdown, and natural-language extraction are intentionally
    upstream concerns. This function never synthesizes missing chart fields.
    """

    if not isinstance(source, NatalSource) or source.source_type != "external":
        raise _schema_error(
            "external natal import requires source_type=external",
            {"source_type": getattr(source, "source_type", None)},
        )
    root = _require_mapping(payload, "payload")

    birth = _require_mapping(root.get("birth", {}), "birth")
    bazi = _require_mapping(root.get("bazi", {}), "bazi")
    ziwei = _require_mapping(root.get("ziwei", {}), "ziwei")

    _validate_birth(birth)
    _validate_bazi(bazi)
    _validate_ziwei(ziwei)

    return ExternalNatalView(birth=birth, bazi=bazi, ziwei=ziwei, source=source)
