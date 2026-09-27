"""Validate Pilot-2's fail-closed pre-candidate sequencing gate."""

from __future__ import annotations

from typing import Any, Mapping


def validate_pilot2_pre_candidate_gate(payload: Mapping[str, Any]) -> list[str]:
    raise NotImplementedError("TDD RED: Pilot-2 pre-candidate gate not implemented")


def candidate_case_processing_allowed(payload: Mapping[str, Any]) -> bool:
    raise NotImplementedError("TDD RED: Pilot-2 pre-candidate gate not implemented")
