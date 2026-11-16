"""The shipped fixture configs must be harvestable against the verbatim fixture robots.txt."""

from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
DEV_ENV = REPO_ROOT / "dev_environment"
FIXTURE_ROOT = DEV_ENV / "fixtures" / "openagrar"
FIXTURE_CONFIGS = ["config.fixtures.yaml", "config.fixtures.container.yaml"]


def _robots_respecting_urls(config_name: str) -> list[tuple[str, str]]:
    """(rdi, url) for the entry URL and every fixture file served next to it, per robots-respecting RDI."""
    config = yaml.safe_load((DEV_ENV / config_name).read_text(encoding="utf-8"))
    urls: list[tuple[str, str]] = []
    for repo in config["repositories"]:
        protocol = repo["generic"]["protocol"]
        if not protocol["http"].get("respect_robots_txt", True):
            continue
        entry_url = next(cfg["entry_url"] for key, cfg in protocol.items() if key != "http")
        entry = urlsplit(entry_url)
        served_dir = FIXTURE_ROOT / entry.path.lstrip("/").rpartition("/")[0]
        siblings = [f for f in sorted(served_dir.iterdir()) if f.is_file() and f.name != Path(entry.path).name]
        base = entry_url.rpartition("/")[0]
        urls.append((repo["rdi"], entry_url))
        urls.extend((repo["rdi"], f"{base}/{f.name}") for f in siblings)
    return urls


@pytest.mark.parametrize("config_name", FIXTURE_CONFIGS)
def test_robots_respecting_fixture_rdis_are_allowed_by_fixture_robots_txt(config_name: str) -> None:
    parser = RobotFileParser()
    parser.parse((FIXTURE_ROOT / "robots.txt").read_text(encoding="utf-8").splitlines())

    blocked = [
        (rdi, url) for rdi, url in _robots_respecting_urls(config_name) if not parser.can_fetch("*", urlsplit(url).path)
    ]

    assert not blocked
