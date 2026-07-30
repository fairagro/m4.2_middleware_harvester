# Linked Data Harvesting — Design

## Architecture overview

`middleware/linked_data` is split into three responsibilities:

- `config.py` defines explicit plugin configuration for sitemap, dataset, and payload types.
- `dataset.py` defines the dataset abstraction and placeholder dataset implementations.
- `linked_data_mapper.py` defines the graph-to-ARC mapper abstraction and placeholder mapper implementations.
- `sitemap.py` defines the sitemap abstraction and XML sitemap implementation.
- `plugin.py` is the plugin entrypoint and config-driven factory layer that resolves implementations from registry maps and instantiates the correct sitemap and mapper implementations.

The current implementation supports only one concrete type per enum, but the plugin is architected so that new sitemap kinds, dataset providers, and payload formats can be added with minimal changes.

## Key Decisions

1. **Use explicit typed enums for sitemap, dataset, and payload selection**
   — The plugin must not infer formats automatically. Explicit `StrEnum` values in `Config` enforce that the harvester only uses the configured sitemap and payload types, and they provide a stable extension point for future provider-specific implementations.

2. **Use registration decorators on interface bases and resolve implementations from registries in `plugin.py`**
   — A decorator-driven registry avoids nested `if`/`elif` chains and keeps each concrete class responsible for its own registration, so adding a new sitemap, dataset, or mapper type does not require modifying the factory selection code.

3. **Extract dataset and mapper abstractions into separate modules**
   — `dataset.py` and `linked_data_mapper.py` isolate responsibility for dataset payloads and graph-to-ARC mapping. `sitemap.py` now owns the sitemap abstraction and XML sitemap implementation.

4. **Yield `DiscoveryResult` objects from `Sitemap.discover()` and construct `Dataset` instances in the plugin**
   — Sitemap implementations are responsible for locating dataset sources and representing them as typed `DiscoveryResult` values (e.g., `UrlDiscoveryResult`). The plugin instantiates the configured `Dataset` class by calling `Dataset.from_discovery_result(...)`. This keeps sitemap parsing and dataset payload handling fully separate, and allows a sitemap that yields raw content (e.g., inline JSON-LD) to coexist with one that yields URLs to fetch.

5. **Implement `XmlSitemap` as the XML sitemap parser for the `xml` sitemap type**
   — The XML sitemap protocol is a distinct source format, so it is isolated in its own implementation file and can evolve separately from dataset parsing and mapping. This also keeps the plugin factory focused on type selection, not parsing details.

6. **Keep `LinkedDataPlugin.run()` as an async generator yielding `HarvestedArc | HarvesterError | SkippedRecord`**
   — This matches the harvester orchestrator contract. Successes, record-level
   failures, and deliberate skips share one stream so
   [`harvest-report`](../../../harvest-report/) statistics and
   `fairagro:failedRecords` stay complete. Errors must be yielded, not only
   logged inside sitemap/dataset code
   ([`error-handling`](../../../../openspec/specs/error-handling/)).

7. **Implement the `Sitemap.discover()` contract as an async generator**
   — The abstract method explicitly returns `AsyncGenerator[DiscoveryResult, None]`, so concrete sitemap implementations can asynchronously yield raw discovery results and the plugin can consume them with `async for` consistently.

8. **Keep vocabulary-specific mappers under vocabulary-specific names**
   — The shared ABC is `LinkedDataMapper`. Concrete mappers keep vocabulary-accurate names (e.g. `GeneralSchemaOrgMapper` for schema.org). Placeholders for the interface contract may use a generic dummy name, but production mappers must not pretend a schema.org crosswalk is vocabulary-neutral.

9. **Inject shared `NiceHttpClient` into sitemaps; use `get_with_policy()` for discovery HTTP**
   — Discovery (XML nesting, MyCoRe/Regal pagination) and dataset fetches share one
   polite client so robots.txt, per-host rate limiting, and retry/backoff apply to
   every outbound request—not only landing-page fetches.
