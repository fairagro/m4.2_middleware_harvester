# Schema.org Mapper — Design

## Architecture overview

The mapper converts a parsed Schema.org RDF graph into serialized ARC RO-Crate JSON-LD. It is a distinct concern from sitemap discovery and dataset payload abstraction.

## Key Decisions

1. **Keep mapping logic in `schema_org_mapper.py`**
   — This isolates graph-to-ARC translation from sitemap and dataset concerns.

2. **Register mapper implementations by `PayloadType`**
   — The plugin selects the correct mapper based on configuration rather than guessing payload formats.

3. **Emit mapping errors as `HarvesterError` objects**
   — Mapping failures are part of the pipeline and must not crash the whole harvest process.
