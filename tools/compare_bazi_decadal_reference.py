"""Compare a sealed independent Bazi decadal reference packet with engine-view data.

The module intentionally does not calculate metaphysics values or create oracle
expected values.  Task 3 remains NEEDS_EVIDENCE until an independent oracle
packet is supplied and reviewed.
"""

from __future__ import annotations

from typing import Any, Mapping


def validate_reference_packet(packet: Mapping[str, Any]) -> list[str]:
    raise NotImplementedError("TDD RED: reference packet validator not implemented")


def compare_reference_packet(
    reference: Mapping[str, Any],
    actual_bundle: Mapping[str, Any],
) -> dict:
    raise NotImplementedError("TDD RED: reference comparator not implemented")
