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
    """MVP covers inspire / schema.org-generic / regal; openagrar is MODS real-data (#614)."""
    rdi_ids = {path.relative_to(arc_export_fixtures_root).parts[0] for path in arc_export_fixture_dirs}
    # INSPIRE + Regal stand-ins (historical smoke RDI ids).
    assert {"bonares", "publisso"} <= rdi_ids
    # Schema.org/generic: edal/plabipd — not openagrar (live suite is MODS-mapped).
    assert {"edal", "plabipd"} & rdi_ids, (
        f"expected a Schema.org/generic RDI fixture (edal or plabipd), found {sorted(rdi_ids)}"
    )
    # OpenAgrar live MODS suite folder must remain present after smoke removal.
    assert "openagrar" in rdi_ids


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


def test_publisso_real_data_suite_has_multiple_cases(
    arc_export_fixture_dirs: list[Path],
    arc_export_fixtures_root: Path,
) -> None:
    """Landed publisso real-data suite must be multi-case (nested dirs), not smoke alone."""
    publisso_cases = _nested_cases(arc_export_fixture_dirs, arc_export_fixtures_root, "publisso")
    assert len(publisso_cases) >= 2, (
        f"expected ≥2 nested publisso/<case>/ fixtures, found {len(publisso_cases)}: "
        f"{[str(p.relative_to(arc_export_fixtures_root)) for p in publisso_cases]}"
    )


def test_plabipd_real_data_suite_has_multiple_cases(
    arc_export_fixture_dirs: list[Path],
    arc_export_fixtures_root: Path,
) -> None:
    """Landed plabipd real-data suite must be multi-case (nested dirs)."""
    plabipd_cases = _nested_cases(arc_export_fixture_dirs, arc_export_fixtures_root, "plabipd")
    assert len(plabipd_cases) >= 2, (
        f"expected ≥2 nested plabipd/<case>/ fixtures, found {len(plabipd_cases)}: "
        f"{[str(p.relative_to(arc_export_fixtures_root)) for p in plabipd_cases]}"
    )


def test_openagrar_real_data_suite_has_multiple_cases(
    arc_export_fixture_dirs: list[Path],
    arc_export_fixtures_root: Path,
) -> None:
    """Landed openagrar real-data suite must be multi-case (nested dirs), no root smoke."""
    openagrar_cases = _nested_cases(arc_export_fixture_dirs, arc_export_fixtures_root, "openagrar")
    assert len(openagrar_cases) >= 2, (
        f"expected ≥2 nested openagrar/<case>/ fixtures, found {len(openagrar_cases)}: "
        f"{[str(p.relative_to(arc_export_fixtures_root)) for p in openagrar_cases]}"
    )
    root_smoke = arc_export_fixtures_root / "openagrar" / "ro-crate-metadata.json"
    assert not root_smoke.exists(), "openagrar root smoke crate must be removed once real-data suite lands"


def test_phenoroam_real_data_suite_has_multiple_cases(
    arc_export_fixture_dirs: list[Path],
    arc_export_fixtures_root: Path,
) -> None:
    """Landed phenoroam real-data suite must be multi-case (nested dirs), no root smoke."""
    phenoroam_cases = _nested_cases(arc_export_fixture_dirs, arc_export_fixtures_root, "phenoroam")
    assert len(phenoroam_cases) >= 2, (
        f"expected ≥2 nested phenoroam/<case>/ fixtures, found {len(phenoroam_cases)}: "
        f"{[str(p.relative_to(arc_export_fixtures_root)) for p in phenoroam_cases]}"
    )
    root_smoke = arc_export_fixtures_root / "phenoroam" / "ro-crate-metadata.json"
    assert not root_smoke.exists(), "phenoroam must not invent a root smoke crate"
