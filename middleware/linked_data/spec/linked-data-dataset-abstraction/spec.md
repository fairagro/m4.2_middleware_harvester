# Linked Data Dataset Abstraction

Abstract payload handling for individual dataset records discovered during Linked Data harvesting.

## Requirements

- [ ] Provide a `Dataset` interface that exposes a stable identifier and an async `to_graph()` method returning an `rdflib.Graph`.
- [ ] Provide a `Dataset.from_discovery_result(result: DiscoveryResult, client: NiceHttpClient | None, config: Config) -> Dataset` class method so the plugin can construct dataset instances from raw discovery results. `client` may be `None` for dataset implementations that do not make HTTP requests; implementations that require HTTP access must raise a descriptive error when `client` is `None`.
- [ ] Keep dataset wrappers independent of sitemap discovery and HTTP fetching.
- [ ] Use the dataset identifier as the stable key for error reporting and downstream mapping.
- [ ] Require every successful `DiscoveryResult` to expose a stable `identifier` used for sitemap-level deduplication.
- [x] Deduplicate successful discovery identifiers in `Sitemap.discover()` and yield shared `SkippedRecord` (not a plugin-local duplicate type).
- [x] Yield shared `RecordProcessingError` for unusable discovery entries (missing id, non-object payload, empty loc, …)—same type as inspire; do not introduce a plugin-local failure wrapper.
- [x] Have the plugin forward `RecordProcessingError` and `SkippedRecord` from discovery to the orchestrator unchanged.

## Edge Cases

- A dataset implementation receiving an unsupported `DiscoveryResult` subtype → raise a descriptive error.
- A dataset implementation must not perform top-level plugin orchestration.
- Discovery failure with no stable `@id` → still yield `RecordProcessingError` with a descriptive reason and a synthetic key (e.g. page offset + array index) so `fairagro:failedRecords` can list it.
