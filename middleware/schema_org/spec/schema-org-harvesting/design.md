# Schema.org Harvesting — Design

## Architecture overview

`middleware/schema_org` is split into three responsibilities:

- `config.py` defines explicit plugin configuration for sitemap, dataset, and payload types.
- `dataset.py` defines the dataset abstraction and placeholder dataset implementations.
- `schema_org_mapper.py` defines the graph-to-ARC mapper abstraction and placeholder mapper implementations.
- `sitemap.py` defines the sitemap abstraction and XML sitemap implementation.
- `plugin.py` is the plugin entrypoint and config-driven factory layer that resolves implementations from registry maps and instantiates the correct sitemap and mapper implementations.

The current implementation supports only one concrete type per enum, but the plugin is architected so that new sitemap kinds, dataset providers, and payload formats can be added with minimal changes.

## Key Decisions

1. **Use explicit typed enums for sitemap, dataset, and payload selection**
   — The plugin must not infer formats automatically. Explicit `StrEnum` values in `Config` enforce that the harvester only uses the configured sitemap and payload types, and they provide a stable extension point for future provider-specific implementations.

2. **Use registration decorators on interface bases and resolve implementations from registries in `plugin.py`**
   — A decorator-driven registry avoids nested `if`/`elif` chains and keeps each concrete class responsible for its own registration, so adding a new sitemap, dataset, or mapper type does not require modifying the factory selection code.

3. **Extract dataset and mapper abstractions into separate modules**
   — `dataset.py` and `schema_org_mapper.py` isolate responsibility for dataset payloads and graph-to-ARC mapping. `sitemap.py` now owns the sitemap abstraction and XML sitemap implementation.

4. **Yield `DiscoveryResult` objects from `Sitemap.discover()` and construct `Dataset` instances in the plugin**
   — Sitemap implementations are responsible for locating dataset sources and representing them as typed `DiscoveryResult` values (e.g., `UrlDiscoveryResult`). The plugin instantiates the configured `Dataset` class by calling `Dataset.from_discovery_result(...)`. This keeps sitemap parsing and dataset payload handling fully separate, and allows a sitemap that yields raw content (e.g., inline JSON-LD) to coexist with one that yields URLs to fetch.

5. **Implement `XmlSitemap` as the XML sitemap parser for the `xml` sitemap type**
   — The XML sitemap protocol is a distinct source format, so it is isolated in its own implementation file and can evolve separately from dataset parsing and mapping. This also keeps the plugin factory focused on type selection, not parsing details.

6. **Keep `run_plugin()` as an async generator that yields `str | HarvesterError`**
   — This matches the harvester orchestrator contract directly and ensures errors are emitted as part of the same async stream instead of being raised out of band.

7. **Use a string-based forward annotation for `PluginConfig` in `schema_org.plugin.py`**
   — The plugin only needs `PluginConfig` for type checking, and the runtime import would create a circular dependency. Using a quoted type annotation avoids the unnecessary `from __future__ import annotations` import while keeping the module runtime-safe.

8. **Implement the `Sitemap.discover()` contract as an async generator**
   — The abstract method explicitly returns `AsyncGenerator[DiscoveryResult, None]`, so concrete sitemap implementations can asynchronously yield raw discovery results and the plugin can consume them with `async for` consistently.

9. **Keep dummy concrete implementations minimal and clearly isolated**
   — `DummyDataset` and `DummySchemaOrgMapper` are intentionally simple placeholders. They demonstrate the interface contract without adding parsing or network behavior, so future real implementations can replace them with provider-specific subclasses.
