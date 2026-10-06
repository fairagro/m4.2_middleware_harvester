"""Harvested ARC transfer object shared by mappers and the orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from middleware.payload.arc_comments import drop_date_modified_comment_node, unique_comment_names

if TYPE_CHECKING:
    from arctrl import ARC  # type: ignore[import-untyped]


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
        """Serialize an arctrl ``ARC`` and capture identifier plus composition counts.

        Comment names are made unique first (``arc_comments``): ARCtrl cannot write an ARC
        with repeated Comment names, and the API writes every harvested ARC.
        """
        unique_comment_names(arc)
        identifier = getattr(arc, "Identifier", None)
        return cls(
            arc_json=drop_date_modified_comment_node(str(arc.ToROCrateJsonString())),
            source_url=source_url,
            identifier=str(identifier) if identifier else None,
            studies=int(arc.StudyCount),
            assays=int(arc.AssayCount),
        )
