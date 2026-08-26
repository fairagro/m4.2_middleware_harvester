## ADDED Requirements

### Requirement: Repository entries MUST include a mapper config beside the plugin

Each repository entry MUST include a `mapper` configuration object beside the
single plugin key (`inspire`, `linked_data`, …). The `mapper` block MUST
specify an explicit mapper `type` (registry key) and MAY include
mapper-specific fields. The `mapper` key is NOT counted as a plugin field for
the exactly-one-plugin rule.

#### Scenario: Valid entry with plugin and mapper

- **WHEN** a repository entry sets exactly one plugin key and a `mapper` with
  a supported `type`
- **THEN** configuration validation succeeds

#### Scenario: Missing mapper is rejected for plugins that use shared mappers

- **WHEN** a `linked_data` repository entry omits `mapper` after this change
- **THEN** validation fails at startup with a clear error

### Requirement: Validate mapper type and PayloadKind compatibility at startup

The system SHALL validate that the configured mapper `type` is registered and
that its accepted `PayloadKind` is compatible with the payload the selected
plugin/parser produces (for `linked_data`, the RDF graph path / `rdf_graph`).
Unsupported mapper types MUST fail fast at startup.

#### Scenario: Unknown mapper type fails fast

- **WHEN** `mapper.type` is not in the mapper registry
- **THEN** validation fails at startup and the process aborts before harvest

#### Scenario: Kind mismatch fails fast

- **WHEN** `mapper.type` accepts a `PayloadKind` other than what the plugin
  produces
- **THEN** validation fails at startup with a clear compatibility error
