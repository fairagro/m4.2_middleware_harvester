"""arc_stream wires HarvestedArc.warnings into RepositoryScope.record_warning (issue #637)."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest

from middleware.contracts.plugin_base import HarvestedArc
from middleware.harvester.upload import ArcStreamState, arc_stream
from middleware.shared.report import HarvestReport


async def _gen(*items: HarvestedArc) -> AsyncGenerator[HarvestedArc, None]:
    for item in items:
        yield item


@pytest.mark.asyncio
async def test_arc_stream_records_each_warning_without_changing_counts() -> None:
    report = HarvestReport(software_version="test")
    scope = report.open_repository("rdi-warn")
    state = ArcStreamState()
    arc = HarvestedArc(
        arc_json="{}",
        identifier="id-1",
        source_url="https://example.org/d1",
        warnings=("title fallback: headline", "unparsed datePublished"),
    )

    drained = [item async for item in arc_stream(_gen(arc), "rdi-warn", scope, state)]

    snap = scope.snapshot()
    assert drained == ["{}"]
    assert state.submitted == 1
    assert snap.harvested_datasets == 0
    assert snap.failed_datasets == 0
    assert snap.skipped_datasets == 0
    assert snap.warned_datasets == 2
    assert [w.message for w in snap.warnings] == [
        "title fallback: headline",
        "unparsed datePublished",
    ]
    assert all(w.record_id == "id-1" for w in snap.warnings)
    assert all(w.url == "https://example.org/d1" for w in snap.warnings)


@pytest.mark.asyncio
async def test_arc_stream_skips_record_warning_when_empty() -> None:
    scope = MagicMock()
    state = ArcStreamState()
    arc = HarvestedArc(arc_json="{}", warnings=())

    drained = [item async for item in arc_stream(_gen(arc), "rdi-ok", scope, state)]

    assert drained == ["{}"]
    scope.record_warning.assert_not_called()
    assert state.submitted == 1
