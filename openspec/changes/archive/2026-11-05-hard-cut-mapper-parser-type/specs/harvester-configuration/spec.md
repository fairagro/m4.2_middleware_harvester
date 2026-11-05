## ADDED Requirements

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

## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Prefer type-as-key mapper and parser blocks

**Reason:** Soft-accept of legacy `{ type: … }` replaced by hard rejection (#478).

**Migration:** Use type-as-key only (`mapper: { <registry_key>: { … } }` / `parser: { <registry_key>: { … } }`). See the
ADDED requirement “Require type-as-key mapper and parser blocks”.
