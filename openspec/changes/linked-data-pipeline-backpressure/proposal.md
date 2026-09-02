## Why

The Linked Data plugin bounds in-flight fetch/map with a semaphore tied to
`worker_tasks`, but releases the permit after enqueueing mapped results into an
**unbounded** `asyncio.Queue`. When the Middleware API upload is slower than
discovery and mapping (especially for Regal inline payloads), full RO-Crate JSON
strings accumulate without limit. On harvest abort (`aclose()` / `GeneratorExit`),
the consumer exits while the TaskGroup producer and workers keep mapping into a
queue nobody reads — wasting CPU and delaying shutdown.

GitHub issue:
[#146](https://github.com/fairagro/m4.2_middleware_harvester/issues/146).

## What Changes

- Bind mapped-ARC buffering to consumption: use a **bounded result queue**
  (`maxsize=worker_tasks`) so production stalls when the consumer is slow.
- Document the memory bound: at most **2 × `worker_tasks`** mapped payloads
  in the plugin pipeline (in-flight workers plus queued results).
- On generator close / upload abort: **cancel** the TaskGroup producer and
  worker tasks promptly instead of draining the remainder of the catalog.
- Add unit tests for slow-consumer backpressure and early `aclose()` cancellation.
- Preserve existing behaviour: arrival-order yield, per-record error handling,
  and no asyncio loop exceptions on clean shutdown.

### Non-Goals

- Changing upload-side concurrency (`harvest_arcs` / `max_concurrency`) — already bounded upstream of the API.
- Applying the same TaskGroup pattern to the INSPIRE plugin (different architecture).
- Holding the semaphore until post-upload acknowledgment (cross-layer coupling).
- New configuration fields beyond existing `worker_tasks` / `max_connections`.

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `linked-data-harvesting`: Pipeline MUST bound buffered mapped output and MUST
  stop discovery/mapping promptly when the plugin generator is closed early.
- `async-concurrency`: Linked Data plugin concurrency MUST include a documented
  bound on buffered mapped ARC payloads tied to `worker_tasks`.

## Impact

- **Affected domains**: `openspec/specs/linked-data-harvesting/`,
  `openspec/specs/async-concurrency/`.
- **Code**: `middleware/linked_data/src/middleware/linked_data/plugin.py`
  (`_run_with_task_group`, worker/consumer lifecycle); unit tests in
  `middleware/linked_data/tests/unit/test_linked_data_plugin.py`.
- **Branch**: `feature/issue-146-linked-data-backpressure`.
- **Dependencies**: none new.
