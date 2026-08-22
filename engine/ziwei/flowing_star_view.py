from __future__ import annotations

from typing import Iterable, Optional, Sequence, Tuple

from engine.calendar.sexagenary import ZHI

from .errors import ZiweiFlowingStarError
from .flowing_star_models import (
    FlowingStarLayer,
    FlowingStarMaterializedRecord,
    ScopePalaceMapping,
    ZiweiDynamicCycleView,
)
from .models import CycleTransformationLayer
from .natal_models import ZiweiPalaceRecord


_SCOPE_PREFIX = {
    "decadal": "運",
    "yearly": "流",
    "monthly": "月",
    "daily": "日",
    "hourly": "時",
}

_DISPLAY_SUFFIX = {
    "天魁": "魁",
    "天鉞": "鉞",
    "文昌": "昌",
    "文曲": "曲",
    "祿存": "祿",
    "擎羊": "羊",
    "陀羅": "陀",
    "天馬": "馬",
    "紅鸞": "鸞",
    "天喜": "喜",
    "年解": "年解",
}


def _raise(code, message, details=None):
    raise ZiweiFlowingStarError(code, message, details)


def _display_name(scope: str, star: str) -> str:
    if star == "年解":
        return "年解"
    try:
        return _SCOPE_PREFIX[scope] + _DISPLAY_SUFFIX[star]
    except KeyError:
        _raise(
            "flowing_star_materialization_mismatch",
            "unsupported flowing-star display identity",
            {"scope": scope, "star": star},
        )
    raise AssertionError("unreachable")


def _natal_palace_index(palaces: Sequence[ZiweiPalaceRecord]):
    items = tuple(palaces)
    if len(items) != 12 or any(not isinstance(item, ZiweiPalaceRecord) for item in items):
        _raise(
            "flowing_star_materialization_mismatch",
            "natal materialization requires twelve ZiweiPalaceRecord items",
            {"count": len(items)},
        )
    branches = tuple(item.branch for item in items)
    if len(set(branches)) != 12 or set(branches) != set(ZHI):
        _raise(
            "flowing_star_materialization_mismatch",
            "natal materialization requires all twelve unique branches",
            {"branches": branches},
        )
    return {item.branch: item.name for item in items}


def _validate_scope_mapping(layer: FlowingStarLayer, mapping: ScopePalaceMapping) -> None:
    mismatches = {}
    expected = {
        "chart_id": layer.identity.chart_id,
        "scope": layer.identity.scope,
        "reference": layer.identity.reference,
    }
    actual = {
        "chart_id": mapping.chart_id,
        "scope": mapping.scope,
        "reference": mapping.reference,
    }
    for field in ("chart_id", "scope", "reference"):
        if expected[field] != actual[field]:
            mismatches[field] = {"expected": expected[field], "actual": actual[field]}
    if mismatches:
        _raise(
            "flowing_star_materialization_mismatch",
            "scope palace mapping identity does not match flowing-star layer",
            {"mismatches": mismatches},
        )


def materialize_flowing_star_layer(
    layer: FlowingStarLayer,
    natal_palaces: Sequence[ZiweiPalaceRecord],
    scope_mapping: Optional[ScopePalaceMapping] = None,
) -> Tuple[FlowingStarMaterializedRecord, ...]:
    if not isinstance(layer, FlowingStarLayer):
        _raise(
            "flowing_star_materialization_mismatch",
            "materialization requires FlowingStarLayer",
        )
    natal_by_branch = _natal_palace_index(natal_palaces)

    if scope_mapping is not None:
        if not isinstance(scope_mapping, ScopePalaceMapping):
            _raise(
                "flowing_star_materialization_mismatch",
                "scope_mapping must be ScopePalaceMapping",
            )
        _validate_scope_mapping(layer, scope_mapping)

    records = []
    for placement in layer.placements:
        target = placement.target_branch
        records.append(
            FlowingStarMaterializedRecord(
                base_star=placement.base_star,
                display_name=_display_name(layer.identity.scope, placement.base_star),
                target_branch=target,
                natal_palace=natal_by_branch[target],
                scope_palace=None if scope_mapping is None else scope_mapping.palaces[target],
                scope=layer.identity.scope,
                source_reference=layer.identity.reference,
            )
        )
    return tuple(records)


def join_dynamic_cycle(
    transformation_layer: Optional[CycleTransformationLayer],
    flowing_star_layer: FlowingStarLayer,
    materialized_records: Iterable[FlowingStarMaterializedRecord] = (),
) -> ZiweiDynamicCycleView:
    if not isinstance(flowing_star_layer, FlowingStarLayer):
        _raise(
            "flowing_star_materialization_mismatch",
            "dynamic join requires FlowingStarLayer",
        )

    if transformation_layer is not None:
        if not isinstance(transformation_layer, CycleTransformationLayer):
            _raise(
                "flowing_star_materialization_mismatch",
                "transformation_layer has invalid type",
            )
        transform_key = (
            transformation_layer.identity.chart_id,
            transformation_layer.identity.scope,
            transformation_layer.identity.reference,
        )
        flowing_key = (
            flowing_star_layer.identity.chart_id,
            flowing_star_layer.identity.scope,
            flowing_star_layer.identity.reference,
        )
        if transform_key != flowing_key:
            labels = ("chart_id", "scope", "reference")
            mismatches = {}
            for index, field in enumerate(labels):
                if transform_key[index] != flowing_key[index]:
                    mismatches[field] = {
                        "transformation": transform_key[index],
                        "flowing_star": flowing_key[index],
                    }
            _raise(
                "flowing_star_materialization_mismatch",
                "dynamic cycle join key mismatch",
                {"mismatches": mismatches},
            )

    records = tuple(materialized_records)
    if any(not isinstance(item, FlowingStarMaterializedRecord) for item in records):
        _raise(
            "flowing_star_materialization_mismatch",
            "dynamic cycle materialized_records contain invalid type",
        )
    for record in records:
        if (
            record.scope != flowing_star_layer.identity.scope
            or record.source_reference != flowing_star_layer.identity.reference
        ):
            _raise(
                "flowing_star_materialization_mismatch",
                "materialized record identity does not match flowing-star layer",
                {
                    "record_scope": record.scope,
                    "record_reference": record.source_reference,
                },
            )

    return ZiweiDynamicCycleView(
        transformation_layer=transformation_layer,
        flowing_star_layer=flowing_star_layer,
        materialized_records=records,
    )
