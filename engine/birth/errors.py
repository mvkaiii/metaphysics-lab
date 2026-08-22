from __future__ import annotations

from typing import Optional


class BirthFoundationError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[dict] = None,
    ) -> None:
        self.code = code
        self.details = details or {}
        super().__init__(message)
