# Async Concurrency — Design

## Architecture Overview

Concurrency is introduced at four independent layers:

1. **Thread offload** (`inspire/csw_client.py`) — OWSLib synchronous calls
   wrapped in `asyncio.to_thread()`; the `CSWClient` internal API is unchanged.
2. **Task-level parallelism** (`schema_org/plugin.py`) — `asyncio.Semaphore` +
   `asyncio.TaskGroup` for concurrent dataset fetches within a single plugin
   invocation.
3. **Repository-level parallelism** (`harvester/main.py`) — `asyncio.gather()`
   over all `RepositoryConfig` entries.
4. **Upload parallelism** — delegated entirely to `ApiClient.harvest_arcs`,
   which runs bounded parallel submissions internally via `asyncio.wait`.

## Key Decisions

1. **`asyncio.to_thread()` for OWSLib, not a full async CSW client**
   — OWSLib has no async API. Wrapping at the call site with `asyncio.to_thread()`
   surfaces the I/O wait to the event loop with minimal code change. A full async
   CSW client would require reimplementing OWS XML parsing for marginal additional
   benefit.

2. **`asyncio.Semaphore` sourced from `max_connections`, no new config field**
   — `max_connections` already controls the httpx connection pool ceiling. Using
   the same value for the Semaphore ensures in-flight fetch tasks never exceed
   available connections, preventing connection starvation without adding a
   separate concurrency knob.

3. **`asyncio.TaskGroup` for dataset fetches; results yielded in arrival order**
   — Per-task error handling (catch inside each task, convert to
   `RecordProcessingError`) means `TaskGroup` never sees an unhandled exception
   and never cancels siblings. Yielding in arrival order via `asyncio.as_completed`
   maximises throughput: slow pages do not hold up fast ones.

4. **`asyncio.gather(return_exceptions=True)` for repository processing**
   — `return_exceptions=True` ensures all repositories run to completion
   regardless of sibling failures. The default (`return_exceptions=False`) would
   cancel in-progress repositories on the first failure, losing partial harvest
   progress.

5. **`harvest_arcs` replaces per-record `create_or_update_arc`**
   — `harvest_arcs` creates a server-side harvest context, submits all ARCs with
   bounded internal parallelism (`ApiClient.max_concurrency`), and completes or
   cancels atomically. A thin filter generator (`_arc_stream`) adapts the plugin's
   `AsyncGenerator[str | HarvesterError, None]` output to the
   `AsyncIterator[str]` interface expected by `harvest_arcs`.

6. **Per-record `arc_upload` OTLP spans are not emitted**
   — `harvest_arcs` manages individual submissions internally in parallel;
   injecting per-record spans would require replicating that internal loop in the
   orchestrator, negating the purpose of using `harvest_arcs`. A single
   `harvest_upload` span at the repository level (with `harvester.arcs_uploaded`
   and `harvester.harvest_id` attributes) provides sufficient observability.

7. **`expected_datasets` surfaced via a plugin-level pre-fetch**
   — Sources that report a total count on their first network call (INSPIRE CSW
   `numberOfMatchedRecords`, MyCoRe Solr `numFound`) expose it through an
   optional `get_expected_count()` coroutine on their client/sitemap class. The
   orchestrator calls this before starting the plugin generator and passes the
   result to `harvest_arcs`. Sources that do not know the count upfront (XML
   sitemap, general Schema.org) do not implement this coroutine; the orchestrator
   passes `expected_datasets=None`. No pre-fetch is issued for sources that do
   not support it.

8. **No multiprocessing**
   — All bottlenecks are I/O-bound (HTTP, API uploads). Python's GIL is not a
   limiting factor. Multiprocessing would add IPC overhead, break the `pythonnet`
   / arctrl .NET bridge (which must stay on a single OS process), and prevent
   sharing the asyncio event loop across repositories.

9. **arctrl (.NET bridge) remains on the event loop thread**
   — `asyncio.to_thread()` is used exclusively for I/O (OWSLib, JSON-LD
   parsing). ARC object construction and serialisation (`arc.ToROCrateJsonString()`)
   always executes on the event loop thread. This is safe with PyInstaller
   `--onedir` because `threading` and `concurrent.futures` work correctly in
   frozen onedir binaries; only `multiprocessing` is problematic in that
   environment.
