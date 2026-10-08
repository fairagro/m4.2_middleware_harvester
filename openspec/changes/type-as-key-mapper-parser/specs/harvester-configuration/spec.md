# Spec Delta

## ADDED Requirements

### Requirement: Prefer type-as-key mapper and parser blocks

Canonical repository `mapper:` and `parser:` configuration SHALL use type-as-key form: shared fields (when any) as
siblings of exactly one type-named child whose key is the registry type. Type-specific settings MUST live under that
child. Legacy `{ type: <registry key>, … }` MUST remain accepted with a lift into the nested form and MUST emit a
`logger.warning` directing operators to type-as-key. Validation MUST NOT fail solely because `type:` is present.

#### Scenario: Nested mapper type-as-key loads

- **WHEN** a repository sets `mapper: { placeholders: …, regal_general: { resource_base_url: … } }` (exactly one type
  child)
- **THEN** configuration validation succeeds and the active mapper type is `regal_general`

#### Scenario: Nested parser type-as-key loads

- **WHEN** a repository sets `parser: { html_jsonld: { allowed_context_url: … } }`
- **THEN** configuration validation succeeds and the active parser type is `html_jsonld`

#### Scenario: Legacy mapper type discriminator warns and lifts

- **WHEN** a repository sets `mapper: { type: schema_org_general }`
- **THEN** validation succeeds after lift to `mapper.schema_org_general`, and a `logger.warning` mentions type-as-key

#### Scenario: Legacy parser type discriminator warns and lifts

- **WHEN** a repository sets `parser: { type: jsonld, allowed_context_url: … }`
- **THEN** validation succeeds after lift under `parser.jsonld`, and a `logger.warning` mentions type-as-key

#### Scenario: Two mapper type keys fail closed

- **WHEN** a repository sets both `mapper.regal_general` and `mapper.schema_org_general`
- **THEN** configuration validation fails

## MODIFIED Requirements

### Requirement: Repository entries that use shared mappers MUST include a mapper config beside the plugin

Each repository entry that uses shared `middleware.payload` mappers (`linked_data`, `generic`, `oai_pmh`, **`inspire`**)
MUST include a `mapper` configuration object beside the single plugin key, **or** MUST be covered by a documented legacy
lift: (for legacy `linked_data` only) a `linked_data.payload_type` lifted into the mapper block with a `logger.warning`;
(for legacy `inspire` only) an omitted `mapper` lifted to nested `inspire_general` with a `logger.warning`. The `mapper`
block MUST select an explicit mapper registry type via type-as-key (preferred) or deprecated `{ type: … }`, and MAY
include mapper-specific fields under the type child (and shared siblings such as `placeholders`). The `mapper` key is
NOT counted as a plugin field for the exactly-one-plugin rule.

#### Scenario: Valid linked_data entry with plugin and mapper

- **WHEN** a repository entry sets exactly one plugin key `linked_data` and a `mapper` with a supported type (nested or
  deprecated `type:`)
- **THEN** configuration validation succeeds

#### Scenario: Missing mapper is rejected for linked_data unless legacy payload_type is present

- **WHEN** a `linked_data` repository entry omits both `mapper` and `linked_data.payload_type`
- **THEN** configuration validation fails

#### Scenario: Legacy payload_type satisfies mapper requirement

- **WHEN** a `linked_data` repository entry omits `mapper` but sets `linked_data.payload_type` to a supported value
- **THEN** configuration validation succeeds after lifting into the mapper block, and a `logger.warning` is emitted

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
