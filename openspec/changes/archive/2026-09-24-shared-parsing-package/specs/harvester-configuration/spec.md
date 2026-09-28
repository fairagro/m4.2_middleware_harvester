## ADDED Requirements

### Requirement: Repository entries that use shared parsers MUST include a parser config beside the plugin

Each repository entry that uses shared `middleware.parsing` PayloadParsers (v1: `generic`) MUST include a `parser`
configuration object beside the single plugin key. The `parser` block MUST specify an explicit parser `type` (registry
key). The `parser` key is NOT counted as a plugin field for the exactly-one-plugin rule. Repository entries that do not
use shared parsers in v1 (e.g. `inspire`, `linked_data`) MUST NOT be required to set `parser`.

#### Scenario: Valid generic entry with plugin, parser, and mapper

- **WHEN** a repository entry sets `generic`, `parser` with a supported `type`, and `mapper` with a supported `type`
- **THEN** configuration validation succeeds

#### Scenario: Missing parser is rejected for generic

- **WHEN** a `generic` repository entry omits `parser`
- **THEN** validation fails at startup with a clear error

#### Scenario: inspire without parser remains valid

- **WHEN** an `inspire` repository entry omits `parser`
- **THEN** configuration validation succeeds

## MODIFIED Requirements

### Requirement: generic repositories require mapper config

The system SHALL require a top-level repository `mapper` block when the `generic` plugin key is selected, and SHALL fail
closed when the configured parser's `produces` kind is incompatible with `mapper.accepts` at startup when both kinds are
known statically.

#### Scenario: generic without mapper fails closed

- **WHEN** a repository entry sets `generic` but omits `mapper`
- **THEN** configuration validation fails

### Requirement: Each repository entry may use the generic plugin key

The system SHALL allow each repository entry to select exactly one plugin field among the supported keys, including
`generic` alongside existing keys such as `inspire` and `linked_data`. Zero or two or more plugin fields remain
rejected. Sibling `mapper` and `parser` keys are not plugin fields.

#### Scenario: generic alone is accepted

- **WHEN** a repository entry sets only `generic` (plus shared fields and `mapper` / `parser` as required)
- **THEN** configuration validation succeeds

#### Scenario: generic together with linked_data is rejected

- **WHEN** a repository entry sets both `generic` and `linked_data`
- **THEN** configuration validation fails
