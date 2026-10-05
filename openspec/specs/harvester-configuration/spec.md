# Harvester Configuration

## Purpose

Defines the structure of the harvester configuration file. The configuration is validated at startup via Pydantic; an
invalid config aborts the process before any harvesting begins.

The top-level `Config` class follows the `ConfigWrapper / ConfigBase` pattern — see skill
[`config-wrapper`](../../../.agents/skills/config-wrapper/SKILL.md). Plugin configs (nested under each repository entry)
are plain Pydantic `BaseModel` subclasses; they are populated by the same YAML loading but do not extend `ConfigBase`.

## Requirements

### Requirement: The configuration must contain exactly one api_client section

The system SHALL ensure that the configuration must contain exactly one `api_client` section.

#### Scenario: Satisfies — The configuration must contain exactly one api_client section

- **WHEN** the conditions described by this requirement apply
- **THEN** The configuration must contain exactly one `api_client` section

### Requirement: The configuration must contain a non-empty repositories list

The system SHALL ensure that the configuration must contain a non-empty `repositories` list.

#### Scenario: Satisfies — The configuration must contain a non-empty repositories list

- **WHEN** the conditions described by this requirement apply
- **THEN** The configuration must contain a non-empty `repositories` list

### Requirement: Each repository entry must contain a shared rdi field (string,…

The system SHALL ensure that each repository entry must contain a shared `rdi` field (string, required).

#### Scenario: Satisfies — Each repository entry must contain a shared rdi field (string,…

- **WHEN** the conditions described by this requirement apply
- **THEN** Each repository entry must contain a shared `rdi` field (string, required)

### Requirement: Each repository entry must contain exactly one plugin field (e.g.…

The system SHALL ensure that each repository entry must contain exactly one plugin field (e.g. `inspire`); zero or two
or more plugin fields are rejected with a validation error.

#### Scenario: Satisfies — Each repository entry must contain exactly one plugin field (e.g.…

- **WHEN** the conditions described by this requirement apply
- **THEN** Each repository entry must contain exactly one plugin field (e.g. `inspire`); zero or two or more plugin
  fields are rejected with a validation error

### Requirement: Plugin field types are statically typed Pydantic models; no dict[str,…

The system SHALL ensure that plugin field types are statically typed Pydantic models; no `dict[str, Any]` is used for
plugin config.

#### Scenario: Satisfies — Plugin field types are statically typed Pydantic models; no dict[str,…

- **WHEN** the conditions described by this requirement apply
- **THEN** Plugin field types are statically typed Pydantic models; no `dict[str, Any]` is used for plugin config

### Requirement: Edge case — Repository entry with no plugin field

The system SHALL handle this edge case: when Repository entry with no plugin field, then `ValidationError` at startup,
process aborts.

#### Scenario: Edge case — Repository entry with no plugin field

- **WHEN** Repository entry with no plugin field
- **THEN** `ValidationError` at startup, process aborts

### Requirement: Edge case — Repository entry with two plugin fields set

The system SHALL handle this edge case: when Repository entry with two plugin fields set, then `ValidationError` at
startup, process aborts.

#### Scenario: Edge case — Repository entry with two plugin fields set

- **WHEN** Repository entry with two plugin fields set
- **THEN** `ValidationError` at startup, process aborts

### Requirement: Edge case — Repository entry with an unrecognised key

The system SHALL handle this edge case: when Repository entry with an unrecognised key, then Pydantic ignores extra
fields by default; no silent data loss because `_PLUGIN_FIELDS` drives dispatch, not raw dict keys.

#### Scenario: Edge case — Repository entry with an unrecognised key

- **WHEN** Repository entry with an unrecognised key
- **THEN** Pydantic ignores extra fields by default; no silent data loss because `_PLUGIN_FIELDS` drives dispatch, not
  raw dict keys

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

### Requirement: generic repositories require mapper config

The system SHALL require a top-level repository `mapper` block when the `generic` plugin key is selected, and SHALL fail
closed when the configured parser's `produces` kind is incompatible with `mapper.accepts` at startup when both kinds are
known statically.

#### Scenario: generic without mapper fails closed

- **WHEN** a repository entry sets `generic` but omits `mapper`
- **THEN** configuration validation fails

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

### Requirement: Generic repositories use nested protocol config with deprecated flat lift

Each `generic` repository entry MUST supply protocol settings either as a nested `protocol` object (shared `http` plus
exactly one registered type-named child with type-specific fields such as `entry_url` when applicable) or as the
deprecated flat fields `protocol_type` and `sitemap_url` (optional flat `http` / `page_size`) that the system lifts into
`protocol` with a deprecation warning. The repository `source_url` for generic entries MUST resolve to the active type
child's `entry_url` when that field is present, and MAY be unset when the active type has no entry URL.

#### Scenario: Nested protocol source_url

- **WHEN** a generic repository sets `protocol.xml.entry_url` to `https://example.org/sitemap.xml`
- **THEN** repository `source_url` is that entry URL

#### Scenario: Deprecated flat sitemap_url still provides source_url

- **WHEN** a generic repository sets only deprecated `protocol_type` and `sitemap_url`
- **THEN** repository `source_url` equals that `sitemap_url` after lift

### Requirement: Placeholder values MUST be configurable per repository

The repository `mapper` block MUST accept an optional `placeholder_values` list of strings: the whole-value placeholders
this RDI writes instead of leaving a field empty. The default MUST be `middleware.payload.placeholders`
`DEFAULT_PLACEHOLDER_VALUES`; a configured list MUST replace the defaults. Values MUST be compared trimmed and
case-insensitive. The same field MUST apply to every plugin (`inspire`, `linked_data`, `generic`, `oai_pmh`).

#### Scenario: Per-RDI list

- **WHEN** a repository sets `mapper.placeholder_values: [" Keine Angabe "]`
- **THEN** configuration validation succeeds and that repository's placeholder list is `{"keine angabe"}`

#### Scenario: Default list

- **WHEN** a repository omits `mapper.placeholder_values`
- **THEN** its placeholder list is `DEFAULT_PLACEHOLDER_VALUES`
