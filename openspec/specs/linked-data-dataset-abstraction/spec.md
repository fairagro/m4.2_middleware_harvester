# Linked Data Dataset Abstraction

## Purpose

Abstract payload handling for individual dataset records discovered during Linked Data harvesting.

## Requirements

### Requirement: Provide a Dataset interface that exposes a stable identifier and…
The system SHALL provide a `Dataset` interface that exposes a stable identifier and an async `to_graph()` method returning an `rdflib.Graph`.

#### Scenario: Satisfies — Provide a Dataset interface that exposes a stable identifier and…
- **WHEN** the conditions described by this requirement apply
- **THEN** The system SHALL provide a `Dataset` interface that exposes a stable identifier and an async `to_graph()` method returning an `rdflib.Graph`

### Requirement: Provide a Dataset.from_discovery_result(result: DiscoveryResult, client: NiceHttpClient | None, config: Config)…
The system SHALL provide a `Dataset.from_discovery_result(result: DiscoveryResult, client: NiceHttpClient | None, config: Config) -> Dataset` class method so the plugin can construct dataset instances from raw discovery results. `client` may be `None` for dataset implementations that do not make HTTP requests; implementations that require HTTP access must raise a descriptive error when `client` is `None`.

#### Scenario: Satisfies — Provide a Dataset.from_discovery_result(result: DiscoveryResult, client: NiceHttpClient | None, config: Config)…
- **WHEN** the conditions described by this requirement apply
- **THEN** The system SHALL provide a `Dataset.from_discovery_result(result: DiscoveryResult, client: NiceHttpClient | None, config: Config) -> Dataset` class method so the plugin can construct dataset instances from raw discovery results. `client` may be `None` for dataset implementations that do not make HTTP requests; implementations that require HTTP access must raise a descriptive error when `client` is `None`

### Requirement: Keep dataset wrappers independent of sitemap discovery and HTTP fetching
The system SHALL keep dataset wrappers independent of sitemap discovery and HTTP fetching.

#### Scenario: Satisfies — Keep dataset wrappers independent of sitemap discovery and HTTP fetching
- **WHEN** the conditions described by this requirement apply
- **THEN** Keep dataset wrappers independent of sitemap discovery and HTTP fetching

### Requirement: Use the dataset identifier as the stable key for error…
The system SHALL use the dataset identifier as the stable key for error reporting and downstream mapping.

#### Scenario: Satisfies — Use the dataset identifier as the stable key for error…
- **WHEN** the conditions described by this requirement apply
- **THEN** Use the dataset identifier as the stable key for error reporting and downstream mapping

### Requirement: Require every successful DiscoveryResult to expose a stable identifier used…
The system SHALL require every successful `DiscoveryResult` to expose a stable `identifier` used for sitemap-level deduplication.

#### Scenario: Satisfies — Require every successful DiscoveryResult to expose a stable identifier used…
- **WHEN** the conditions described by this requirement apply
- **THEN** Require every successful `DiscoveryResult` to expose a stable `identifier` used for sitemap-level deduplication

### Requirement: Deduplicate successful discovery identifiers in Sitemap.discover() and yield shared SkippedRecord…
The system SHALL deduplicate successful discovery identifiers in `Sitemap.discover()` and yield shared `SkippedRecord` (not a plugin-local duplicate type).

#### Scenario: Satisfies — Deduplicate successful discovery identifiers in Sitemap.discover() and yield shared SkippedRecord…
- **WHEN** the conditions described by this requirement apply
- **THEN** Deduplicate successful discovery identifiers in `Sitemap.discover()` and yield shared `SkippedRecord` (not a plugin-local duplicate type)

### Requirement: Yield shared RecordProcessingError for unusable discovery entries (missing id, non-object…
The system SHALL yield shared `RecordProcessingError` for unusable discovery entries (missing id, non-object payload, empty loc, …)—same type as inspire; do not introduce a plugin-local failure wrapper.

#### Scenario: Satisfies — Yield shared RecordProcessingError for unusable discovery entries (missing id, non-object…
- **WHEN** the conditions described by this requirement apply
- **THEN** Yield shared `RecordProcessingError` for unusable discovery entries (missing id, non-object payload, empty loc, …)—same type as inspire; do not introduce a plugin-local failure wrapper

### Requirement: Have the plugin forward RecordProcessingError and SkippedRecord from discovery to…
The system SHALL have the plugin forward `RecordProcessingError` and `SkippedRecord` from discovery to the orchestrator unchanged.

#### Scenario: Satisfies — Have the plugin forward RecordProcessingError and SkippedRecord from discovery to…
- **WHEN** the conditions described by this requirement apply
- **THEN** Have the plugin forward `RecordProcessingError` and `SkippedRecord` from discovery to the orchestrator unchanged

### Requirement: Edge case — - A dataset implementation receiving an unsupported DiscoveryResult subtype
The system SHALL handle this edge case: when - A dataset implementation receiving an unsupported `DiscoveryResult` subtype, then raise a descriptive error. - A dataset implementation must not perform top-level plugin orchestration. - Discovery failure with no stable `@id` → still yield `RecordProcessingError` with a descriptive reason and a synthetic key (e.g. page offset + array index) so `fairagro:failedRecords` can list it.

#### Scenario: Edge case — - A dataset implementation receiving an unsupported DiscoveryResult subtype
- **WHEN** - A dataset implementation receiving an unsupported `DiscoveryResult` subtype
- **THEN** raise a descriptive error. - A dataset implementation must not perform top-level plugin orchestration. - Discovery failure with no stable `@id` → still yield `RecordProcessingError` with a descriptive reason and a synthetic key (e.g. page offset + array index) so `fairagro:failedRecords` can list it
