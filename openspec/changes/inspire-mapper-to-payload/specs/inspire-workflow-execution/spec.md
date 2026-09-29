# Plugin Execution (delta)

## MODIFIED Requirements

### Requirement: Implement InspirePlugin

The system SHALL implement `InspirePlugin` in `plugin.py`. The central harvester instantiates it with the plugin config
**and** the repository `mapper` config and invokes `run()` and `get_expected_datasets()` via the `Plugin` interface.

#### Scenario: Plugin interface wiring

- **WHEN** a repository is configured with the inspire plugin type and a `mapper` block
- **THEN** the orchestrator constructs `InspirePlugin` with the plugin config and mapper config and calls `run()` /
  `get_expected_datasets()`

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
