# Harvest Report

## Purpose

At the end of each harvester run, the orchestrator emits an operator-facing
harvest summary to **stdout**. The report **domain model, counting API,
JSON-LD shape, and vocabulary** are defined and owned by
[`fairagro/m4.2_advanced_middleware_api`](https://github.com/fairagro/m4.2_advanced_middleware_api)
(`middleware.shared.report` in `fairagro-middleware-shared`).

This domain only specifies how the harvester **drives and emits** that shared
report. Do not restate the shared contract here — read the API repository’s
OpenSpec `harvest-report` capability and `ns/harvest-report/v1/`.

## Requirements

### Requirement: Use the shared report counting API

The harvester MUST create a mutable `HarvestReport` at the start of the run,
open one `RepositoryScope` per configured repository, invoke the shared
counting methods on that scope for harvest events, call `finish()` when the
run ends, and render with `JsonLdReportSerializer`. It MUST NOT maintain
parallel counters for harvested, failed, skipped, expected, study, or assay
statistics, and MUST NOT duplicate the report domain model or JSON-LD
serializer.

#### Scenario: Event updates go through the scope

- **GIVEN** an open `RepositoryScope` for a repository
- **WHEN** a dataset is harvested, fails, or is skipped
- **THEN** the orchestrator calls `record_harvested`, `record_failed`, or
  `record_skipped` on that scope (and does not later copy a separate counter
  into the report)

### Requirement: One repository scope per configured repository

After all repository tasks finish (whether they succeed or fail), the
finished `HarvestReport` MUST contain exactly one repository scope snapshot
per configured repository.

#### Scenario: Successful and failed repositories both produce entries

- **WHEN** the harvest run finishes with a mix of successful and failed
  repository tasks
- **THEN** `HarvestReport.repository_reports` has exactly one entry per
  configured repository

#### Scenario: Gather escape does not duplicate a scope

- **GIVEN** `run_repository` already opened a scope for an RDI
- **WHEN** the task still surfaces a `BaseException` to `asyncio.gather`
- **THEN** the orchestrator MUST NOT call `open_repository` again for that RDI
  (one report entry; failure already recorded on the original scope when the
  exception escaped after the scope was opened)

### Requirement: Drive shared fields from the live harvest

For each repository the orchestrator MUST:

- open the scope with the repository RDI
- call `set_expected_datasets` when `Plugin.get_expected_datasets()` returns a
  value
- call `set_harvest_id` when a harvest id is known (including recovery from a
  post-create API failure)
- call `record_failed` for each per-item API error, then `record_harvested`
  once per remaining submitted ARC (`submitted - len(errors)`) after
  `harvest_arcs` returns. On catastrophic upload abort, count each submitted
  ARC as failed instead (or one failure if none were submitted)
- call `record_failed` for each plugin `HarvesterError` (with optional record
  id / URL)
- call `record_skipped` for each yielded `SkippedRecord` (see also
  [`skipped-datasets`](../skipped-datasets/))
- call `add_studies` / `add_assays` with the composition counts carried on each
  yielded `HarvestedArc` (plugins set these from the arctrl ARC object before
  serialization; no JSON re-parse in the orchestrator)

#### Scenario: Sum studies and assays from harvested ARCs

- **GIVEN** two successfully uploaded ARCs containing one Study and one Assay
  each
- **WHEN** the repository scope is snapshotted after the run
- **THEN** `total_studies` is 2 and `total_assays` is 2

#### Scenario: API duplicate does not count as harvested

- **GIVEN** two ARCs submitted and one per-item API duplicate error
- **WHEN** upload outcomes are recorded
- **THEN** `record_harvested` is called once and `record_failed` once

#### Scenario: Plugin yields a HarvesterError

- **WHEN** the plugin stream yields a `HarvesterError`
- **THEN** the orchestrator calls `record_failed` on the repository scope

### Requirement: Print after tracing shutdown via JsonLdReportSerializer

The orchestrator MUST serialize the finished report with
`JsonLdReportSerializer().render(report)` and print the resulting string to
stdout **after** tracing shutdown has been initiated. Serialization or print
failures MUST be logged and MUST NOT change the process exit code.

#### Scenario: Ordering relative to OTLP shutdown

- **WHEN** the harvester process is shutting down after a completed run
- **THEN** tracing shutdown is initiated before the JSON-LD report is printed

### Requirement: Edge case — unhandled repository exception

When a repository task raises an unhandled exception, `harvest_id` MUST be the
created harvest id when recoverable, otherwise unset; the scope MUST record at
least one failure describing the repository-level error.

#### Scenario: Unhandled exception after harvest creation

- **WHEN** a repository task fails after a harvest id is known
- **THEN** the repository scope retains that `harvest_id` and records the
  failure via `record_failed`

### Requirement: Edge case — unknown plugin type

When `PLUGIN_FACTORIES` has no entry for `repo.plugin_type`, the repository
scope MUST record one failure describing the unknown type (so the report does
not look like an empty success) and MUST NOT call the API client.

#### Scenario: Unknown plugin type

- **WHEN** `run_repository` is called with an unrecognised `plugin_type`
- **THEN** the scope records one `record_failed` and `harvest_arcs` is not
  invoked
