"""Envelope for intermediate payloads passed to shared DataMappers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from middleware.payload.kinds import PayloadKind


@dataclass(frozen=True)
class ParsedPayload:
    """Typed intermediate payload ready for mapping.

    Producers emit this envelope (or an equivalent exposing the same fields)
    before invoking the shared DataMapper API.
    """

    kind: PayloadKind
    value: Any
    identifier: str

    def __post_init__(self) -> None:
        """Reject empty or whitespace-only identifiers."""
        if not self.identifier or not str(self.identifier).strip():
            raise ValueError("ParsedPayload.identifier must be a non-empty stable id")
