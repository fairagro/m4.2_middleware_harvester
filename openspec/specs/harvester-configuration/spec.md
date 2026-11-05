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

### Requirement: Require type-as-key mapper and parser blocks

Canonical repository `mapper:` and `parser:` configuration SHALL use type-as-key form: shared fields (when any) as
siblings of exactly one type-named child whose key is the registry type. Type-specific settings MUST live under that
child. Configuration that still sets a `type:` discriminator under `mapper` or `parser` MUST fail validation as an
unknown field (no soft-lift and no dedicated migration-only validator). The system MUST NOT lift or warn-and-accept
legacy `{ type: <registry key>, … }` shapes.

#### Scenario: Nested mapper type-as-key loads

- **WHEN** a repository sets `mapper: { placeholders: …, regal_general: { resource_base_url: … } }` (exactly one type
  child)
- **THEN** configuration validation succeeds and the active mapper type is `regal_general`

#### Scenario: Nested parser type-as-key loads

- **WHEN** a repository sets `parser: { html_jsonld: { allowed_context_url: … } }`
- **THEN** configuration validation succeeds and the active parser type is `html_jsonld`

#### Scenario: Legacy mapper type discriminator is rejected

- **WHEN** a repository sets `mapper: { type: schema_org_general }`
- **THEN** configuration validation fails before harvest

#### Scenario: Legacy parser type discriminator is rejected

- **WHEN** a repository sets `parser: { type: jsonld, allowed_context_url: … }`
- **THEN** configuration validation fails before harvest

#### Scenario: Two mapper type keys fail closed

- **WHEN** a repository sets both `mapper.regal_general` and `mapper.schema_org_general`
- **THEN** configuration validation fails

### Requirement: Reject the linked_data plugin key

The system SHALL NOT accept the repository plugin key `linked_data`. Configuration that still sets `linked_data` MUST
fail validation at startup as an unknown repository field (no dedicated `linked_data` field or migration-only
validator). Supported plugin keys remain `inspire`, `generic`, and `oai_pmh`. Migration guidance for operators remains
in `docs/linked_data_to_generic.md`.

#### Scenario: linked_data repository is rejected

- **WHEN** a repository entry sets `linked_data`
- **THEN** configuration validation fails before harvest

#### Scenario: generic repository still validates

- **WHEN** a repository entry sets exactly one plugin key `generic` with required sibling `parser` and `mapper`
- **THEN** configuration validation succeeds

### Requirement: Shared-mapper plugins require sibling mapper config (inspire legacy lift only)

Each repository entry that uses shared `middleware.payload` mappers (`generic`, `oai_pmh`, **`inspire`**) MUST include a
`mapper` configuration object beside the single plugin key, **or** MUST be covered by a documented legacy lift: (for
legacy `inspire` only) an omitted `mapper` lifted to nested `inspire_general` with a `logger.warning`. The `mapper`
block MUST select an explicit mapper registry type via type-as-key, and MAY include mapper-specific fields under the
type child (and shared siblings such as `placeholders`). The `mapper` key is NOT counted as a plugin field for the
exactly-one-plugin rule.

#### Scenario: Omitted inspire mapper defaults to inspire_general

- **WHEN** an `inspire` repository entry omits `mapper`
- **THEN** configuration validation succeeds after lifting to nested `inspire_general`, and a `logger.warning` is
  emitted (omission is deprecated)

#### Scenario: Valid oai_pmh entry with plugin and mapper

- **WHEN** a repository entry sets exactly one plugin key `oai_pmh` and a `mapper` with a supported type (and `parser`
  as required)
- **THEN** configuration validation succeeds

#### Scenario: Valid inspire entry with plugin and mapper

- **WHEN** a repository entry sets `inspire` and nested `mapper.inspire_general`
- **THEN** configuration validation succeeds

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

### Requirement: inspire repositories use shared mapper config

The system SHALL resolve a top-level repository `mapper` for the `inspire` plugin key. When `mapper` is omitted, the
system SHALL default to nested `mapper.inspire_general`, emit a `logger.warning` that omission is deprecated, and SHALL
fail closed when a configured mapper’s `accepts` kind is not `inspire_record`.

#### Scenario: inspire without mapper defaults with deprecation warning

- **WHEN** a repository entry sets `inspire` but omits `mapper`
- **THEN** configuration validation succeeds with active mapper type `inspire_general` and a deprecation warning

#### Scenario: Valid inspire entry with inspire_general

- **WHEN** a repository entry sets `inspire` and `mapper: { inspire_general: {} }`
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

### Requirement: Generic repositories use nested protocol config

Each `generic` repository entry MUST supply protocol settings as a nested `protocol` object (shared `http` plus exactly
one registered type-named child with type-specific fields such as `entry_url` when applicable). Flat `protocol_type`,
`sitemap_url`, `http`, and `page_size` on the generic plugin config MUST NOT be accepted. The repository `source_url`
for generic entries MUST resolve to the active type child's `entry_url` when that field is present, and MAY be unset
when the active type has no entry URL.

#### Scenario: Nested protocol source_url

- **WHEN** a generic repository sets `protocol.xml.entry_url` to `https://example.org/sitemap.xml`
- **THEN** repository `source_url` is that entry URL

#### Scenario: Flat protocol fields rejected

- **WHEN** a generic repository sets only flat `protocol_type` and `sitemap_url`
- **THEN** configuration validation fails

### Requirement: Accept nested mycore_rest protocol settings

The system SHALL accept nested `generic.protocol.mycore_rest` with at least `entry_url` (list endpoint including
operator filters) and optional `page_size` (or equivalent paging control) consistent with other paginated protocols.

#### Scenario: mycore_rest entry_url required

- **WHEN** `protocol.mycore_rest` is selected without `entry_url`
- **THEN** configuration validation fails

### Requirement: Accept mods_xml parser and mods_general mapper keys

The system SHALL accept repository sibling `parser.mods_xml` and `mapper.mods_general` (type-as-key) as valid
registrations alongside existing parser/mapper keys.

#### Scenario: OpenAgrar-style composition validates

- **WHEN** a repository configures `generic` + `protocol.mycore_rest` + `parser.mods_xml` + `mapper.mods_general`
- **THEN** configuration validation succeeds when kinds align (`mods_record`)

### Requirement: Placeholder values MUST be configurable per repository

Placeholders MUST be configured as a `placeholders` object (`middleware.payload.placeholders` `PlaceholderConfig`):
`values`, the whole-value placeholders this RDI writes instead of leaving a field empty, and `unrendered_templates`,
whether unrendered `$var`, `${var}` and `{{var}}` templates also count. The block MUST sit where the check runs: the
`inspire` plugin block for INSPIRE (`inspire.placeholders`, read by the parser), and the `mapper` block for `generic`
and `oai_pmh` (`mapper.placeholders`, read by the mapper). The defaults MUST live on the model and MUST be empty
(`values: []`, `unrendered_templates: false`), so nothing is treated as a placeholder unless the operator configures it.
Values MUST be compared trimmed and case-insensitive. Code that receives the placeholders (parsers, clients, mappers)
MUST take a config object holding the `PlaceholderConfig` and MUST NOT supply its own default.

#### Scenario: Per-RDI values

- **WHEN** a repository sets `mapper.placeholders.values: [" Keine Angabe "]`
- **THEN** configuration validation succeeds and that repository's placeholder values are `{"keine angabe"}`

#### Scenario: INSPIRE placeholders on the plugin block

- **WHEN** an `inspire` repository sets `inspire.placeholders.values: ["None"]`
- **THEN** configuration validation succeeds without a warning and the INSPIRE parser treats "None" as a placeholder

#### Scenario: No placeholders by default

- **WHEN** a repository sets no `placeholders`
- **THEN** no value counts as a placeholder, including "None" and `$licenseURL`

### Requirement: mapper.placeholders on inspire repositories is deprecated

When an `inspire` repository explicitly sets `mapper.placeholders`, configuration validation MUST succeed, MUST emit a
`logger.warning` pointing at `inspire.placeholders`, and MUST use that value as `inspire.placeholders`. When both are
set and differ, validation MUST fail. An unset `mapper.placeholders` MUST NOT warn. Repositories of other plugins MUST
keep reading `mapper.placeholders` unchanged.

#### Scenario: Legacy location is lifted

- **WHEN** an `inspire` repository sets `mapper.placeholders.values: ["None"]` and no `inspire.placeholders`
- **THEN** validation succeeds, a deprecation warning is logged, and `inspire.placeholders.values` is `{"none"}`

#### Scenario: Conflicting locations

- **WHEN** an `inspire` repository sets `mapper.placeholders.values: ["None"]` and
  `inspire.placeholders.values: ["n/a"]`
- **THEN** configuration validation fails naming both fields

#### Scenario: Generic repository is unaffected

- **WHEN** a `generic` repository sets `mapper.placeholders.unrendered_templates: true`
- **THEN** no deprecation warning is logged and the mapper receives that `PlaceholderConfig`

### Requirement: Top-level jsonld_context_cache_max_entries bounds the shared context cache

The system SHALL accept optional top-level `jsonld_context_cache_max_entries` (positive integer; default 64) on the
harvester `Config`. At startup the harvester MUST apply that value as the process-lifetime JSON-LD context-document
cache size cap (see `jsonld-context-loader`).

#### Scenario: Default cache size

- **WHEN** config omits `jsonld_context_cache_max_entries`
- **THEN** configuration validation succeeds and the effective cache size cap is 64

#### Scenario: Explicit cache size

- **WHEN** config sets `jsonld_context_cache_max_entries: 8`
- **THEN** configuration validation succeeds and startup configures the shared cache for at most 8 entries

#### Scenario: Non-positive cache size rejected

- **WHEN** config sets `jsonld_context_cache_max_entries: 0`
- **THEN** configuration validation fails
