"""Structured errors for the portable distribution runtime."""

from __future__ import annotations

from typing import Any, Mapping, Optional


class DistributionError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.code = code
        self.details = dict(details or {})
        super().__init__(message)
