## ADDED Requirements

### Requirement: Repository entries that use shared mappers MUST include a mapper config beside the plugin

Each repository entry that uses shared `middleware.payload` mappers (v1: `linked_data`) MUST include a `mapper`
configuration object beside the single plugin key, or MUST supply a legacy `linked_data.payload_type` that is lifted to
`mapper.type` with a `logger.warning`. The `mapper` block MUST specify an explicit mapper `type` (registry key) and
MAY include mapper-specific fields. The `mapper` key is NOT counted as a plugin field for the exactly-one-plugin rule.
Repository entries that do not use shared mappers in v1 (e.g. `inspire`) MUST NOT be required to set `mapper`.

#### Scenario: Valid linked_data entry with plugin and mapper

- **WHEN** a repository entry sets exactly one plugin key `linked_data` and a `mapper` with a supported `type`
- **THEN** configuration validation succeeds

#### Scenario: Missing mapper is rejected for linked_data unless legacy payload_type is present

- **WHEN** a `linked_data` repository entry omits both `mapper` and `linked_data.payload_type`
- **THEN** validation fails at startup with a clear error

#### Scenario: Legacy payload_type satisfies mapper requirement

- **WHEN** a `linked_data` repository entry omits `mapper` but sets `linked_data.payload_type` to a supported value
- **THEN** configuration validation succeeds after lifting to `mapper.type`, and a `logger.warning` is emitted

#### Scenario: inspire without mapper remains valid

- **WHEN** an `inspire` repository entry omits `mapper`
- **THEN** configuration validation succeeds (v1)

### Requirement: Validate mapper type and PayloadKind compatibility at startup

The system SHALL validate that the configured mapper `type` is registered and that its accepted `PayloadKind` is
compatible with the payload the selected plugin produces (for `linked_data`, `rdf_graph`). Unsupported mapper types MUST
fail fast at startup.

#### Scenario: Unknown mapper type fails fast

- **WHEN** `mapper.type` is not in the mapper registry
- **THEN** validation fails at startup and the process aborts before harvest

#### Scenario: Kind mismatch fails fast

- **WHEN** `mapper.type` accepts a `PayloadKind` other than what the plugin produces
- **THEN** validation fails at startup with a clear compatibility error
