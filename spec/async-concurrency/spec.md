# Async Concurrency

The harvester and its plugins perform I/O-bound operations (HTTP fetches, API
uploads). All I/O must be non-blocking on the event loop, and independent
operations must run concurrently to overlap network latency.

## Requirements

### Event-Loop Safety

- [ ] No synchronous blocking call (network I/O, file I/O, or CPU-bound work
      > ~5 ms) is executed directly on the event loop; all such calls are
      offloaded via `asyncio.to_thread()`.
- [ ] `CSWClient` offloads every OWSLib call (`CatalogueServiceWeb.__init__`,
      `getrecords2`) to a thread via `asyncio.to_thread()` so the event loop
      remains responsive during multi-second HTTP waits.
- [ ] `HtmlJsonLdDataset.to_graph()` offloads JSON-LD parsing
      (`json.loads` + `rdflib.Graph.parse`) via `asyncio.to_thread()` when the
      total JSON-LD block size exceeds `Config.jsonld_parse_threshold_bytes`
      (default: 65 536 bytes).

### Concurrent Dataset Fetching

- [ ] The Schema.org plugin fetches multiple dataset URLs concurrently,
      bounded by an `asyncio.Semaphore` initialised from `Config.max_connections`.
- [ ] The concurrency limit for dataset fetching uses the same `max_connections`
      value already used as the httpx connection pool ceiling — no new
      configuration field is introduced.
- [ ] A dataset fetch failure is caught per task and converted to a
      `RecordProcessingError`; it does not cancel in-flight sibling fetches.
- [ ] Results are yielded in arrival order (first completed, first yielded),
      not in original discovery order.

### Concurrent Repository Processing

- [ ] The orchestrator processes all configured repositories concurrently via
      `asyncio.gather(return_exceptions=True)`.
- [ ] A failure in one repository sets its `plugin_run` OTLP span to ERROR and
      does not cancel other in-progress repositories.

### Harvest-Based Batch Upload

- [ ] For each repository, the orchestrator calls
      `client.harvest_arcs(repo.rdi, arc_stream, expected_datasets=N)` in place
      of per-record `create_or_update_arc` calls.
- [ ] `arc_stream` is a thin filter async generator that passes through `str`
      items from the plugin, logs `HarvesterError` items, and skips them.
- [ ] When the source protocol reports a total record count upfront
      (INSPIRE CSW `numberOfMatchedRecords`, MyCoRe Solr `numFound`), the
      plugin exposes that count and the orchestrator passes it as
      `expected_datasets`.
- [ ] When the total count is not known upfront (XML sitemap, general
      Schema.org sources), `expected_datasets` is omitted (`None`).
- [ ] Per-record `arc_upload` OTLP spans are not emitted; the `harvest_arcs`
      call is represented as a single `harvest_upload` span on the `plugin_run`
      level, carrying `harvester.arcs_uploaded` and `harvester.harvest_id`
      attributes.

## Edge Cases

Plugin yields only `HarvesterError` items → `arc_stream` drains with zero
`str` items → `harvest_arcs` creates and immediately completes a harvest with
zero ARCs; no error is raised.

All repositories fail → `asyncio.gather(return_exceptions=True)` collects all
exceptions; orchestrator logs each; process exits non-zero.

`max_connections = 1` → all concurrency reduces to sequential execution; no
deadlock.

Thread pool exhausted → `asyncio.to_thread()` calls queue behind available
workers; event loop continues processing other coroutines.

Source reports `numberOfMatchedRecords = 0` on first call → `expected_datasets`
is passed as `0`; `harvest_arcs` creates and immediately completes the harvest.
