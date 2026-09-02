## Context

See `proposal.md` — Why. The Linked Data plugin uses a TaskGroup with a
producer (sitemap discovery), worker tasks (fetch + map under a semaphore), and
a consumer loop that `yield`s from an `asyncio.Queue`. Today the queue is
unbounded and the semaphore is released in the worker `finally` after
`results.put()`, decoupling production from consumption. On `GeneratorExit` the
consumer returns without cancelling sibling tasks.

Current implementation: `middleware/linked_data/src/middleware/linked_data/plugin.py`
(`_run_with_task_group`).

## Goals / Non-Goals

**Goals:**

- Bound in-plugin mapped payload memory to **2 × `effective_worker_tasks`**.
- Propagate backpressure from slow upload to discovery/workers without deadlock.
- Cancel producer and workers promptly on early generator close.
- Preserve arrival-order yield and existing error/skip semantics.

**Non-Goals:**

- Upload-layer changes (`harvest_arcs`, `arc_stream`, orchestrator).
- INSPIRE plugin concurrency refactor.
- New config knobs.

## Decisions

### 1. Bounded queue (`maxsize=worker_tasks`) for backpressure

**Choice:** Replace `asyncio.Queue()` with `asyncio.Queue(maxsize=worker_tasks)`.

**Reasoning:** When the queue is full, `await results.put()` blocks the worker
before its `finally` releases the semaphore. The producer cannot acquire new
permits, so in-flight workers plus queued items stay within
`worker_tasks + worker_tasks = 2 × worker_tasks`. This matches the spec bound
without cross-layer acknowledgment from upload.

**Alternatives considered:**

- *Hold semaphore until after consumer `yield`* — tighter bound but requires
  consumer-side release and breaks the current worker-only lifecycle.
- *Unbounded queue + counter only* — does not solve RAM growth.

### 2. Keep semaphore release in worker `finally` after successful `put`

**Choice:** No change to release site; rely on blocking `put` to hold the
permit when the queue is full.

**Reasoning:** Existing deadlock comment (release on `CancelledError`) remains
valid. Blocking `put` naturally couples permit lifetime to queue space.

### 3. Explicit shutdown on `GeneratorExit`

**Choice:** On `GeneratorExit` during `yield`, set an abort flag, cancel all
TaskGroup tasks, drain/clear the results queue as needed, then re-raise or
exit without waiting for full catalog completion.

**Reasoning:** Returning normally from `_run_with_task_group` lets
`TaskGroup.__aexit__` wait for all tasks. Cancellation matches the spec's
"stop promptly" requirement. Python 3.12 `asyncio.TaskGroup` cancels sibling
tasks when one raises `ExceptionGroup`; we will trigger cancellation explicitly
(e.g. cancel tracked tasks or raise `CancelledError` into the group) rather
than swallowing `GeneratorExit` with a bare `return`.

**Alternatives considered:**

- *Bare `return` on GeneratorExit* — current behaviour; rejected (wasted work).
- *Abort `Event` checked only in producer* — workers already started would
  still run; need task cancellation anyway.

### 4. Direct discovery puts (errors/skips) bypass the semaphore but use the same queue

**Choice:** Keep `RecordProcessingError` / `SkippedRecord` / `HarvesterError`
puts from discovery on the bounded queue without acquiring the semaphore.

**Reasoning:** These payloads are small and rare relative to mapped ARC JSON.
They still respect queue backpressure. Changing this is unnecessary complexity.

### 5. Tests: instrument concurrency, not production metrics

**Choice:** Unit tests with fake sitemap + delayed consumer and early
`aclose()`, asserting max in-flight `_process_result` calls and total map count.

**Reasoning:** Observable behaviour matches spec scenarios without exposing
internal queue types in production code.

## Risks / Trade-offs

- **[Risk] Cancelled workers mid-map leave partial state** → Acceptable; abort
  means upload already failed. Ensure `active_workers` and semaphore invariants
  on cancellation (existing `finally` blocks).
- **[Risk] `GeneratorExit` handling differs across Python versions** → Test on
  3.12 (project minimum). Re-raise after cancel to avoid silent swallow.
- **[Risk] Bounded queue + slow consumer reduces throughput** → Intended
  trade-off; bounds RAM. Throughput recovers when consumer catches up.
- **[Risk] Regression on arrival-order yield** → Keep FIFO queue; add test that
  order is preserved under backpressure.

## Migration Plan

- Deploy as a patch to the linked-data plugin only; no config migration.
- Rollback: revert `plugin.py` if cancellation causes unexpected loop noise
  (existing `aclose()` test guards this).

## Open Questions

_None — bound formula (2 × worker_tasks) and bounded-queue approach are fixed
in the proposal/specs._
