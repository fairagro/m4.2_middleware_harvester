# Linked Data Mapper

Define the mapping contract from a parsed Linked Data RDF graph to ARC RO-Crate JSON-LD.

Vocabulary-specific implementations (e.g. `GeneralSchemaOrgMapper` for schema.org,
or a future Regal mapper) register against `payload_type` and implement this interface.

## Requirements

- [ ] Provide a `LinkedDataMapper` interface that accepts an `rdflib.Graph` and returns a serialized RO-Crate JSON-LD string.
- [ ] Select mapper implementations using `payload_type` configuration values.
- [ ] Keep mapping logic separate from sitemap discovery and dataset payload extraction.
- [ ] Produce errors as `HarvesterError` objects when mapping fails.
- [ ] Support explicit, non-guessing mapper selection based on the configured payload type.

## Edge Cases

- A graph without valid dataset metadata must yield a mapping error and not crash the plugin.
- Mapping implementations must not depend on runtime config outside the selected `payload_type`.
