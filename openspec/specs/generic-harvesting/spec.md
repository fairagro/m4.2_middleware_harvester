# Generic Harvesting

## Purpose

Generic harvest plugin that composes a registered Protocol, PayloadParser, and
repository-level DataMapper into the standard AsyncGenerator harvest contract.

## Requirements

### Requirement: Provide a plugin-level Config as a Pydantic BaseModel

The system SHALL provide a plugin-level `Config` class as a Pydantic `BaseModel`
referenced by the main harvester repository schema under the `generic` plugin
key. The config SHALL require explicit `protocol_type` and `parser_type` values
and SHALL NOT infer protocol or parser from URLs or payloads.

#### Scenario: Explicit protocol and parser types required

- **WHEN** a repository entry uses the `generic` plugin key
- **THEN** validation fails closed unless both `protocol_type` and `parser_type`
  are set to registered enum values

### Requirement: Implement GenericPlugin satisfying the Plugin harvest contract

The system SHALL implement a generic plugin that the orchestrator instantiates
with plugin config plus repository `mapper` config and invokes via the shared
`Plugin` interface (`run()` and `get_expected_datasets()`).

#### Scenario: Orchestrator dispatches generic repositories

- **WHEN** a repository entry selects `generic`
- **THEN** the harvester instantiates the generic plugin and consumes its
  AsyncGenerator of `HarvestedArc | HarvesterError | SkippedRecord`

### Requirement: Orchestrate Protocol then PayloadParser then DataMapper

The system SHALL, for each successful discovery unit: invoke the configured
PayloadParser to obtain a `ParsedPayload`, fail closed when
`payload.kind != mapper.accepts`, then invoke the shared DataMapper and yield
`HarvestedArc` on success.

#### Scenario: Kind mismatch fails the record without stopping the harvest

- **WHEN** a parser emits a `ParsedPayload` whose kind differs from the
  repository mapper's `accepts`
- **THEN** the plugin yields a record-level `HarvesterError` (or subclass) for
  that unit and continues with remaining discovery units

#### Scenario: Successful path yields HarvestedArc

- **WHEN** discovery, parse, kind-check, and map all succeed for a unit
- **THEN** the plugin yields a `HarvestedArc` for that unit

### Requirement: Select Protocol and PayloadParser via registries

The system SHALL resolve `protocol_type` and `parser_type` through registries
and SHALL fail fast at startup on unsupported enum values.

#### Scenario: Unknown protocol_type fails at config validation

- **WHEN** `protocol_type` is not registered
- **THEN** configuration validation fails before harvesting starts

### Requirement: Forward discovery errors and skips unchanged

The system SHALL forward `RecordProcessingError` and `SkippedRecord` emitted by
the Protocol discovery stream to the orchestrator unchanged, and SHALL continue
harvesting remaining units after record-level parse or map failures.

#### Scenario: Empty discovery exits cleanly

- **WHEN** the Protocol yields no successful discovery units
- **THEN** the plugin yields zero `HarvestedArc` outputs and exits without error

### Requirement: Expected count comes from the Protocol when available

The system SHALL implement `get_expected_datasets()` by asking the configured
Protocol for an expected count when the Protocol supports it, and SHALL return
`None` when the count cannot be determined.

#### Scenario: Protocol count failure softens to None

- **WHEN** the Protocol raises while computing expected count
- **THEN** `get_expected_datasets()` returns `None` and harvesting may still run
