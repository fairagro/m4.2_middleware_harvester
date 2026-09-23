# Harvest Protocol

## Purpose

Protocol abstraction for harvest discovery and transport selection, independent
of payload parsing and ARC mapping.

## Requirements

### Requirement: Provide a Protocol interface for discovery

The system SHALL provide a Protocol abstraction that, given plugin
configuration and an HTTP client where needed, can stream discovery units and
optionally report an expected count. Successful discovery units SHALL expose a
stable `identifier` used for deduplication.

#### Scenario: Discovery yields identifiable units

- **WHEN** a Protocol discovers harvestable units
- **THEN** each successful unit exposes a stable `identifier`

### Requirement: Register Protocol implementations by type key

The system SHALL select Protocol implementations through a registry keyed by
`protocol_type` and SHALL reject unregistered keys at configuration validation.

#### Scenario: Registered xml protocol resolves

- **WHEN** `protocol_type` refers to a registered XML-sitemap-style protocol
- **THEN** the generic plugin constructs that Protocol implementation

### Requirement: Deduplicate discovery identifiers and use shared skip/error types

The system SHALL deduplicate successful discovery identifiers within a Protocol
run and SHALL yield shared `SkippedRecord` for duplicates. Unusable discovery
entries SHALL be yielded as shared `RecordProcessingError`, not plugin-local
wrapper types.

#### Scenario: Duplicate identifier is skipped

- **WHEN** the same discovery `identifier` appears more than once in one run
- **THEN** subsequent occurrences are yielded as `SkippedRecord`

### Requirement: Keep Protocol independent of PayloadParser and DataMapper

The system SHALL keep Protocol implementations free of payload parsing and ARC
mapping logic. Protocols MAY produce typed discovery payloads (for example a
URL or an inline document) for parsers to consume.

#### Scenario: Protocol does not import mappers

- **WHEN** a Protocol implementation is loaded
- **THEN** it does not depend on DataMapper or PayloadParser registries to
  perform discovery
