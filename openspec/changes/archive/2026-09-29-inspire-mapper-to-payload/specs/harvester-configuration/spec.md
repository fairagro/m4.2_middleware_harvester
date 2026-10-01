# Harvester Configuration (delta)

## MODIFIED Requirements

### Requirement: Repository entries that use shared mappers MUST include a mapper config beside the plugin

Each repository entry that uses shared `middleware.payload` mappers (`linked_data`, `generic`, `oai_pmh`, **`inspire`**)
MUST include a `mapper` configuration object beside the single plugin key, **or** MUST be covered by a documented legacy
lift: (for legacy `linked_data` only) a `linked_data.payload_type` lifted to `mapper.type` with a `logger.warning`; (for
legacy `inspire` only) an omitted `mapper` lifted to `mapper.type: inspire_general` with a `logger.warning`. The
`mapper` block MUST specify an explicit mapper `type` (registry key) and MAY include mapper-specific fields. The
`mapper` key is NOT counted as a plugin field for the exactly-one-plugin rule.

#### Scenario: Valid linked_data entry with plugin and mapper

- **WHEN** a repository entry sets exactly one plugin key `linked_data` and a `mapper` with a supported `type`
- **THEN** configuration validation succeeds

#### Scenario: Missing mapper is rejected for linked_data unless legacy payload_type is present

- **WHEN** a `linked_data` repository entry omits both `mapper` and `linked_data.payload_type`
- **THEN** configuration validation fails

#### Scenario: Legacy payload_type satisfies mapper requirement

- **WHEN** a `linked_data` repository entry omits `mapper` but sets `linked_data.payload_type` to a supported value
- **THEN** configuration validation succeeds after lifting to `mapper.type`, and a `logger.warning` is emitted

#### Scenario: Omitted inspire mapper defaults to inspire_general

- **WHEN** an `inspire` repository entry omits `mapper`
- **THEN** configuration validation succeeds after lifting to `mapper.type: inspire_general`, and a `logger.warning` is
  emitted (omission is deprecated)

#### Scenario: Valid oai_pmh entry with plugin and mapper

- **WHEN** a repository entry sets exactly one plugin key `oai_pmh` and a `mapper` with a supported `type` (and `parser`
  as required)
- **THEN** configuration validation succeeds

#### Scenario: Valid inspire entry with plugin and mapper

- **WHEN** a repository entry sets `inspire` and `mapper` with type `inspire_general`
- **THEN** configuration validation succeeds

### Requirement: Validate mapper type and PayloadKind compatibility at startup

The system SHALL validate that the configured mapper `type` is registered and that its accepted `PayloadKind` is
compatible with the payload the selected plugin produces (for `linked_data`, `generic`, and `oai_pmh`: as determined by
the configured shared parser’s `produces` kind when a sibling `parser` is present; for **`inspire`**: `inspire_record`).
Unsupported mapper types MUST fail fast at startup.

#### Scenario: Unknown mapper type fails fast

- **WHEN** `mapper.type` is not in the mapper registry
- **THEN** validation fails at startup and the process aborts before harvest

#### Scenario: Kind mismatch fails fast

- **WHEN** `mapper.type` accepts a `PayloadKind` other than what the plugin/parser produces
- **THEN** validation fails at startup with a clear compatibility error

#### Scenario: inspire with non-inspire_record mapper fails fast

- **WHEN** an `inspire` repository sets `mapper.type` to a mapper that does not accept `inspire_record`
- **THEN** configuration validation fails at startup

## ADDED Requirements

### Requirement: inspire repositories use shared mapper config

The system SHALL resolve a top-level repository `mapper` for the `inspire` plugin key. When `mapper` is omitted, the
system SHALL default to `mapper.type: inspire_general`, emit a `logger.warning` that omission is deprecated, and SHALL
fail closed when a configured mapper’s `accepts` kind is not `inspire_record`.

#### Scenario: inspire without mapper defaults with deprecation warning

- **WHEN** a repository entry sets `inspire` but omits `mapper`
- **THEN** configuration validation succeeds with `mapper.type` equal to `inspire_general` and a deprecation warning

#### Scenario: Valid inspire entry with inspire_general

- **WHEN** a repository entry sets `inspire` and `mapper: { type: inspire_general }`
- **THEN** configuration validation succeeds
