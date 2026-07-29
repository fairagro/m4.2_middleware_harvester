# Linked Data Mapper — Design

## Architecture overview

`LinkedDataMapper` is the plugin-wide ABC that converts an `rdflib.Graph` into
serialized ARC RO-Crate JSON-LD. It is a distinct concern from sitemap discovery
and dataset payload abstraction. Concrete subclasses are vocabulary-specific
(e.g. `GeneralSchemaOrgMapper` for schema.org).

## Key Decisions

1. **Keep the shared ABC in `linked_data_mapper.py`, vocabulary mappers in dedicated modules**
   — The ABC isolates graph-to-ARC translation from sitemap and dataset concerns.
   Concrete mappers such as `GeneralSchemaOrgMapper` stay named after the vocabulary
   they understand.

2. **Register mapper implementations by `PayloadType`**
   — The plugin selects the correct mapper based on configuration rather than guessing payload formats.

3. **Emit mapping errors as `HarvesterError` objects**
   — Mapping failures are part of the pipeline and must not crash the whole harvest process.
