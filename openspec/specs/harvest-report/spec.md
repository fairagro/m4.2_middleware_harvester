# Harvest Report

## Purpose

At the end of each harvester run, the orchestrator emits a machine-readable
summary of the completed harvest to **stdout** as a JSON-LD document.  The
document describes every repository that was processed, including timing,
expected dataset count, outcome statistics, and a per-record failure list.

## Requirements

### Requirement: After all repository tasks finish (whether they succeed or fail),…
The system SHALL ensure that after all repository tasks finish (whether they succeed or fail), the.

#### Scenario: Satisfies — After all repository tasks finish (whether they succeed or fail),…
- **WHEN** the conditions described by this requirement apply
- **THEN** After all repository tasks finish (whether they succeed or fail), the

### Requirement: RepositoryReport captures:
The system SHALL ensure that `RepositoryReport` captures:.

#### Scenario: Satisfies — RepositoryReport captures:
- **WHEN** the conditions described by this requirement apply
- **THEN** `RepositoryReport` captures:

### Requirement: HarvestReport captures:
The system SHALL ensure that `HarvestReport` captures:.

#### Scenario: Satisfies — HarvestReport captures:
- **WHEN** the conditions described by this requirement apply
- **THEN** `HarvestReport` captures:

### Requirement: The report is serialised as JSON-LD and printed to **stdout**…
The report SHALL be serialised as JSON-LD and printed to **stdout** (not to the.

#### Scenario: Satisfies — The report is serialised as JSON-LD and printed to **stdout**…
- **WHEN** the conditions described by this requirement apply
- **THEN** The report is serialised as JSON-LD and printed to **stdout** (not to the

### Requirement: The JSON-LD document uses https://schema.org/ as its primary
The JSON-LD document SHALL use `https://schema.org/` as its primary.

#### Scenario: Satisfies — The JSON-LD document uses https://schema.org/ as its primary
- **WHEN** the conditions described by this requirement apply
- **THEN** The JSON-LD document uses `https://schema.org/` as its primary

### Requirement: The JSON-LD document uses an additional fairagro: prefix
The JSON-LD document SHALL use an additional `fairagro:` prefix.

#### Scenario: Satisfies — The JSON-LD document uses an additional fairagro: prefix
- **WHEN** the conditions described by this requirement apply
- **THEN** The JSON-LD document uses an additional `fairagro:` prefix

### Requirement: Every yielded HarvesterError increments failed_datasets and appends
The system SHALL ensure that every yielded `HarvesterError` increments `failed_datasets` and appends.

#### Scenario: Satisfies — Every yielded HarvesterError increments failed_datasets and appends
- **WHEN** the conditions described by this requirement apply
- **THEN** Every yielded `HarvesterError` increments `failed_datasets` and appends

### Requirement: Schema:startTime and schema:endTime on the top-level Action are
The system SHALL ensure that `schema:startTime` and `schema:endTime` on the top-level `Action` are.

#### Scenario: Satisfies — Schema:startTime and schema:endTime on the top-level Action are
- **WHEN** the conditions described by this requirement apply
- **THEN** `schema:startTime` and `schema:endTime` on the top-level `Action` are

### Requirement: Schema:duration on each repository entry is an ISO 8601 duration…
The system SHALL ensure that `schema:duration` on each repository entry is an ISO 8601 duration string.

#### Scenario: Satisfies — Schema:duration on each repository entry is an ISO 8601 duration…
- **WHEN** the conditions described by this requirement apply
- **THEN** `schema:duration` on each repository entry is an ISO 8601 duration string

### Requirement: Printing the report must not raise; if serialisation fails for…
The system SHALL ensure that printing the report must not raise; if serialisation fails for any reason.

#### Scenario: Satisfies — Printing the report must not raise; if serialisation fails for…
- **WHEN** the conditions described by this requirement apply
- **THEN** Printing the report must not raise; if serialisation fails for any reason

### Requirement: The report is printed **after** tracing shutdown has been initiated…
The report SHALL be printed **after** tracing shutdown has been initiated so.

#### Scenario: Satisfies — The report is printed **after** tracing shutdown has been initiated…
- **WHEN** the conditions described by this requirement apply
- **THEN** The report is printed **after** tracing shutdown has been initiated so

### Requirement: Edge case — Repository task raised an unhandled exception
The system SHALL handle this edge case: when Repository task raised an unhandled exception, then `harvest_id` is the created harvest id when recoverable (e.g. from the failing `/v3/harvests/{id}/…` request URL), otherwise `None`; `failed_datasets` equals `expected_datasets` if known, otherwise `None`; `failed_records` contains at least one entry describing the repository-level failure.

#### Scenario: Edge case — Repository task raised an unhandled exception
- **WHEN** Repository task raised an unhandled exception
- **THEN** `harvest_id` is the created harvest id when recoverable (e.g. from the failing `/v3/harvests/{id}/…` request URL), otherwise `None`; `failed_datasets` equals `expected_datasets` if known, otherwise `None`; `failed_records` contains at least one entry describing the repository-level failure

### Requirement: Edge case — Get_expected_datasets() returned None
The system SHALL handle this edge case: when `get_expected_datasets()` returned `None`, then `expected_datasets` is omitted from the JSON-LD output (the key is not emitted rather than set to `null`).

#### Scenario: Edge case — Get_expected_datasets() returned None
- **WHEN** `get_expected_datasets()` returned `None`
- **THEN** `expected_datasets` is omitted from the JSON-LD output (the key is not emitted rather than set to `null`)

### Requirement: Edge case — No failed records for a repository
The system SHALL handle this edge case: when No failed records for a repository, then omit `fairagro:failedRecords` (do not emit an empty array).

#### Scenario: Edge case — No failed records for a repository
- **WHEN** No failed records for a repository
- **THEN** omit `fairagro:failedRecords` (do not emit an empty array)

### Requirement: Edge case — No repositories configured
The system SHALL handle this edge case: when No repositories configured, then an `Action` with an empty `result` array and a zero-duration is emitted.

#### Scenario: Edge case — No repositories configured
- **WHEN** No repositories configured
- **THEN** an `Action` with an empty `result` array and a zero-duration is emitted

### Requirement: Edge case — Serialisation of the report raises
The system SHALL handle this edge case: when Serialisation of the report raises, then a single `WARNING` log line is emitted; the harvester exits with the same code it would have used otherwise.

#### Scenario: Edge case — Serialisation of the report raises
- **WHEN** Serialisation of the report raises
- **THEN** a single `WARNING` log line is emitted; the harvester exits with the same code it would have used otherwise
