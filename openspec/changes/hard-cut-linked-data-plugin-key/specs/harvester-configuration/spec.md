## ADDED Requirements

### Requirement: Reject the linked_data plugin key

The system SHALL NOT accept the repository plugin key `linked_data`. Configuration that still sets `linked_data` MUST
fail validation at startup. The error MUST direct operators to `generic` with nested `protocol` and sibling `parser` /
`mapper` (migration documented in `docs/linked_data_to_generic.md`). Supported plugin keys remain `inspire`, `generic`,
and `oai_pmh`.

#### Scenario: linked_data repository is rejected

- **WHEN** a repository entry sets `linked_data`
- **THEN** configuration validation fails before harvest
- **AND** the failure message names `generic` (or the migration doc) as the replacement path

#### Scenario: generic repository still validates

- **WHEN** a repository entry sets exactly one plugin key `generic` with required sibling `parser` and `mapper`
- **THEN** configuration validation succeeds

### Requirement: Shared-mapper plugins require sibling mapper config (inspire legacy lift only)

Each repository entry that uses shared `middleware.payload` mappers (`generic`, `oai_pmh`, **`inspire`**) MUST include a
`mapper` configuration object beside the single plugin key, **or** MUST be covered by a documented legacy lift: (for
legacy `inspire` only) an omitted `mapper` lifted to nested `inspire_general` with a `logger.warning`. The `mapper`
block MUST select an explicit mapper registry type via type-as-key (preferred) or deprecated `{ type: … }`, and MAY
include mapper-specific fields under the type child (and shared siblings such as `placeholders`). The `mapper` key is
NOT counted as a plugin field for the exactly-one-plugin rule.

#### Scenario: Omitted inspire mapper defaults to inspire_general

- **WHEN** an `inspire` repository entry omits `mapper`
- **THEN** configuration validation succeeds after lifting to nested `inspire_general`, and a `logger.warning` is
  emitted (omission is deprecated)

#### Scenario: Valid oai_pmh entry with plugin and mapper

- **WHEN** a repository entry sets exactly one plugin key `oai_pmh` and a `mapper` with a supported type (and `parser`
  as required)
- **THEN** configuration validation succeeds

#### Scenario: Valid inspire entry with plugin and mapper

- **WHEN** a repository entry sets `inspire` and `mapper` with type `inspire_general` (nested or deprecated `type:`)
- **THEN** configuration validation succeeds

### Requirement: generic is a supported plugin key among inspire and oai_pmh

The system SHALL allow each repository entry to select exactly one plugin field among the supported keys, including
`generic` alongside existing keys such as `inspire` and `oai_pmh`. Zero or two or more plugin fields remain rejected.
Sibling `mapper` and `parser` keys are not plugin fields.

#### Scenario: generic alone is accepted

- **WHEN** a repository entry sets only `generic` (plus shared fields and `mapper` / `parser` as required)
- **THEN** configuration validation succeeds

#### Scenario: generic together with inspire is rejected

- **WHEN** a repository entry sets both `generic` and `inspire`
- **THEN** configuration validation fails

## REMOVED Requirements

### Requirement: linked_data plugin key emits deprecation warning

**Reason:** Soft-deprecation replaced by hard rejection of the plugin key (#467).

**Migration:** Reconfigure the repository as `generic:` with nested `protocol` and sibling `parser` / `mapper` (see
`docs/linked_data_to_generic.md`).

### Requirement: Repository entries that use shared mappers MUST include a mapper config beside the plugin

**Reason:** Replaced by “Shared-mapper plugins require sibling mapper config (inspire legacy lift only)” after dropping
`linked_data` / `payload_type` lift scenarios (#467).

**Migration:** See the ADDED requirement; no `linked_data.payload_type` lift remains.

### Requirement: Each repository entry may use the generic plugin key

**Reason:** Replaced by “generic is a supported plugin key among inspire and oai_pmh” so dual-plugin scenarios no longer
reference `linked_data` (#467).

**Migration:** See the ADDED requirement (`generic` + `inspire` mutual exclusion).

## MODIFIED Requirements

### Requirement: Validate mapper type and PayloadKind compatibility at startup

The system SHALL validate that the configured mapper `type` is registered and that its accepted `PayloadKind` is
compatible with the payload the selected plugin produces (for `generic` and `oai_pmh`: as determined by the configured
shared parser’s `produces` kind when a sibling `parser` is present; for **`inspire`**: `inspire_record`). Unsupported
mapper types MUST fail fast at startup.

#### Scenario: Unknown mapper type fails fast

- **WHEN** `mapper.type` is not in the mapper registry
- **THEN** validation fails at startup and the process aborts before harvest

#### Scenario: Kind mismatch fails fast

- **WHEN** `mapper.type` accepts a `PayloadKind` other than what the plugin/parser produces
- **THEN** validation fails at startup with a clear compatibility error

#### Scenario: inspire with non-inspire_record mapper fails fast

- **WHEN** an `inspire` repository sets `mapper.type` to a mapper that does not accept `inspire_record`
- **THEN** configuration validation fails at startup

### Requirement: Repository entries that use shared parsers MUST include a parser config beside the plugin

Each repository entry that uses shared `middleware.parsing` PayloadParsers (v1: `generic`, `oai_pmh`) MUST include a
`parser` configuration object beside the single plugin key. The `parser` block MUST specify an explicit parser `type`
(registry key). The `parser` key is NOT counted as a plugin field for the exactly-one-plugin rule. Repository entries
that do not use shared parsers in v1 (e.g. `inspire`) MUST NOT be required to set `parser`.

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
`oai_pmh` alongside existing keys such as `inspire` and `generic`. Zero or two or more plugin fields remain rejected.
Sibling `mapper` and `parser` keys are not plugin fields.

#### Scenario: oai_pmh alone is accepted

- **WHEN** a repository entry sets only `oai_pmh` (plus shared fields and `mapper` / `parser` as required)
- **THEN** configuration validation succeeds

#### Scenario: oai_pmh together with generic is rejected

- **WHEN** a repository entry sets both `oai_pmh` and `generic`
- **THEN** configuration validation fails

### Requirement: Placeholder values MUST be configurable per repository

The repository `mapper` block MUST accept an optional `placeholders` object (`middleware.payload.placeholders`
`PlaceholderConfig`): `values`, the whole-value placeholders this RDI writes instead of leaving a field empty, and
`unrendered_templates`, whether unrendered `$var`, `${var}` and `{{var}}` templates also count. The defaults MUST live
on the model and MUST be empty (`values: []`, `unrendered_templates: false`), so nothing is treated as a placeholder
unless the operator configures it. Values MUST be compared trimmed and case-insensitive. Code that receives the
placeholders (parsers, clients, mappers) MUST take the `PlaceholderConfig` object and MUST NOT supply its own default.
The same field MUST apply to every plugin (`inspire`, `generic`, `oai_pmh`).

#### Scenario: Per-RDI values

- **WHEN** a repository sets `mapper.placeholders.values: [" Keine Angabe "]`
- **THEN** configuration validation succeeds and that repository's placeholder values are `{"keine angabe"}`

#### Scenario: No placeholders by default

- **WHEN** a repository omits `mapper.placeholders`
- **THEN** no value counts as a placeholder, including "None" and `$licenseURL`
