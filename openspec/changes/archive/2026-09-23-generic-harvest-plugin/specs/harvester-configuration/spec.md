## ADDED Requirements

### Requirement: Each repository entry may use the generic plugin key

The system SHALL allow each repository entry to select exactly one plugin field
among the supported keys, including `generic` alongside existing keys such as
`inspire` and `linked_data`. Zero or two or more plugin fields remain rejected.

#### Scenario: generic alone is accepted

- **WHEN** a repository entry sets only `generic` (plus shared fields and
  `mapper` as required)
- **THEN** configuration validation succeeds

#### Scenario: generic together with linked_data is rejected

- **WHEN** a repository entry sets both `generic` and `linked_data`
- **THEN** configuration validation fails

### Requirement: generic repositories require mapper config

The system SHALL require a top-level repository `mapper` block when the
`generic` plugin key is selected, and SHALL fail closed when the configured
parser's `produces` kind is incompatible with `mapper.accepts` at startup when
both kinds are known statically.

#### Scenario: generic without mapper fails closed

- **WHEN** a repository entry sets `generic` but omits `mapper`
- **THEN** configuration validation fails
