# Skipped Datasets

## Purpose

Plugins may deliberately skip individual records (e.g. duplicate discovery
entries) without treating them as failures. Skips are counted separately from
errors in the shared harvest report so operators can distinguish intentional
omissions from real failures.

## Requirements

### Requirement: SkippedRecord signal type

The system SHALL provide a `SkippedRecord` class in
`middleware.harvester.errors` that carries a human-readable `reason` and an
optional `url`.

#### Scenario: Class is available to plugins and orchestrator

- **WHEN** a plugin or the orchestrator needs to signal a deliberate skip
- **THEN** it uses `SkippedRecord` from `middleware.harvester.errors`

### Requirement: SkippedRecord is not a HarvesterError

`SkippedRecord` MUST NOT be a subclass of `HarvesterError` and MUST NOT be an
exception type. It is a distinct, non-exception signal value that is yielded,
never raised, for deliberate skips.

#### Scenario: Type distinction from failures

- **WHEN** code inspects `SkippedRecord` relative to `HarvesterError`
- **THEN** `issubclass(SkippedRecord, HarvesterError)` is false and
  `SkippedRecord` is not an `Exception` subclass

### Requirement: Plugin contract includes SkippedRecord

`Plugin.run()` MUST return
`AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None]`. Plugins
that never yield `SkippedRecord` remain valid.

#### Scenario: Three-way yield union

- **WHEN** a plugin implements `run()`
- **THEN** its return type admits `HarvestedArc`, `HarvesterError`, and
  `SkippedRecord`

### Requirement: Orchestrator counts each SkippedRecord

When `arc_stream` receives a `SkippedRecord`, the orchestrator MUST call
`RepositoryScope.record_skipped()` and MUST NOT submit that item to
`harvest_arcs` or count it as harvested or failed.

#### Scenario: Skip increments skipped_datasets only

- **GIVEN** a plugin yields one `SkippedRecord` and one `HarvestedArc`
- **WHEN** the repository run completes successfully
- **THEN** `skipped_datasets` is 1, the ARC is uploaded, and
  `failed_datasets` is not increased by the skip

### Requirement: Skips are logged at INFO

The orchestrator MUST log each skipped record at INFO level (not ERROR or
WARNING), including the repository RDI and the skip reason (and URL when
present).

#### Scenario: INFO log for a skip

- **WHEN** `arc_stream` handles a `SkippedRecord` with a URL
- **THEN** an INFO log entry is emitted for that repository, skip reason, and
  URL

### Requirement: skipped_datasets is always present on the repository report

The shared `RepositoryReport` MUST include `skipped_datasets: int` with default
`0`. The JSON-LD serializer MUST always emit `fairagro:skippedDatasets` for
every repository entry, including when the value is `0`.

#### Scenario: Zero skips still emit the field

- **WHEN** a repository run finishes with no `SkippedRecord` yields
- **THEN** `skipped_datasets` is `0` and `fairagro:skippedDatasets` is present
  in the JSON-LD output with value `0`

### Requirement: linked_data yields SkippedRecord for duplicate discovery

The linked_data plugin MUST yield `SkippedRecord` (not `HarvesterError`) when
discovery deduplication skips a duplicate identifier or URL.

#### Scenario: Duplicate sitemap / discovery id

- **WHEN** the same discovery identity appears more than once in a harvest run
- **THEN** subsequent occurrences are yielded as `SkippedRecord` and counted
  toward `skipped_datasets`

### Requirement: Edge case — unhandled repository exception

When a repository task raises an unhandled exception before any skips are
recorded, `skipped_datasets` for that repository MUST be `0`.

#### Scenario: Crash before any skip

- **WHEN** a repository task fails with no prior `SkippedRecord` yields
- **THEN** the repository report entry has `skipped_datasets == 0`
