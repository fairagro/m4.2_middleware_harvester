## ADDED Requirements

### Requirement: Each repository entry may use the oai_pmh plugin key

The system SHALL allow each repository entry to select exactly one plugin field among the supported keys, including
`oai_pmh` alongside existing keys such as `inspire`, `linked_data`, and `generic`. Zero or two or more plugin fields
remain rejected. Sibling `mapper` and `parser` keys are not plugin fields.

#### Scenario: oai_pmh alone is accepted

- **WHEN** a repository entry sets only `oai_pmh` (plus shared fields and `mapper` / `parser` as required)
- **THEN** configuration validation succeeds

#### Scenario: oai_pmh together with generic is rejected

- **WHEN** a repository entry sets both `oai_pmh` and `generic`
- **THEN** configuration validation fails

### Requirement: oai_pmh repositories require mapper and parser config

The system SHALL require top-level repository `mapper` and `parser` blocks when the `oai_pmh` plugin key is selected,
and SHALL fail closed when the configured parser’s `produces` kind is incompatible with `mapper.accepts` at startup when
both kinds are known statically.

#### Scenario: oai_pmh without mapper fails closed

- **WHEN** a repository entry sets `oai_pmh` but omits `mapper`
- **THEN** configuration validation fails

#### Scenario: oai_pmh without parser fails closed

- **WHEN** a repository entry sets `oai_pmh` but omits `parser`
- **THEN** configuration validation fails

#### Scenario: Valid oai_pmh entry with plugin, parser, and mapper

- **WHEN** a repository entry sets `oai_pmh`, `parser` with a supported `type`, and `mapper` with a supported `type`
- **THEN** configuration validation succeeds

## MODIFIED Requirements

### Requirement: Repository entries that use shared mappers MUST include a mapper config beside the plugin

Each repository entry that uses shared `middleware.payload` mappers (v1: `linked_data`, `generic`, `oai_pmh`) MUST
include a `mapper` configuration object beside the single plugin key, or (for legacy `linked_data` only) MUST supply a
legacy `linked_data.payload_type` that is lifted to `mapper.type` with a `logger.warning`. The `mapper` block MUST
specify an explicit mapper `type` (registry key) and MAY include mapper-specific fields. The `mapper` key is NOT counted
as a plugin field for the exactly-one-plugin rule. Repository entries that do not use shared mappers in v1 (e.g.
`inspire`) MUST NOT be required to set `mapper`.

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

#### Scenario: Valid oai_pmh entry with plugin and mapper

- **WHEN** a repository entry sets exactly one plugin key `oai_pmh` and a `mapper` with a supported `type` (and `parser`
  as required for shared parsers)
- **THEN** configuration validation succeeds

### Requirement: Repository entries that use shared parsers MUST include a parser config beside the plugin

Each repository entry that uses shared `middleware.parsing` PayloadParsers (v1: `generic`, `oai_pmh`) MUST include a
`parser` configuration object beside the single plugin key. The `parser` block MUST specify an explicit parser `type`
(registry key). The `parser` key is NOT counted as a plugin field for the exactly-one-plugin rule. Repository entries
that do not use shared parsers in v1 (e.g. `inspire`, `linked_data`) MUST NOT be required to set `parser`.

#### Scenario: Valid generic entry with plugin, parser, and mapper

- **WHEN** a repository entry sets `generic`, `parser` with a supported `type`, and `mapper` with a supported `type`
- **THEN** configuration validation succeeds

#### Scenario: Missing parser is rejected for generic

- **WHEN** a `generic` repository entry omits `parser`
- **THEN** validation fails at startup with a clear error

#### Scenario: Missing parser is rejected for oai_pmh

- **WHEN** an `oai_pmh` repository entry omits `parser`
- **THEN** validation fails at startup with a clear error

#### Scenario: inspire without parser remains valid

- **WHEN** an `inspire` repository entry omits `parser`
- **THEN** configuration validation succeeds

### Requirement: Validate mapper type and PayloadKind compatibility at startup

The system SHALL validate that the configured mapper `type` is registered and that its accepted `PayloadKind` is
compatible with the payload the selected plugin produces (for `linked_data`, `generic`, and `oai_pmh`: as determined by
the configured shared parser’s `produces` kind when a sibling `parser` is present, typically `rdf_graph`). Unsupported
mapper types MUST fail fast at startup.

#### Scenario: Unknown mapper type fails fast

- **WHEN** `mapper.type` is not in the mapper registry
- **THEN** validation fails at startup and the process aborts before harvest

#### Scenario: Kind mismatch fails fast

- **WHEN** `mapper.type` accepts a `PayloadKind` other than what the plugin/parser produces
- **THEN** validation fails at startup with a clear compatibility error
