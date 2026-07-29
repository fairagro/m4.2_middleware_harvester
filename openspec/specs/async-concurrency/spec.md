# Async Concurrency

## Purpose

The harvester and its plugins perform I/O-bound operations (HTTP fetches, API
uploads). All I/O must be non-blocking on the event loop, and independent
operations must run concurrently to overlap network latency.

## Requirements

### Requirement: No synchronous blocking call (network I/O, file I/O, or CPU-bound…
The system SHALL ensure that no synchronous blocking call (network I/O, file I/O, or CPU-bound work.

#### Scenario: Satisfies — No synchronous blocking call (network I/O, file I/O, or CPU-bound…
- **WHEN** the conditions described by this requirement apply
- **THEN** No synchronous blocking call (network I/O, file I/O, or CPU-bound work

### Requirement: CSWClient offloads every OWSLib call (CatalogueServiceWeb.__init__,
The system SHALL ensure that `CSWClient` offloads every OWSLib call (`CatalogueServiceWeb.__init__`,.

#### Scenario: Satisfies — CSWClient offloads every OWSLib call (CatalogueServiceWeb.__init__,
- **WHEN** the conditions described by this requirement apply
- **THEN** `CSWClient` offloads every OWSLib call (`CatalogueServiceWeb.__init__`,

### Requirement: HtmlJsonLdDataset.to_graph() offloads JSON-LD parsing
The system SHALL ensure that `HtmlJsonLdDataset.to_graph()` offloads JSON-LD parsing.

#### Scenario: Satisfies — HtmlJsonLdDataset.to_graph() offloads JSON-LD parsing
- **WHEN** the conditions described by this requirement apply
- **THEN** `HtmlJsonLdDataset.to_graph()` offloads JSON-LD parsing

### Requirement: The Linked Data plugin fetches multiple dataset URLs concurrently,
The Linked Data plugin SHALL fetch multiple dataset URLs concurrently,.

#### Scenario: Satisfies — The Linked Data plugin fetches multiple dataset URLs concurrently,
- **WHEN** the conditions described by this requirement apply
- **THEN** The Linked Data plugin fetches multiple dataset URLs concurrently,

### Requirement: The concurrency limit for dataset fetching uses the same max_connections
The concurrency limit for dataset fetching SHALL use the same `max_connections`.

#### Scenario: Satisfies — The concurrency limit for dataset fetching uses the same max_connections
- **WHEN** the conditions described by this requirement apply
- **THEN** The concurrency limit for dataset fetching uses the same `max_connections`

### Requirement: A dataset fetch failure is caught per task and converted…
The system SHALL ensure that a dataset fetch failure is caught per task and converted to a.

#### Scenario: Satisfies — A dataset fetch failure is caught per task and converted…
- **WHEN** the conditions described by this requirement apply
- **THEN** A dataset fetch failure is caught per task and converted to a

### Requirement: Results are yielded in arrival order (first completed, first yielded),
The system SHALL ensure that results are yielded in arrival order (first completed, first yielded),.

#### Scenario: Satisfies — Results are yielded in arrival order (first completed, first yielded),
- **WHEN** the conditions described by this requirement apply
- **THEN** Results are yielded in arrival order (first completed, first yielded),

### Requirement: The orchestrator processes all configured repositories concurrently via
The orchestrator SHALL process all configured repositories concurrently via.

#### Scenario: Satisfies — The orchestrator processes all configured repositories concurrently via
- **WHEN** the conditions described by this requirement apply
- **THEN** The orchestrator processes all configured repositories concurrently via

### Requirement: A failure in one repository sets its plugin_run OTLP span…
The system SHALL ensure that a failure in one repository sets its `plugin_run` OTLP span to ERROR and.

#### Scenario: Satisfies — A failure in one repository sets its plugin_run OTLP span…
- **WHEN** the conditions described by this requirement apply
- **THEN** A failure in one repository sets its `plugin_run` OTLP span to ERROR and

### Requirement: For each repository, the orchestrator calls
The system SHALL ensure that for each repository, the orchestrator calls.

#### Scenario: Satisfies — For each repository, the orchestrator calls
- **WHEN** the conditions described by this requirement apply
- **THEN** For each repository, the orchestrator calls

### Requirement: Arc_stream is a thin filter async generator that passes through…
The system SHALL ensure that `arc_stream` is a thin filter async generator that passes through `str`.

#### Scenario: Satisfies — Arc_stream is a thin filter async generator that passes through…
- **WHEN** the conditions described by this requirement apply
- **THEN** `arc_stream` is a thin filter async generator that passes through `str`

### Requirement: When the source protocol reports a total record count upfront
The system SHALL ensure that when the source protocol reports a total record count upfront.

#### Scenario: Satisfies — When the source protocol reports a total record count upfront
- **WHEN** the conditions described by this requirement apply
- **THEN** When the source protocol reports a total record count upfront

### Requirement: When the total count is not known upfront (XML sitemap,…
The system SHALL ensure that when the total count is not known upfront (XML sitemap, general.

#### Scenario: Satisfies — When the total count is not known upfront (XML sitemap,…
- **WHEN** the conditions described by this requirement apply
- **THEN** When the total count is not known upfront (XML sitemap, general

### Requirement: Per-record arc_upload OTLP spans are not emitted; the harvest_arcs
The system SHALL ensure that per-record `arc_upload` OTLP spans are not emitted; the `harvest_arcs`.

#### Scenario: Satisfies — Per-record arc_upload OTLP spans are not emitted; the harvest_arcs
- **WHEN** the conditions described by this requirement apply
- **THEN** Per-record `arc_upload` OTLP spans are not emitted; the `harvest_arcs`

### Requirement: Edge case — Plugin yields only HarvesterError items
The system SHALL handle this edge case: when Plugin yields only `HarvesterError` items, then `arc_stream` drains with zero `str` items → `harvest_arcs` creates and immediately completes a harvest with zero ARCs; no error is raised.

#### Scenario: Edge case — Plugin yields only HarvesterError items
- **WHEN** Plugin yields only `HarvesterError` items
- **THEN** `arc_stream` drains with zero `str` items → `harvest_arcs` creates and immediately completes a harvest with zero ARCs; no error is raised

### Requirement: Edge case — All repositories fail
The system SHALL handle this edge case: when All repositories fail, then `asyncio.gather(return_exceptions=True)` collects all exceptions; orchestrator logs each; process exits non-zero.

#### Scenario: Edge case — All repositories fail
- **WHEN** All repositories fail
- **THEN** `asyncio.gather(return_exceptions=True)` collects all exceptions; orchestrator logs each; process exits non-zero

### Requirement: Edge case — Max_connections = 1
The system SHALL handle this edge case: when `max_connections = 1`, then all concurrency reduces to sequential execution; no deadlock.

#### Scenario: Edge case — Max_connections = 1
- **WHEN** `max_connections = 1`
- **THEN** all concurrency reduces to sequential execution; no deadlock

### Requirement: Edge case — Thread pool exhausted
The system SHALL handle this edge case: when Thread pool exhausted, then `asyncio.to_thread()` calls queue behind available workers; event loop continues processing other coroutines.

#### Scenario: Edge case — Thread pool exhausted
- **WHEN** Thread pool exhausted
- **THEN** `asyncio.to_thread()` calls queue behind available workers; event loop continues processing other coroutines

### Requirement: Edge case — Source reports numberOfMatchedRecords = 0 on first call
The system SHALL handle this edge case: when Source reports `numberOfMatchedRecords = 0` on first call, then `expected_datasets` is passed as `0`; `harvest_arcs` creates and immediately completes the harvest.

#### Scenario: Edge case — Source reports numberOfMatchedRecords = 0 on first call
- **WHEN** Source reports `numberOfMatchedRecords = 0` on first call
- **THEN** `expected_datasets` is passed as `0`; `harvest_arcs` creates and immediately completes the harvest
