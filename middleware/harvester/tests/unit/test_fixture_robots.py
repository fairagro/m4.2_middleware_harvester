"""The shipped fixture configs must be harvestable against the verbatim fixture robots.txt."""

from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import pytest

from middleware.generic.config import Config as GenericConfig
from middleware.harvester.config import Config

REPO_ROOT = Path(__file__).resolve().parents[4]
DEV_ENV = REPO_ROOT / "dev_environment"
FIXTURE_ROOT = DEV_ENV / "fixtures" / "openagrar"
FIXTURE_CONFIGS = ["config.fixtures.yaml", "config.fixtures.container.yaml"]


def _robots_respecting_urls(config_name: str) -> list[tuple[str, str]]:
    """(rdi, url) for the entry URL and every fixture file served next to it, per robots-respecting RDI."""
    config = Config.from_yaml_file(DEV_ENV / config_name)
    urls: list[tuple[str, str]] = []
    for repo in config.repositories:
        assert isinstance(repo.plugin_config, GenericConfig)
        protocol = repo.plugin_config.protocol
        assert protocol is not None
        assert protocol.http is not None
        assert protocol.protocol_type is not None
        if not protocol.http.respect_robots_txt:
            continue
        entry_url = getattr(protocol, protocol.protocol_type).entry_url
        entry = urlsplit(entry_url)
        served_dir = FIXTURE_ROOT / entry.path.lstrip("/").rpartition("/")[0]
        siblings = [f for f in sorted(served_dir.iterdir()) if f.is_file() and f.name != Path(entry.path).name]
        base = entry_url.rpartition("/")[0]
        urls.append((repo.rdi, entry_url))
        urls.extend((repo.rdi, f"{base}/{f.name}") for f in siblings)
    return urls


@pytest.mark.parametrize("config_name", FIXTURE_CONFIGS)
def test_robots_respecting_fixture_rdis_are_allowed_by_fixture_robots_txt(config_name: str) -> None:
    parser = RobotFileParser()
    parser.parse((FIXTURE_ROOT / "robots.txt").read_text(encoding="utf-8").splitlines())

    blocked = [
        (rdi, url) for rdi, url in _robots_respecting_urls(config_name) if not parser.can_fetch("*", urlsplit(url).path)
    ]

    assert not blocked
