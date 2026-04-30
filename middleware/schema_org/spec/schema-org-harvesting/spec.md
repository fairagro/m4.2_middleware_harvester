# Schema.org Harvesting

Top-level plugin contract for the Schema.org harvester component.

This spec defines the plugin entrypoint, configuration contract, and implementation selection model. Concrete behavior is defined in specialized feature specs.

## Requirements

- [ ] Provide a plugin-level `Config` class as a Pydantic `BaseModel` that is referenced by the main `middleware.harvester.config.Config` plugin config schema.
- [ ] Require explicit `sitemap_type`, `dataset_type`, and `payload_type` values. Do not infer source formats automatically.
- [ ] Expose the plugin entrypoint as `run_plugin(config: PluginConfig) -> AsyncGenerator[str | HarvesterError, None]`.
- [ ] Select implementations using registries for sitemap, dataset, and mapper types.
- [ ] Validate config at startup and fail fast on unsupported enum values.
- [ ] Yield serialized RO-Crate JSON-LD strings or `HarvesterError` objects for every dataset processed.
- [ ] Continue harvesting remaining datasets when a dataset-level failure occurs.

## Feature split

- `middleware/schema_org/spec/xml-sitemap-parser/spec.md` — XML sitemap discovery and dataset URL extraction.
- `middleware/schema_org/spec/schemaorg-dataset-abstraction/spec.md` — Dataset payload abstraction and provider-specific dataset wrappers.
- `middleware/schema_org/spec/schemaorg-mapper/spec.md` — Graph-to-ARC mapping and RO-Crate serialization.

## Edge Cases

- An empty sitemap must yield zero outputs and exit cleanly.
- Duplicate dataset URLs in a sitemap must be deduplicated before parsing.
- Unsupported sitemap, dataset, or payload types must fail fast during validation.
- Dataset-level parse or map failures must be emitted as errors and should not stop the overall harvest.
