from __future__ import annotations

from typing import Any, Mapping, Optional


class ZiweiPhase2AError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.code = code
        self.details = dict(details or {})
        super().__init__(message)


class ZiweiFineCycleError(ValueError):
    def __init__(self, code, message, details=None):
        self.code = code
        self.details = dict(details or {})
        super().__init__(message)
