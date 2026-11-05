## ADDED Requirements

### Requirement: Stamp installed harvester version on the shared report

When the harvester creates the run `HarvestReport`, it MUST set `software_version` to the installed `harvester`
distribution’s PEP 440 version (same value logged at job start / printed by `--version`). The shared JSON-LD serializer
owns emission of `schema:instrument` / `schema:softwareVersion`; the harvester MUST NOT re-implement that shape.

#### Scenario: Report carries the package version

- **WHEN** the orchestrator creates a `HarvestReport` for a run
- **THEN** `HarvestReport.software_version` equals `importlib.metadata.version("harvester")`

#### Scenario: Serializer still owns the JSON-LD instrument node

- **WHEN** `JsonLdReportSerializer` renders a report with `software_version` set
- **THEN** the harvester does not add a parallel instrument field outside the shared serializer
