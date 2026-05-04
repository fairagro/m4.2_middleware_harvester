# Schema.org Dataset Abstraction

Abstract payload handling for individual dataset records discovered during Schema.org harvesting.

## Requirements

- [ ] Provide a `Dataset` interface that exposes a stable identifier and an async `to_graph()` method returning an `rdflib.Graph`.
- [ ] Provide a `Dataset.from_discovery_result(result: DiscoveryResult) -> Dataset` class method so the plugin can construct dataset instances from raw discovery results.
- [ ] Keep dataset wrappers independent of sitemap discovery and HTTP fetching.
- [ ] Use the dataset identifier as the stable key for error reporting and downstream mapping.

## Edge Cases

- A dataset implementation receiving an unsupported `DiscoveryResult` subtype → raise a descriptive error.
- A dataset implementation must not perform top-level plugin orchestration.
