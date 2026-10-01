# Plugin Execution

## Purpose

Exposes an asynchronous generator that iterates over CSW records and yields `HarvestedArc`, `HarvesterError`, or
`SkippedRecord` values. As a plugin it must not run standalone (no `main()`) and relies on the central harvester for API
uploads.

## Requirements

### Requirement: Implement InspirePlugin

The system SHALL implement `InspirePlugin` in `plugin.py`. The central harvester instantiates it with the plugin config
**and** the repository `mapper` config and invokes `run()` and `get_expected_datasets()` via the `Plugin` interface.

#### Scenario: Plugin interface wiring

- **WHEN** a repository is configured with the inspire plugin type and a `mapper` block
- **THEN** the orchestrator constructs `InspirePlugin` with the plugin config and mapper config and calls `run()` /
  `get_expected_datasets()`

### Requirement: Fetch records via CSWClient

The system SHALL use `CSWClient` to communicate with the CSW endpoint and fetch metadata records iteratively.

#### Scenario: Iterative CSW fetch

- **WHEN** `InspirePlugin.run()` executes
- **THEN** records are obtained through `CSWClient.get_records_async()`

### Requirement: Skip non-harvestable hierarchy levels

When a record’s `hierarchy` is set and is not one of `dataset`, `series`, or `nongeographicdataset`, the plugin MUST
yield a `SkippedRecord` (with the record URL when available) and MUST NOT map or upload that record.

#### Scenario: Non-dataset hierarchy

- **WHEN** a record has hierarchy `service` (or another non-harvestable value)
- **THEN** the plugin yields `SkippedRecord` and continues with the next record

### Requirement: Map valid records with InspireMapper

The system SHALL map each harvestable parsed record via the shared `inspire_general` `DataMapper` selected by repository
`mapper.type` (accepting `PayloadKind.inspire_record`). The plugin SHALL wrap the record in the shared intermediate
envelope before mapping and SHALL NOT call a plugin-local ISO→ARC mapper.

#### Scenario: Successful map

- **WHEN** a harvestable record is processed with a compatible `mapper.type`
- **THEN** the shared DataMapper produces `HarvestedArc` value(s) for that record

#### Scenario: Kind mismatch fails closed

- **WHEN** the configured mapper does not accept `inspire_record`
- **THEN** startup validation fails, or the record path fails closed before invoking an incompatible mapper

### Requirement: Yield HarvestedArc for successful maps

For each successfully mapped ARC the plugin MUST yield a `HarvestedArc` built via
`HarvestedArc.from_arctrl(arc, source_url=…)`, which serializes through `arc.ToROCrateJsonString()` and carries
study/assay counts plus the optional source URL. The plugin MUST NOT yield a bare JSON string.

#### Scenario: Successful harvest item

- **WHEN** mapping succeeds for a record
- **THEN** the generator yields a `HarvestedArc` (not a raw `str`) to the orchestrator

### Requirement: Yield RecordProcessingError on map failure

When mapping fails for a specific record, the plugin MUST yield `RecordProcessingError` for that record and continue
with remaining records.

#### Scenario: Map failure does not abort the run

- **WHEN** `map_record` raises for one record
- **THEN** the plugin yields `RecordProcessingError` and continues iteration

### Requirement: Plugin has no standalone entrypoint

The inspire plugin MUST NOT include a `main()` function, CLI argument parsing, or `ApiClient` upload logic.

#### Scenario: Upload remains orchestrator-owned

- **WHEN** inspecting the inspire package entrypoints and plugin module
- **THEN** API upload is performed only by the harvester orchestrator, not by the plugin
