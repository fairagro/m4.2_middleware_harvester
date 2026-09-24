## MODIFIED Requirements

### Requirement: Select Protocol and PayloadParser via registries

The system SHALL resolve `protocol_type` through the Protocol registry owned by the generic plugin package and
`parser_type` through the shared PayloadParser registry in `middleware.parsing`, and SHALL fail fast at startup on
unsupported enum values.

#### Scenario: Unknown protocol_type fails at config validation

- **WHEN** `protocol_type` is not registered
- **THEN** configuration validation fails before harvesting starts

#### Scenario: Unknown parser_type fails at config validation

- **WHEN** `parser_type` is not registered in `middleware.parsing`
- **THEN** configuration validation fails before harvesting starts

### Requirement: Orchestrate Protocol then PayloadParser then DataMapper

The system SHALL, for each successful discovery unit: invoke the configured PayloadParser from `middleware.parsing` to
obtain a `ParsedPayload`, fail closed when `payload.kind != mapper.accepts`, then invoke the shared DataMapper and yield
`HarvestedArc` on success.

#### Scenario: Kind mismatch fails the record without stopping the harvest

- **WHEN** a parser emits a `ParsedPayload` whose kind differs from the repository mapper's `accepts`
- **THEN** the plugin yields a record-level `HarvesterError` (or subclass) for that unit and continues with remaining
  discovery units

#### Scenario: Successful path yields HarvestedArc

- **WHEN** discovery, parse, kind-check, and map all succeed for a unit
- **THEN** the plugin yields a `HarvestedArc` for that unit
