# Schema.org Dataset Abstraction

Define the dataset payload abstraction used by Schema.org sitemap implementations.

## Requirements

- [ ] Provide a `Dataset` interface whose concrete implementations expose a stable identifier and an async `to_graph()` method returning an `rdflib.Graph`.
- [ ] Select `Dataset` implementations using `dataset_type` configuration values.
- [ ] Keep sitemap discovery and payload parsing responsibilities separate.
- [ ] Allow dataset wrappers to be provider-specific while exposing the same public contract.
- [ ] Use the dataset identifier as the stable dataset key for error reporting and mapping.

## Edge Cases

- A dataset implementation must handle missing or malformed payload content by raising a parse error or returning an empty graph as appropriate.
- Dataset wrappers must not perform top-level plugin orchestration or HTTP fetching.
