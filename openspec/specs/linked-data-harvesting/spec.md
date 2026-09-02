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
The system SHALL require explicit `sitemap_type`, `dataset_type`, and `payload_type` values. Do not infer source formats automatically.

#### Scenario: Satisfies — Require explicit sitemap_type, dataset_type, and payload_type values. Do not infer…
- **WHEN** the conditions described by this requirement apply
- **THEN** Require explicit `sitemap_type`, `dataset_type`, and `payload_type` values. Do not infer source formats automatically

### Requirement: Implement LinkedDataPlugin(Plugin) in plugin.py; the central Harvester instantiates it with…
The system SHALL implement `LinkedDataPlugin(Plugin)` in `plugin.py`; the central Harvester instantiates it with the plugin config and invokes `run()` and `get_expected_datasets()` via the `Plugin` interface.

#### Scenario: Satisfies — Implement LinkedDataPlugin(Plugin) in plugin.py; the central Harvester instantiates it with…
- **WHEN** the conditions described by this requirement apply
- **THEN** Implement `LinkedDataPlugin(Plugin)` in `plugin.py`; the central Harvester instantiates it with the plugin config and invokes `run()` and `get_expected_datasets()` via the `Plugin` interface

### Requirement: Select implementations using registries for sitemap, dataset, and mapper types
The system SHALL select implementations using registries for sitemap, dataset, and mapper types.

#### Scenario: Satisfies — Select implementations using registries for sitemap, dataset, and mapper types
- **WHEN** the conditions described by this requirement apply
- **THEN** Select implementations using registries for sitemap, dataset, and mapper types

### Requirement: Validate config at startup and fail fast on unsupported enum…
The system SHALL validate config at startup and fail fast on unsupported enum values.

#### Scenario: Satisfies — Validate config at startup and fail fast on unsupported enum…
- **WHEN** the conditions described by this requirement apply
- **THEN** Validate config at startup and fail fast on unsupported enum values

### Requirement: Yield HarvestedArc, HarvesterError, or SkippedRecord for every dataset outcome
The system SHALL yield `HarvestedArc`, `HarvesterError`, or `SkippedRecord` for every dataset outcome (success, failure, or deliberate skip).

#### Scenario: Satisfies — Yield HarvestedArc, HarvesterError, or SkippedRecord for every dataset outcome
- **WHEN** the conditions described by this requirement apply
- **THEN** Yield `HarvestedArc`, `HarvesterError`, or `SkippedRecord` for every dataset outcome (success, failure, or deliberate skip)

### Requirement: Continue harvesting remaining datasets when a dataset-level failure occurs
The system SHALL continue harvesting remaining datasets when a dataset-level failure occurs.

#### Scenario: Satisfies — Continue harvesting remaining datasets when a dataset-level failure occurs
- **WHEN** the conditions described by this requirement apply
- **THEN** Continue harvesting remaining datasets when a dataset-level failure occurs

### Requirement: Ensure every yielded HarvesterError and SkippedRecord reaches the orchestrator so…
The system SHALL ensure that every yielded `HarvesterError` and `SkippedRecord` reaches the orchestrator so harvest-report counters and `fairagro:failures` stay complete; do not treat local logging as a substitute for yielding.

#### Scenario: Satisfies — Ensure every yielded HarvesterError and SkippedRecord reaches the orchestrator so…
- **WHEN** the conditions described by this requirement apply
- **THEN** Ensure every yielded `HarvesterError` and `SkippedRecord` reaches the orchestrator so harvest-report counters and `fairagro:failures` stay complete; do not treat local logging as a substitute for yielding

### Requirement: Edge case — - An empty sitemap must yield zero outputs and exit…
The system SHALL handle this edge case: when - An empty sitemap must yield zero outputs and exit cleanly. - Duplicate dataset URLs in a sitemap must be deduplicated before parsing. - Unsupported sitemap, dataset, or payload types must fail fast during validation. - Dataset-level parse or map failures must be emitted as errors and should not stop the overall harvest. - Malformed discovery entries that cannot be turned into a dataset must be yielded as `RecordProcessingError` (shared harvester type), not only logged inside the sitemap. - Duplicate discovery identifiers must be yielded as `SkippedRecord`, not as failures., then behaviour matches the documented outcome.

#### Scenario: Edge case — - An empty sitemap must yield zero outputs and exit…
- **WHEN** - An empty sitemap must yield zero outputs and exit cleanly. - Duplicate dataset URLs in a sitemap must be deduplicated before parsing. - Unsupported sitemap, dataset, or payload types must fail fast during validation. - Dataset-level parse or map failures must be emitted as errors and should not stop the overall harvest. - Malformed discovery entries that cannot be turned into a dataset must be yielded as `RecordProcessingError` (shared harvester type), not only logged inside the sitemap. - Duplicate discovery identifiers must be yielded as `SkippedRecord`, not as failures.
- **THEN** behaviour matches the documented outcome

### Requirement: Linked-data plugin MUST pass the discovered dataset URL into Schema.org mapping

When mapping a linked-data graph, the linked-data plugin MUST build a
`MappingContext` from discovery and pass it to `map_graph`. For
`UrlDiscoveryResult`, the context MUST include the discovered page URL as
`source_url` and MUST forward optional `harvest_source_id` when present so
Schema.org mapping can key `Investigation.identifier` to the harvest unit
without parsing URLs inside StableGraph. Inline discovery results without a
fetched URL MUST still pass an explicit `MappingContext()` (with null
`source_url` / `harvest_source_id`); callers MUST NOT omit the context argument.

#### Scenario: Discovery URL is available to the Schema.org mapper

- **WHEN** the plugin maps an HTML JSON-LD dataset discovered at a page URL
- **THEN** `map_graph` MUST receive a MappingContext whose `source_url` is that
  page URL

#### Scenario: Harvest source id from sitemap is forwarded to the mapper

- **WHEN** the plugin processes a `UrlDiscoveryResult` with `harvest_source_id`
  set (e.g. MyCoRe Solr `id`)
- **THEN** `map_graph` MUST receive a MappingContext carrying that
  `harvest_source_id`

#### Scenario: Inline discovery without URL uses empty MappingContext

- **WHEN** the plugin maps a dataset from an inline discovery result with no
  landing URL
- **THEN** `map_graph` MUST be called with an explicit `MappingContext()` whose
  `source_url` and `harvest_source_id` are null, and MUST NOT invent a fake URL
  solely to populate context

#### Scenario: No per-run DOI collision registry required

- **WHEN** a harvest run processes multiple Schema.org datasets including pages that share the same DOI
- **THEN** the plugin MUST NOT require a collect-then-map phase or colliding-DOI set; distinct harvest source ids or `source_url` values MUST yield distinct `Investigation.identifier` values via the mapper's harvest-source-first chain

### Requirement: Linked Data plugin bounds buffered mapped ARC payloads

The Linked Data plugin pipeline (`discovery → fetch/map → yield`) MUST bound
the number of completed mapped outcomes (`HarvestedArc`, `RecordProcessingError`,
or `SkippedRecord`) waiting between the worker stage and the consumer `yield`.
The bound MUST be tied to the configured worker concurrency
(`effective_worker_tasks`, derived from `max_connections`). At no time during
a normal harvest run SHALL more than **2 × `effective_worker_tasks`** mapped
outcomes reside in the plugin pipeline (in-flight worker tasks plus items
queued for yield).

#### Scenario: Slow consumer does not grow unbounded memory

- **WHEN** the plugin maps datasets faster than the orchestrator consumes
  yielded items (simulated slow consumer)
- **THEN** the number of mapped outcomes held inside the plugin pipeline MUST
  NOT exceed 2 × `effective_worker_tasks`

#### Scenario: Backpressure does not stall discovery permanently

- **WHEN** the consumer resumes after a slow period
- **THEN** the plugin MUST continue yielding remaining datasets in arrival order
  until discovery completes and all workers finish

### Requirement: Linked Data plugin stops promptly on generator close

When the plugin async generator is closed early (e.g. orchestrator
`aclose()` after upload abort or repository teardown), the plugin MUST stop
starting new worker tasks and MUST cancel in-flight producer and worker tasks
within a bounded shutdown window. The plugin MUST NOT continue mapping the
remainder of the catalog into an unread queue. Shutdown MUST NOT leave
unhandled exceptions on the asyncio event loop.

#### Scenario: Early aclose cancels remaining work

- **WHEN** the consumer takes one or more yielded items then closes the plugin
  generator while discovery would still produce many more datasets
- **THEN** further dataset mapping MUST stop without processing the full catalog
  AND the asyncio event loop MUST report no unhandled task exceptions

#### Scenario: Clean shutdown after full harvest is unchanged

- **WHEN** the consumer drains all yielded items until the generator completes
  normally
- **THEN** the plugin MUST exit cleanly with no cancellation side effects on
  the harvest report counters for items already yielded

## Feature split

- `openspec/specs/xml-sitemap-parser/spec.md` — XML sitemap discovery from a single sitemap URL and dataset URL extraction.
- `openspec/specs/sitemap-mycore-solr/spec.md` — MyCoRe Solr JSON discovery source; Solr pagination and `/receive/{id}` URL construction.
- `openspec/specs/linked-data-dataset-abstraction/spec.md` — Dataset payload abstraction and provider-specific dataset wrappers.
- `openspec/specs/html-jsonld-dataset/spec.md` — Dataset implementation that fetches an HTML page and extracts embedded JSON-LD.
- `openspec/specs/regal-jsonld/spec.md` — Regal `/find` discovery, inline Regal JSON-LD datasets, and Regal→ARC mapping.
- `openspec/specs/regal-to-arc-mapping/spec.md` — Regal ResearchData graph → ARC implementation contract (authoritative field rules in `docs/regal_mapping.md`).
- `openspec/specs/linked-data-mapper/spec.md` — Graph-to-ARC mapping and RO-Crate serialization.
