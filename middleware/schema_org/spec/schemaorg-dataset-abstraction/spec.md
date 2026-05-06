# Schema.org Dataset Abstraction

Abstract payload handling for individual dataset records discovered during Schema.org harvesting.

## Requirements

- [ ] Provide a `Dataset` interface that exposes a stable identifier and an async `to_graph()` method returning an `rdflib.Graph`.
- [ ] Provide a `Dataset.from_discovery_result(result: DiscoveryResult, client: NiceHttpClient | None, config: Config) -> Dataset` class method so the plugin can construct dataset instances from raw discovery results. `client` may be `None` for dataset implementations that do not make HTTP requests; implementations that require HTTP access must raise a descriptive error when `client` is `None`.
- [ ] Keep dataset wrappers independent of sitemap discovery and HTTP fetching.
- [ ] Use the dataset identifier as the stable key for error reporting and downstream mapping.

## Edge Cases

- A dataset implementation receiving an unsupported `DiscoveryResult` subtype → raise a descriptive error.
- A dataset implementation must not perform top-level plugin orchestration.
