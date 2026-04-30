# Schema.org Harvesting

Harvest Schema.org dataset metadata from configured sitemap sources, parse it into `rdflib.Graph`, and convert each dataset to ARC RO-Crate JSON-LD.

## Requirements

- [ ] Provide a plugin-level `Config` class as a Pydantic `BaseModel` that is referenced by the main `middleware.harvester.config.Config` plugin config schema.
- [ ] Require explicit sitemap configuration in `Config`; do not infer sitemap type or dataset payload format automatically.
- [ ] Support explicit sitemap kinds via configuration as distinct values such as `xml`, `edal`, and `thunen`.
- [ ] Support explicit dataset kinds via configuration as distinct values such as `edal` and `bonares`.
- [ ] Define an abstract `Sitemap` interface whose async iterator yields dataset descriptors.
- [ ] Define an abstract `Dataset` interface whose concrete implementations expose the payload as an `rdflib.Graph`.
- [ ] Define an abstract `SchemaOrgMapper` interface whose concrete implementations map `rdflib.Graph` to ARC Ro-Crate JSON-LD.
- [ ] Ensure the `Sitemap` implementation constructs the correct `Dataset` subtype based on configured payload type and source metadata.
- [ ] For URI-based datasets, download the payload asynchronously and parse it using the configured dataset payload type.
- [ ] Parse JSON-LD payloads directly as JSON-LD.
- [ ] Parse HTML payloads containing embedded Schema.org metadata in JSON-LD, RDFa, or microdata.
- [ ] Accept dataset payloads that are plain JSON-LD strings.
- [ ] When parsing Schema.org content, only consider Schema.org `Dataset` entities or `@graph` structures containing at least one `Dataset` entity. If no valid dataset entity is found, emit a warning and continue.
- [ ] Expose the plugin entrypoint as `run_plugin(config: PluginConfig) -> AsyncGenerator[str | HarvesterError, None]`.
- [ ] Validate config at startup and fail fast on unsupported sitemap or dataset payload types.
- [ ] For any dataset that cannot be fetched, parsed, or mapped, emit a processing error and continue harvesting remaining datasets.

## Edge Cases

- A missing or unsupported `sitemap_type` or `dataset_type` must fail fast during config validation.
- An empty sitemap must yield zero ARC outputs and exit cleanly.
- If the resource type pointed to by a sitemap entry does not match the configured dataset payload type, the plugin must emit a dataset-level processing error and continue.
- Duplicate dataset URLs in a sitemap must be deduplicated before parsing.
- HTML pages with embedded Schema.org content that do not contain a valid `schema:Dataset` node must yield a parsing error and continue.
- Invalid JSON-LD syntax in a configured JSON-LD payload must yield a processing error and continue.
- When parsing fails (JSON-LD, HTML, or XML), the error message must include the raw payload that caused the failure.
- If `rdflib.Graph` parsing succeeds but ARC mapping fails due to missing required metadata, the plugin must yield a mapping error and continue; the mapping failure is logged as a warning.
- The harvest flow must not perform automatic format detection; it must only parse the explicitly configured sitemap and payload types.
