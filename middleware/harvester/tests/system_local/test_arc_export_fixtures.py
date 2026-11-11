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


def _nested_cases(arc_export_fixture_dirs: list[Path], root: Path, rdi: str) -> list[Path]:
    return [
        path
        for path in arc_export_fixture_dirs
        if path.relative_to(root).parts[:1] == (rdi,) and len(path.relative_to(root).parts) >= 2
    ]


def test_bonares_real_data_suite_has_multiple_cases(
    arc_export_fixture_dirs: list[Path],
    arc_export_fixtures_root: Path,
) -> None:
    """Landed bonares real-data suite must be multi-case (nested dirs), not smoke alone."""
    bonares_cases = _nested_cases(arc_export_fixture_dirs, arc_export_fixtures_root, "bonares")
    assert len(bonares_cases) >= 2, (
        f"expected ≥2 nested bonares/<case>/ fixtures, found {len(bonares_cases)}: "
        f"{[str(p.relative_to(arc_export_fixtures_root)) for p in bonares_cases]}"
    )


def test_edal_real_data_suite_has_multiple_cases(
    arc_export_fixture_dirs: list[Path],
    arc_export_fixtures_root: Path,
) -> None:
    """Landed edal real-data suite must be multi-case (nested dirs)."""
    edal_cases = _nested_cases(arc_export_fixture_dirs, arc_export_fixtures_root, "edal")
    assert len(edal_cases) >= 2, (
        f"expected ≥2 nested edal/<case>/ fixtures, found {len(edal_cases)}: "
        f"{[str(p.relative_to(arc_export_fixtures_root)) for p in edal_cases]}"
    )
