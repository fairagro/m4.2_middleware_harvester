"""Validate committed RO-Crate fixtures with DataHUB-equivalent arc-export."""

from __future__ import annotations

from pathlib import Path

import pytest

from middleware.arc_validation import validate_rocrate

pytestmark = pytest.mark.system_local


def test_each_arc_export_fixture_passes(arc_export_fixture_dirs: list[Path], arc_export_image: str) -> None:
    """Every committed per-RDI fixture must pass shared arc-export validation."""
    for rdi_dir in arc_export_fixture_dirs:
        crate_path = rdi_dir / "ro-crate-metadata.json"
        crate = crate_path.read_text(encoding="utf-8")
        result = validate_rocrate(crate, image=arc_export_image)
        assert result.ok, (
            f"{crate_path.relative_to(rdi_dir.parent.parent)} failed arc-export "
            f"(exit {result.exit_code}): {result.cause_excerpt or result.stderr or result.stdout}"
        )


def test_mvp_mapper_family_fixtures_present(arc_export_fixture_dirs: list[Path]) -> None:
    """MVP covers inspire / schema.org-generic / regal representative RDI ids."""
    names = {path.name for path in arc_export_fixture_dirs}
    assert {"bonares", "openagrar", "publisso"} <= names
