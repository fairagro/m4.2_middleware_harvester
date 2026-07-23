# Linked Data Dataset Abstraction — Design

## Architecture overview

The dataset abstraction separates payload handling from sitemap discovery and mapping. Each dataset wrapper exposes a stable identifier and produces an `rdflib.Graph` representation of the payload.

## Key Decisions

1. **Isolate dataset wrappers in `dataset.py`**
   — This keeps provider-specific payload parsing separate from higher-level plugin orchestration.

2. **Register dataset implementations by `DatasetType`**
   — A registry allows the plugin factory to select the correct implementation without branching logic.

3. **Use the dataset identifier as the stable processing key**
   — The identifier is used for error reporting, deduplication, and downstream mapping.

4. **Give every successful `DiscoveryResult` a stable `identifier`**
   — `UrlDiscoveryResult` fills it with the dataset URL; `JsonLdDiscoveryResult`
     with the Regal `@id` (or equivalent). `Sitemap.discover()` deduplicates on
     this field and yields shared `SkippedRecord` for duplicates.

5. **Yield shared harvester signals from discovery (inspire-style)**
   — Unusable entries yield `RecordProcessingError` from `_discover` /
     `discover`. Duplicates become `SkippedRecord`. Do not invent plugin-local
     failure/duplicate wrapper types; the orchestrator already understands the
     shared `middleware.harvester.errors` contract.

6. **Construct dataset wrappers from discovery results**
   — Dataset implementations expose `from_discovery_result(...)` so the plugin can instantiate provider-specific payload handlers from a raw sitemap discovery result.
