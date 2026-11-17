"""Docker helpers for arc-export system_local tests."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

_SYSTEM_LOCAL_DIR = Path(__file__).resolve().parent
# Single SoT for the pinned base image (CI reads the same file).
ARC_EXPORT_BASE_DIGEST = (_SYSTEM_LOCAL_DIR / "arc-export-base.digest").read_text(encoding="utf-8").strip()
ARC_EXPORT_WRAPPER_TAG = "fairagro-arc-export-path:ci"
IMAGE_ENV_VAR = "FAIRAGRO_ARC_EXPORT_IMAGE"

FIXTURES_ROOT = _SYSTEM_LOCAL_DIR.parents[0] / "fixtures" / "arc_export"


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    probe = subprocess.run(  # noqa: S603 — fixed argv, no shell
        ["docker", "info"],
        check=False,
        capture_output=True,
        text=True,
    )
    return probe.returncode == 0


def _ensure_path_wrapper_image() -> str:
    """Build a local image where ``arc-export`` is on PATH (upstream image only has ``/arc-export``)."""
    dockerfile = f"FROM {ARC_EXPORT_BASE_DIGEST}\nRUN ln -sf /arc-export /usr/local/bin/arc-export\n"
    build = subprocess.run(  # noqa: S603
        ["docker", "build", "-t", ARC_EXPORT_WRAPPER_TAG, "-f-", "."],
        check=False,
        capture_output=True,
        text=True,
        input=dockerfile,
        cwd="/tmp",
    )
    if build.returncode != 0:
        msg = build.stderr or build.stdout or "docker build failed"
        pytest.fail(f"Failed to build arc-export PATH wrapper image: {msg}")
    return ARC_EXPORT_WRAPPER_TAG


def _discover_fixture_dirs() -> list[Path]:
    """Leaf dirs under ``arc_export/`` that contain ``ro-crate-metadata.json``.

    Supports both ``<rdi>/ro-crate-metadata.json`` (smoke) and
    ``<rdi>/<case>/ro-crate-metadata.json`` (real-data suites).
    """
    if not FIXTURES_ROOT.is_dir():
        return []
    return sorted({path.parent for path in FIXTURES_ROOT.rglob("ro-crate-metadata.json") if path.is_file()})


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize each RO-Crate fixture directory as its own test case."""
    if "arc_export_fixture_dir" not in metafunc.fixturenames:
        return
    dirs = _discover_fixture_dirs()
    metafunc.parametrize(
        "arc_export_fixture_dir",
        dirs,
        ids=[str(path.relative_to(FIXTURES_ROOT)) for path in dirs],
    )


@pytest.fixture(scope="session")
def arc_export_image() -> str:
    """Resolve the Docker image for ``validate_rocrate`` (env override or local PATH wrapper)."""
    if not _docker_available():
        pytest.skip("Docker is required for system_local arc-export fixtures")
    override = os.environ.get(IMAGE_ENV_VAR, "").strip()
    if override:
        return override
    return _ensure_path_wrapper_image()


@pytest.fixture(scope="session")
def arc_export_fixture_dirs() -> list[Path]:
    """Fixture directories that contain ``ro-crate-metadata.json`` (smoke or case)."""
    dirs = _discover_fixture_dirs()
    if not FIXTURES_ROOT.is_dir():
        pytest.fail(f"Missing fixtures root: {FIXTURES_ROOT}")
    if not dirs:
        pytest.fail(f"No ro-crate-metadata.json fixtures under {FIXTURES_ROOT}")
    return dirs


@pytest.fixture(scope="session")
def arc_export_fixtures_root() -> Path:
    """Root of committed arc-export RO-Crate fixtures."""
    return FIXTURES_ROOT
