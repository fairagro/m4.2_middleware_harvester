# Skipped Datasets

## Purpose

Plugins may deliberately skip individual records (e.g. duplicate sitemap
entries) without treating them as errors.  These skips are counted separately
in the harvest report so operators can distinguish between real failures and
intentional omissions.

## Requirements

### Requirement: A new SkippedRecord class exists in middleware.harvester.errors
The system SHALL ensure that a new `SkippedRecord` class exists in `middleware.harvester.errors`.

#### Scenario: Satisfies — A new SkippedRecord class exists in middleware.harvester.errors
- **WHEN** the conditions described by this requirement apply
- **THEN** A new `SkippedRecord` class exists in `middleware.harvester.errors`

### Requirement: SkippedRecord is **not** a subclass of HarvesterError; it is a
The system SHALL ensure that `SkippedRecord` is **not** a subclass of `HarvesterError`; it is a.

#### Scenario: Satisfies — SkippedRecord is **not** a subclass of HarvesterError; it is a
- **WHEN** the conditions described by this requirement apply
- **THEN** `SkippedRecord` is **not** a subclass of `HarvesterError`; it is a

### Requirement: The plugin contract (Plugin.run()) yields
The system SHALL ensure that the plugin contract (`Plugin.run()`) yields.

#### Scenario: Satisfies — The plugin contract (Plugin.run()) yields
- **WHEN** the conditions described by this requirement apply
- **THEN** The plugin contract (`Plugin.run()`) yields

### Requirement: The orchestrator (_arc_stream) counts every SkippedRecord instance
The system SHALL ensure that the orchestrator (`_arc_stream`) counts every `SkippedRecord` instance.

#### Scenario: Satisfies — The orchestrator (_arc_stream) counts every SkippedRecord instance
- **WHEN** the conditions described by this requirement apply
- **THEN** The orchestrator (`_arc_stream`) counts every `SkippedRecord` instance

### Requirement: A skipped record is logged at **INFO** level (not ERROR),…
The system SHALL ensure that a skipped record is logged at **INFO** level (not ERROR), including the.

#### Scenario: Satisfies — A skipped record is logged at **INFO** level (not ERROR),…
- **WHEN** the conditions described by this requirement apply
- **THEN** A skipped record is logged at **INFO** level (not ERROR), including the

### Requirement: RepositoryReport includes a skipped_datasets: int field (always
The system SHALL ensure that `RepositoryReport` includes a `skipped_datasets: int` field (always.

#### Scenario: Satisfies — RepositoryReport includes a skipped_datasets: int field (always
- **WHEN** the conditions described by this requirement apply
- **THEN** `RepositoryReport` includes a `skipped_datasets: int` field (always

### Requirement: The JSON-LD harvest report includes fairagro:skippedDatasets for every
The system SHALL ensure that the JSON-LD harvest report includes `fairagro:skippedDatasets` for every.

#### Scenario: Satisfies — The JSON-LD harvest report includes fairagro:skippedDatasets for every
- **WHEN** the conditions described by this requirement apply
- **THEN** The JSON-LD harvest report includes `fairagro:skippedDatasets` for every

### Requirement: The linked_data plugin yields SkippedRecord for duplicate discovery
The linked_data plugin SHALL yield `SkippedRecord` for duplicate discovery.

#### Scenario: Satisfies — The linked_data plugin yields SkippedRecord for duplicate discovery
- **WHEN** the conditions described by this requirement apply
- **THEN** The linked_data plugin yields `SkippedRecord` for duplicate discovery

### Requirement: Edge case — - skipped_datasets is always emitted in the JSON-LD output, including…
The system SHALL handle this edge case: when - `skipped_datasets` is always emitted in the JSON-LD output, including when it is `0` — unlike `expectedDatasets`, which may be unknown and is omitted when `None`. - A plugin that never yields `SkippedRecord` requires no change; the field defaults to `0`. - A repository task that raises an unhandled exception, then `skipped_datasets` is `0` (no skips were recorded before the crash).

#### Scenario: Edge case — - skipped_datasets is always emitted in the JSON-LD output, including…
- **WHEN** - `skipped_datasets` is always emitted in the JSON-LD output, including when it is `0` — unlike `expectedDatasets`, which may be unknown and is omitted when `None`. - A plugin that never yields `SkippedRecord` requires no change; the field defaults to `0`. - A repository task that raises an unhandled exception
- **THEN** `skipped_datasets` is `0` (no skips were recorded before the crash)
