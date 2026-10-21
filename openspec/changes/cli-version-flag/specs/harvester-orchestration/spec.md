# Spec Delta

## ADDED Requirements

### Requirement: CLI reports the harvester version

The harvester CLI SHALL accept `-v` / `--version`, print `harvester <version>` to stdout and exit with code `0` without
loading a configuration or contacting any endpoint. `<version>` MUST be the installed `harvester` distribution version,
which release image builds set from the CI-computed `APP_VERSION`.

#### Scenario: Version flag

- **WHEN** the harvester is invoked with `--version` or `-v`
- **THEN** it prints `harvester <version>` and exits `0` without reading the configuration file

#### Scenario: Release image reports the build version

- **WHEN** the image is built with `APP_VERSION=X.Y.Z` and the binary is invoked with `--version`
- **THEN** it prints `harvester X.Y.Z`
