# Harvester Configuration

## Purpose

Defines the structure of the harvester configuration file. The configuration
is validated at startup via Pydantic; an invalid config aborts the process
before any harvesting begins.

The top-level `Config` class follows the `ConfigWrapper / ConfigBase` pattern —
see skill [`config-wrapper`](../../../../.agents/skills/config-wrapper/SKILL.md).
Plugin configs (nested under each repository entry) are plain Pydantic `BaseModel`
subclasses; they are populated by the same YAML loading but do not extend `ConfigBase`.

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
The system SHALL ensure that each repository entry must contain exactly one plugin field (e.g. `inspire`); zero or two or more plugin fields are rejected with a validation error.

#### Scenario: Satisfies — Each repository entry must contain exactly one plugin field (e.g.…
- **WHEN** the conditions described by this requirement apply
- **THEN** Each repository entry must contain exactly one plugin field (e.g. `inspire`); zero or two or more plugin fields are rejected with a validation error

### Requirement: Plugin field types are statically typed Pydantic models; no dict[str,…
The system SHALL ensure that plugin field types are statically typed Pydantic models; no `dict[str, Any]` is used for plugin config.

#### Scenario: Satisfies — Plugin field types are statically typed Pydantic models; no dict[str,…
- **WHEN** the conditions described by this requirement apply
- **THEN** Plugin field types are statically typed Pydantic models; no `dict[str, Any]` is used for plugin config

### Requirement: Edge case — Repository entry with no plugin field
The system SHALL handle this edge case: when Repository entry with no plugin field, then `ValidationError` at startup, process aborts.

#### Scenario: Edge case — Repository entry with no plugin field
- **WHEN** Repository entry with no plugin field
- **THEN** `ValidationError` at startup, process aborts

### Requirement: Edge case — Repository entry with two plugin fields set
The system SHALL handle this edge case: when Repository entry with two plugin fields set, then `ValidationError` at startup, process aborts.

#### Scenario: Edge case — Repository entry with two plugin fields set
- **WHEN** Repository entry with two plugin fields set
- **THEN** `ValidationError` at startup, process aborts

### Requirement: Edge case — Repository entry with an unrecognised key
The system SHALL handle this edge case: when Repository entry with an unrecognised key, then Pydantic ignores extra fields by default; no silent data loss because `_PLUGIN_FIELDS` drives dispatch, not raw dict keys.

#### Scenario: Edge case — Repository entry with an unrecognised key
- **WHEN** Repository entry with an unrecognised key
- **THEN** Pydantic ignores extra fields by default; no silent data loss because `_PLUGIN_FIELDS` drives dispatch, not raw dict keys
