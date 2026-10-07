# Harvest Protocol

## Purpose

Protocol abstraction for harvest discovery and transport selection, independent of payload parsing and ARC mapping.

## Requirements

### Requirement: Provide a Protocol interface for discovery

The system SHALL provide a Protocol abstraction that, given plugin configuration and an HTTP client where needed, can
stream discovery units and optionally report an expected count. Successful discovery units SHALL expose a stable
`identifier` used for deduplication. The discovery-unit type hierarchy used across plugins SHALL be defined in
`middleware.parsing` so Protocol implementations and PayloadParsers share the same types without cross-plugin imports.

#### Scenario: Discovery yields identifiable units

- **WHEN** a Protocol discovers harvestable units
- **THEN** each successful unit exposes a stable `identifier`

#### Scenario: Shared discovery types

- **WHEN** a Protocol yields a URL or inline discovery unit
- **THEN** the unit is an instance of a discovery type owned by `middleware.parsing`

### Requirement: Register Protocol implementations by type key

The system SHALL select Protocol implementations through a registry keyed by the active protocol type key under
`generic.protocol` (the single set type-named child such as `xml` or `mycore_solr`) and SHALL reject unregistered keys
at configuration validation. Protocol constructors SHALL receive the concrete type-specific settings model for that key
(not a structural typing.Protocol config view and not the full plugin config).

#### Scenario: Registered xml protocol resolves

- **WHEN** `generic.protocol` sets the `xml` child
- **THEN** the generic plugin constructs the XML Protocol implementation with `xml` settings

#### Scenario: Registered mycore_solr protocol resolves

- **WHEN** `generic.protocol` sets the `mycore_solr` child
- **THEN** the generic plugin constructs the MyCoRe Solr Protocol implementation with `mycore_solr` settings

### Requirement: Nested protocol config separates shared and type-specific settings

The system SHALL expose a nested `protocol` configuration object on the generic plugin config. Shared transport settings
(`http`) SHALL be fields of that object. Type-specific discovery settings SHALL live under exactly one type-named child
key matching a registered Protocol type. The system SHALL NOT require a parallel `type` discriminator field beside that
child key.

#### Scenario: Shared http beside type key

- **WHEN** a generic repository configures `protocol.http` and `protocol.mycore_solr.entry_url`
- **THEN** validation succeeds and the MyCoRe Solr Protocol uses that `http` client config with the type settings

#### Scenario: Two type keys fail closed

- **WHEN** `protocol` sets both `xml` and `mycore_solr`
- **THEN** configuration validation fails before harvesting starts

#### Scenario: Zero type keys fail closed

- **WHEN** `protocol` is present without any type-named child
- **THEN** configuration validation fails before harvesting starts

### Requirement: Deduplicate discovery identifiers and use shared skip/error types

The system SHALL deduplicate successful discovery identifiers within a Protocol run and SHALL yield shared
`SkippedRecord` for duplicates. Unusable discovery entries SHALL be yielded as shared `RecordProcessingError`, not
plugin-local wrapper types.

#### Scenario: Duplicate identifier is skipped

- **WHEN** the same discovery `identifier` appears more than once in one run
- **THEN** subsequent occurrences are yielded as `SkippedRecord`

### Requirement: Keep Protocol independent of PayloadParser and DataMapper

The system SHALL keep Protocol implementations free of payload parsing and ARC mapping logic. Protocols MAY produce
typed discovery payloads (for example a URL or an inline document) for parsers to consume.

#### Scenario: Protocol does not import mappers

- **WHEN** a Protocol implementation is loaded
- **THEN** it does not depend on DataMapper or PayloadParser registries to perform discovery
