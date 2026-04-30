# Schema.org Harvesting — Design

## Architecture overview

`middleware/schema_org` is split into three responsibilities:

- `config.py` defines explicit plugin configuration for sitemap, dataset, and payload types.
- `interfaces.py` defines the core Schema.org harvesting abstractions (`Sitemap`, `Dataset`, `SchemaOrgMapper`) and provides placeholder `Dummy*` concrete implementations.
- `plugin.py` is the plugin entrypoint and config-driven factory layer that instantiates the correct sitemap and mapper implementations.

The current implementation supports only one concrete type per enum, but the plugin is architected so that new sitemap kinds, dataset providers, and payload formats can be added with minimal changes.

## Key Decisions

1. **Use explicit typed enums for sitemap, dataset, and payload selection**
   — The plugin must not infer formats automatically. Explicit `StrEnum` values in `Config` enforce that the harvester only uses the configured sitemap and payload types, and they provide a stable extension point for future provider-specific implementations.

2. **Create `create_sitemap()` and `create_mapper()` factories in `plugin.py`**
   — Centralising selection logic in the plugin layer keeps the runtime mapping from config values to concrete implementations local and easy to extend, without leaking selection logic into the abstract interface definitions.

3. **Keep `run_plugin()` as an async generator that yields `str | HarvesterError`**
   — This matches the harvester orchestrator contract directly and ensures errors are emitted as part of the same async stream instead of being raised out of band.

4. **Use a string-based forward annotation for `PluginConfig` in `schema_org.plugin.py`**
   — The plugin only needs `PluginConfig` for type checking, and the runtime import would create a circular dependency. Using a quoted type annotation avoids the unnecessary `from __future__ import annotations` import while keeping the module runtime-safe.

5. **Implement the `Sitemap.discover()` contract as an async generator**
   — The abstract method explicitly returns `AsyncGenerator[Dataset, None]`, so concrete sitemap implementations can asynchronously yield dataset descriptors and the plugin can consume them with `async for` consistently.

6. **Keep dummy concrete implementations minimal and clearly isolated**
   — `DummySitemap`, `DummyDataset`, and `DummySchemaOrgMapper` are intentionally simple placeholders. They demonstrate the interface contract without adding parsing or network behavior, so future real implementations can replace them with provider-specific subclasses.
