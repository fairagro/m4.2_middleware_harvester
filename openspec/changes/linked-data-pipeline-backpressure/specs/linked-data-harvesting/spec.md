## ADDED Requirements

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
