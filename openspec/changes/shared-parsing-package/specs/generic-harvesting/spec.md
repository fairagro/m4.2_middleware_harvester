## MODIFIED Requirements

### Requirement: Provide a plugin-level Config as a Pydantic BaseModel

The system SHALL provide a plugin-level `Config` class as a Pydantic `BaseModel` referenced by the main harvester
repository schema under the `generic` plugin key. The config SHALL require an explicit `protocol_type` value and SHALL
NOT infer protocol from URLs or payloads. Shared parser selection SHALL use the repository-level `parser:` block (not a
field on the generic plugin config).

#### Scenario: Explicit protocol and parser types required

- **WHEN** a repository entry uses the `generic` plugin key
- **THEN** validation fails closed unless `protocol_type` is set on the plugin config and `parser.type` is set on the
  sibling `parser` block

#### Scenario: Explicit protocol type required

- **WHEN** a repository entry uses the `generic` plugin key without `protocol_type`
- **THEN** validation fails closed

#### Scenario: Parser selected via sibling parser block

- **WHEN** a `generic` repository is configured with `parser: { type: html_jsonld }`
- **THEN** the PayloadParser implementation is selected from repository `parser.type`

### Requirement: Select Protocol and PayloadParser via registries

The system SHALL resolve `protocol_type` through the Protocol registry owned by the generic plugin package and
`parser.type` through the shared PayloadParser registry in `middleware.parsing`, and SHALL fail fast at startup on
unsupported enum values.

#### Scenario: Unknown protocol_type fails at config validation

- **WHEN** `protocol_type` is not registered
- **THEN** configuration validation fails before harvesting starts

#### Scenario: Unknown parser.type fails at config validation

- **WHEN** `parser.type` is not registered in `middleware.parsing`
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
