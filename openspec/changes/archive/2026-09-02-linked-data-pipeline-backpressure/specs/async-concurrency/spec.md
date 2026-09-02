## ADDED Requirements

### Requirement: Linked Data mapped-output buffering is bounded by worker_tasks

In addition to limiting concurrent dataset fetch/map tasks, the Linked Data
plugin MUST bound buffered mapped output between the worker stage and plugin
`yield`. The documented bound SHALL be **2 × `effective_worker_tasks`**
mapped outcomes (in-flight workers plus queued results). Production MUST
stall when the bound is reached rather than enqueueing unbounded RO-Crate JSON
strings while waiting for a slow upload consumer.

#### Scenario: Bound is documented and tied to config

- **WHEN** `effective_worker_tasks` is N for a linked-data repository
- **THEN** the plugin pipeline MUST NOT hold more than 2 × N mapped outcomes
  at once during concurrent harvest

#### Scenario: Max_connections = 1 remains sequential and bounded

- **WHEN** `max_connections = 1` (so `effective_worker_tasks = 1`)
- **THEN** the plugin MUST process datasets sequentially without deadlock AND
  MUST hold at most two mapped outcomes in the pipeline at once
