# Proposal

## Why

Operators cannot tell which harvester build a pod or local binary runs without reading the image tag (#42). Release CI
already computes a PEP 440 version and passes it to the image build as `APP_VERSION` →
`SETUPTOOLS_SCM_PRETEND_VERSION`, but every workspace package pins a static `version = "0.1.0"`, so the value never
reaches the installed metadata.

## What Changes

- `harvester` package takes its version from hatch-vcs (`dynamic = ["version"]`, `fallback_version = "0.0.0"`), so image
  builds record the CI release version in the `harvester` distribution metadata (already bundled by PyInstaller via
  `--copy-metadata harvester`).
- CLI gains `-v` / `--version`, printing `harvester <version>` and exiting `0` without loading a configuration.
- **Non-goals:** Fixing the root hatch-vcs tag pattern (`[0-9].[0-9]*` does not match the `…-docker-vX.Y.Z` release
  tags, so source runs report a stale `1.0.x.devN`). Versioning the other workspace packages.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `harvester-orchestration`: CLI reports the harvester version.

## Impact

- `middleware/harvester/pyproject.toml`, `uv.lock` (harvester version becomes dynamic)
- `middleware/harvester/src/middleware/harvester/main.py` + unit test
