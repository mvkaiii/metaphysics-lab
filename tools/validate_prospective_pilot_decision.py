"""Validate the public prospective-pilot human decision receipt."""

from __future__ import annotations

from typing import Any, Mapping


def validate_decision_receipt(receipt: Mapping[str, Any]) -> list[str]:
    raise NotImplementedError("TDD RED: decision receipt validator not implemented")


def pilot_start_allowed(receipt: Mapping[str, Any]) -> bool:
    raise NotImplementedError("TDD RED: pilot start gate not implemented")
