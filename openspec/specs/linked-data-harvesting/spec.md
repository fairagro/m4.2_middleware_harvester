# Linked Data Harvesting

## Purpose

Top-level plugin contract for the Linked Data harvester component.

This spec defines the plugin entrypoint, configuration contract, and implementation selection model. Concrete behavior is defined in specialized feature specs.

## Requirements

### Requirement: Provide a plugin-level Config class as a Pydantic BaseModel that…
The system SHALL provide a plugin-level `Config` class as a Pydantic `BaseModel` that is referenced by the main `middleware.harvester.config.Config` plugin config schema.

#### Scenario: Satisfies — Provide a plugin-level Config class as a Pydantic BaseModel that…
- **WHEN** the conditions described by this requirement apply
- **THEN** The system SHALL provide a plugin-level `Config` class as a Pydantic `BaseModel` that is referenced by the main `middleware.harvester.config.Config` plugin config schema

### Requirement: Require explicit sitemap_type, dataset_type, and payload_type values. Do not infer…
The system SHALL ensure that require explicit `sitemap_type`, `dataset_type`, and `payload_type` values. Do not infer source formats automatically.

#### Scenario: Satisfies — Require explicit sitemap_type, dataset_type, and payload_type values. Do not infer…
- **WHEN** the conditions described by this requirement apply
- **THEN** Require explicit `sitemap_type`, `dataset_type`, and `payload_type` values. Do not infer source formats automatically

### Requirement: Implement LinkedDataPlugin(Plugin) in plugin.py; the central Harvester instantiates it with…
The system SHALL ensure that implement `LinkedDataPlugin(Plugin)` in `plugin.py`; the central Harvester instantiates it with the plugin config and invokes `run()` and `get_expected_datasets()` via the `Plugin` interface.

#### Scenario: Satisfies — Implement LinkedDataPlugin(Plugin) in plugin.py; the central Harvester instantiates it with…
- **WHEN** the conditions described by this requirement apply
- **THEN** Implement `LinkedDataPlugin(Plugin)` in `plugin.py`; the central Harvester instantiates it with the plugin config and invokes `run()` and `get_expected_datasets()` via the `Plugin` interface

### Requirement: Select implementations using registries for sitemap, dataset, and mapper types
The system SHALL ensure that select implementations using registries for sitemap, dataset, and mapper types.

#### Scenario: Satisfies — Select implementations using registries for sitemap, dataset, and mapper types
- **WHEN** the conditions described by this requirement apply
- **THEN** Select implementations using registries for sitemap, dataset, and mapper types

### Requirement: Validate config at startup and fail fast on unsupported enum…
The system SHALL ensure that validate config at startup and fail fast on unsupported enum values.

#### Scenario: Satisfies — Validate config at startup and fail fast on unsupported enum…
- **WHEN** the conditions described by this requirement apply
- **THEN** Validate config at startup and fail fast on unsupported enum values

### Requirement: Yield HarvestedArc, HarvesterError, or SkippedRecord for every dataset outcome
The system SHALL yield `HarvestedArc`, `HarvesterError`, or `SkippedRecord` for every dataset outcome (success, failure, or deliberate skip).

#### Scenario: Satisfies — Yield HarvestedArc, HarvesterError, or SkippedRecord for every dataset outcome
- **WHEN** the conditions described by this requirement apply
- **THEN** Yield `HarvestedArc`, `HarvesterError`, or `SkippedRecord` for every dataset outcome (success, failure, or deliberate skip)

### Requirement: Continue harvesting remaining datasets when a dataset-level failure occurs
The system SHALL ensure that continue harvesting remaining datasets when a dataset-level failure occurs.

#### Scenario: Satisfies — Continue harvesting remaining datasets when a dataset-level failure occurs
- **WHEN** the conditions described by this requirement apply
- **THEN** Continue harvesting remaining datasets when a dataset-level failure occurs

### Requirement: Ensure every yielded HarvesterError and SkippedRecord reaches the orchestrator so…
The system SHALL ensure that ensure every yielded `HarvesterError` and `SkippedRecord` reaches the orchestrator so harvest-report counters and `fairagro:failedRecords` stay complete; do not treat local logging as a substitute for yielding.

#### Scenario: Satisfies — Ensure every yielded HarvesterError and SkippedRecord reaches the orchestrator so…
- **WHEN** the conditions described by this requirement apply
- **THEN** Ensure every yielded `HarvesterError` and `SkippedRecord` reaches the orchestrator so harvest-report counters and `fairagro:failedRecords` stay complete; do not treat local logging as a substitute for yielding

### Requirement: Edge case — - An empty sitemap must yield zero outputs and exit…
The system SHALL handle this edge case: when - An empty sitemap must yield zero outputs and exit cleanly. - Duplicate dataset URLs in a sitemap must be deduplicated before parsing. - Unsupported sitemap, dataset, or payload types must fail fast during validation. - Dataset-level parse or map failures must be emitted as errors and should not stop the overall harvest. - Malformed discovery entries that cannot be turned into a dataset must be yielded as `RecordProcessingError` (shared harvester type), not only logged inside the sitemap. - Duplicate discovery identifiers must be yielded as `SkippedRecord`, not as failures., then behaviour matches the documented outcome.

#### Scenario: Edge case — - An empty sitemap must yield zero outputs and exit…
- **WHEN** - An empty sitemap must yield zero outputs and exit cleanly. - Duplicate dataset URLs in a sitemap must be deduplicated before parsing. - Unsupported sitemap, dataset, or payload types must fail fast during validation. - Dataset-level parse or map failures must be emitted as errors and should not stop the overall harvest. - Malformed discovery entries that cannot be turned into a dataset must be yielded as `RecordProcessingError` (shared harvester type), not only logged inside the sitemap. - Duplicate discovery identifiers must be yielded as `SkippedRecord`, not as failures.
- **THEN** behaviour matches the documented outcome

## Feature split

- `openspec/specs/xml-sitemap-parser/spec.md` — XML sitemap discovery from a single sitemap URL and dataset URL extraction.
- `openspec/specs/sitemap-mycore-solr/spec.md` — MyCoRe Solr JSON discovery source; Solr pagination and `/receive/{id}` URL construction.
- `openspec/specs/linked-data-dataset-abstraction/spec.md` — Dataset payload abstraction and provider-specific dataset wrappers.
- `openspec/specs/html-jsonld-dataset/spec.md` — Dataset implementation that fetches an HTML page and extracts embedded JSON-LD.
- `openspec/specs/regal-jsonld/spec.md` — Regal `/find` discovery, inline Regal JSON-LD datasets, and Regal→ARC mapping.
- `openspec/specs/regal-to-arc-mapping/spec.md` — Regal ResearchData graph → ARC implementation contract (authoritative field rules in `docs/regal_mapping.md`).
- `openspec/specs/linked-data-mapper/spec.md` — Graph-to-ARC mapping and RO-Crate serialization.
