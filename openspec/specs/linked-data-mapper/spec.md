# Linked Data Mapper

## Purpose

Define the mapping contract from a parsed Linked Data RDF graph to ARC RO-Crate JSON-LD.

Vocabulary-specific implementations (e.g. `GeneralSchemaOrgMapper` for schema.org,
or a future Regal mapper) register against `payload_type` and implement this interface.

## Requirements

### Requirement: Provide a LinkedDataMapper interface that accepts an rdflib.Graph and returns…
The system SHALL provide a `LinkedDataMapper` interface that accepts an `rdflib.Graph` and returns a serialized RO-Crate JSON-LD string.

#### Scenario: Satisfies — Provide a LinkedDataMapper interface that accepts an rdflib.Graph and returns…
- **WHEN** the conditions described by this requirement apply
- **THEN** The system SHALL provide a `LinkedDataMapper` interface that accepts an `rdflib.Graph` and returns a serialized RO-Crate JSON-LD string

### Requirement: Select mapper implementations using payload_type configuration values
The system SHALL select mapper implementations using `payload_type` configuration values.

#### Scenario: Satisfies — Select mapper implementations using payload_type configuration values
- **WHEN** the conditions described by this requirement apply
- **THEN** Select mapper implementations using `payload_type` configuration values

### Requirement: Keep mapping logic separate from sitemap discovery and dataset payload…
The system SHALL keep mapping logic separate from sitemap discovery and dataset payload extraction.

#### Scenario: Satisfies — Keep mapping logic separate from sitemap discovery and dataset payload…
- **WHEN** the conditions described by this requirement apply
- **THEN** Keep mapping logic separate from sitemap discovery and dataset payload extraction

### Requirement: Produce errors as HarvesterError objects when mapping fails
The system SHALL produce errors as `HarvesterError` objects when mapping fails.

#### Scenario: Satisfies — Produce errors as HarvesterError objects when mapping fails
- **WHEN** the conditions described by this requirement apply
- **THEN** Produce errors as `HarvesterError` objects when mapping fails

### Requirement: Support explicit, non-guessing mapper selection based on the configured payload…
The system SHALL support explicit, non-guessing mapper selection based on the configured payload type.

#### Scenario: Satisfies — Support explicit, non-guessing mapper selection based on the configured payload…
- **WHEN** the conditions described by this requirement apply
- **THEN** Support explicit, non-guessing mapper selection based on the configured payload type

### Requirement: Edge case — - A graph without valid dataset metadata must yield a…
The system SHALL handle this edge case: when - A graph without valid dataset metadata must yield a mapping error and not crash the plugin. - Mapping implementations must not depend on runtime config outside the selected `payload_type`., then behaviour matches the documented outcome.

#### Scenario: Edge case — - A graph without valid dataset metadata must yield a…
- **WHEN** - A graph without valid dataset metadata must yield a mapping error and not crash the plugin. - Mapping implementations must not depend on runtime config outside the selected `payload_type`.
- **THEN** behaviour matches the documented outcome
