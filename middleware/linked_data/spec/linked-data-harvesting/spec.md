# Linked Data Harvesting

Top-level plugin contract for the Linked Data harvester component.

This spec defines the plugin entrypoint, configuration contract, and implementation selection model. Concrete behavior is defined in specialized feature specs.

## Requirements

- [ ] Provide a plugin-level `Config` class as a Pydantic `BaseModel` that is referenced by the main `middleware.harvester.config.Config` plugin config schema.
- [ ] Require explicit `sitemap_type`, `dataset_type`, and `payload_type` values. Do not infer source formats automatically.
- [ ] Implement `LinkedDataPlugin(Plugin)` in `plugin.py`; the central Harvester instantiates it with the plugin config and invokes `run()` and `get_expected_datasets()` via the `Plugin` interface.
- [ ] Select implementations using registries for sitemap, dataset, and mapper types.
- [ ] Validate config at startup and fail fast on unsupported enum values.
- [ ] Yield serialized RO-Crate JSON-LD strings or `HarvesterError` objects for every dataset processed.
- [ ] Continue harvesting remaining datasets when a dataset-level failure occurs.

## Feature split

- `middleware/linked_data/spec/xml-sitemap-parser/spec.md` — XML sitemap discovery from a single sitemap URL and dataset URL extraction.
- `middleware/linked_data/spec/sitemap-mycore-solr/spec.md` — MyCoRe Solr JSON discovery source; Solr pagination and `/receive/{id}` URL construction.
- `middleware/linked_data/spec/linked-data-dataset-abstraction/spec.md` — Dataset payload abstraction and provider-specific dataset wrappers.
- `middleware/linked_data/spec/html-jsonld-dataset/spec.md` — Dataset implementation that fetches an HTML page and extracts embedded JSON-LD.
- `middleware/linked_data/spec/regal-jsonld/spec.md` — Regal `/find` discovery, inline Regal JSON-LD datasets, and Regal→ARC mapping.
- `middleware/linked_data/spec/linked-data-mapper/spec.md` — Graph-to-ARC mapping and RO-Crate serialization.

## Edge Cases

- An empty sitemap must yield zero outputs and exit cleanly.
- Duplicate dataset URLs in a sitemap must be deduplicated before parsing.
- Unsupported sitemap, dataset, or payload types must fail fast during validation.
- Dataset-level parse or map failures must be emitted as errors and should not stop the overall harvest.
