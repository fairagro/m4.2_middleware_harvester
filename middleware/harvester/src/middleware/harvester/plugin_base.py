"""Plugin interface for all harvester plugins."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from middleware.harvester.errors import HarvesterError, SkippedRecord

if TYPE_CHECKING:
    from arctrl import ARC


@dataclass(frozen=True)
class HarvestedArc:
    """One successfully mapped ARC ready for upload and reporting."""

    arc_json: str
    source_url: str | None = None
    identifier: str | None = None
    studies: int = 0
    assays: int = 0

    @classmethod
    def from_arctrl(cls, arc: ARC, *, source_url: str | None = None) -> HarvestedArc:
        """Serialize an arctrl ``ARC`` and capture identifier plus composition counts."""
        identifier = getattr(arc, "Identifier", None)
        return cls(
            arc_json=str(arc.ToROCrateJsonString()),
            source_url=source_url,
            identifier=str(identifier) if identifier else None,
            studies=int(arc.StudyCount),
            assays=int(arc.AssayCount),
        )


class Plugin(Protocol):
    """Protocol defining the harvester plugin interface."""

    def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None]:
        """Run the plugin and yield harvested ARCs, errors, or skips."""
        raise NotImplementedError

    async def get_expected_datasets(self) -> int | None:
        """Return the expected dataset count for the configured source."""
        raise NotImplementedError
