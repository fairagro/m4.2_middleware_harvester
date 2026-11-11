"""Validate committed RO-Crate fixtures with DataHUB-equivalent arc-export."""

from __future__ import annotations

from pathlib import Path

import pytest

from middleware.arc_validation import validate_rocrate

pytestmark = pytest.mark.system_local


def test_arc_export_fixture_passes(
    arc_export_fixture_dir: Path,
    arc_export_fixtures_root: Path,
    arc_export_image: str,
) -> None:
    """Each committed per-RDI fixture must pass shared arc-export validation."""
    crate_path = arc_export_fixture_dir / "ro-crate-metadata.json"
    crate = crate_path.read_text(encoding="utf-8")
    result = validate_rocrate(crate, image=arc_export_image)
    assert result.ok, (
        f"{crate_path.relative_to(arc_export_fixtures_root)} failed arc-export "
        f"(exit {result.exit_code}): {result.cause_excerpt or result.stderr or result.stdout}"
    )


def test_mvp_mapper_family_fixtures_present(
    arc_export_fixture_dirs: list[Path],
    arc_export_fixtures_root: Path,
) -> None:
    """MVP covers inspire / schema.org-generic / regal representative RDI ids."""
    rdi_ids = {path.relative_to(arc_export_fixtures_root).parts[0] for path in arc_export_fixture_dirs}
    assert {"bonares", "openagrar", "publisso"} <= rdi_ids
