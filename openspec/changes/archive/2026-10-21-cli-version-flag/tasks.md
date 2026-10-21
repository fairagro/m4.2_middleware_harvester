# Tasks

## 1. Version source

- [x] 1.1 Make the `harvester` package version dynamic via hatch-vcs with `fallback_version = "0.0.0"`; verify a wheel
      built with `SETUPTOOLS_SCM_PRETEND_VERSION=9.9.9` (as the image's package-builder does) carries `Version: 9.9.9`
- [x] 1.2 Verify the image build: PR #509 CI built with `APP_VERSION=3.3.0` and produced `harvester-3.3.0` wheel
      metadata (bundled into the binary via `--copy-metadata harvester`)

## 2. CLI flag

- [x] 2.1 Add `-v` / `--version` to the harvester CLI printing `harvester <version>` from `importlib.metadata`; verify
      with a unit test that it exits `0` without loading a configuration
