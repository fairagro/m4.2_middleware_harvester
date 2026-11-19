# Spec Delta

## ADDED Requirements

### Requirement: Drive record_warning from HarvestedArc warnings

When the plugin stream yields a `HarvestedArc` that carries one or more dataset warnings, the orchestrator MUST call
`RepositoryScope.record_warning` once per warning message, passing the ARC's identifier as `record_id` when present and
its `source_url` as `url` when present. Those calls MUST NOT change harvested, failed, or skipped counts. Empty warning
lists MUST result in zero `record_warning` calls for that ARC.

#### Scenario: Yielded ARC with one warning

- **GIVEN** a plugin yields a `HarvestedArc` with one warning message and a non-empty identifier and source URL
- **WHEN** `arc_stream` consumes that item
- **THEN** `record_warning` is called once with that message, `record_id`, and `url`
- **AND** harvested / failed / skipped counts are unchanged by that call

#### Scenario: Yielded ARC with no warnings

- **GIVEN** a plugin yields a `HarvestedArc` with an empty warning list
- **WHEN** `arc_stream` consumes that item
- **THEN** `record_warning` is not called for that ARC

#### Scenario: Multiple warnings on one ARC

- **GIVEN** a plugin yields a `HarvestedArc` with two distinct warning messages
- **WHEN** `arc_stream` consumes that item
- **THEN** `record_warning` is called twice (one call per message), still without changing harvest/fail/skip counts

## MODIFIED Requirements

### Requirement: Drive shared fields from the live harvest

For each repository the orchestrator MUST:

- open the scope with the repository RDI
- call `set_expected_datasets` when `Plugin.get_expected_datasets()` returns a value
- call `set_harvest_id` when a harvest id is known (including recovery from a post-create API failure)
- call `record_failed` for each per-item API error, then `record_harvested` once per remaining submitted ARC
  (`submitted - len(errors)`) after `harvest_arcs` returns. On catastrophic upload abort: call `record_failed` once per
  submitted ARC; if none were submitted, call `record_repository_issue` once instead
- call `record_failed` for each plugin `RecordProcessingError` (with optional record id / URL)
- call `record_repository_issue` for other plugin `HarvesterError` values that are not tied to a single dataset (e.g.
  sitemap/discovery failures)
- call `record_skipped` for each yielded `SkippedRecord` (see also [`skipped-datasets`](../skipped-datasets/))
- call `record_warning` for each dataset warning carried on a yielded `HarvestedArc` (see "Drive record_warning from
  HarvestedArc warnings")
- call `add_studies` / `add_assays` with the composition counts carried on each yielded `HarvestedArc` (plugins set
  these from the arctrl ARC object before serialization; no JSON re-parse in the orchestrator)

#### Scenario: Sum studies and assays from harvested ARCs

- **GIVEN** two successfully uploaded ARCs containing one Study and one Assay each
- **WHEN** the repository scope is snapshotted after the run
- **THEN** `total_studies` is 2 and `total_assays` is 2

#### Scenario: API duplicate does not count as harvested

- **GIVEN** two ARCs submitted and one per-item API duplicate error
- **WHEN** upload outcomes are recorded
- **THEN** `record_harvested` is called once and `record_failed` once

#### Scenario: Plugin yields a RecordProcessingError

- **WHEN** the plugin stream yields a `RecordProcessingError`
- **THEN** the orchestrator calls `record_failed` on the repository scope

#### Scenario: Plugin yields a non-record HarvesterError

- **WHEN** the plugin stream yields a `HarvesterError` that is not a `RecordProcessingError` (e.g. sitemap discovery
  failure)
- **THEN** the orchestrator calls `record_repository_issue` and `failed_datasets` is unchanged

#### Scenario: Plugin yields HarvestedArc with warnings

- **WHEN** the plugin stream yields a `HarvestedArc` that carries dataset warnings
- **THEN** the orchestrator calls `record_warning` for each warning before or while submitting the ARC for upload
- **AND** those calls do not substitute for `record_harvested` / `record_failed` / `record_skipped`
