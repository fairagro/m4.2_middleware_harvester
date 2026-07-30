# Linked Data Mapper — Design

## Architecture overview

`LinkedDataMapper` is the plugin-wide ABC that converts an `rdflib.Graph` into
a `HarvestedArc` (ARC RO-Crate JSON-LD plus study/assay counts). It is a
distinct concern from sitemap discovery and dataset payload abstraction.
Concrete subclasses are vocabulary-specific (e.g. `GeneralSchemaOrgMapper` for
schema.org, `RegalMapper` for Regal).

## Key Decisions

1. **Keep the shared ABC in `linked_data_mapper.py`, vocabulary mappers in dedicated modules**
   — The ABC isolates graph-to-ARC translation from sitemap and dataset concerns.
   Concrete mappers such as `GeneralSchemaOrgMapper` stay named after the vocabulary
   they understand.

2. **Register mapper implementations by `PayloadType`**
   — The plugin selects the correct mapper based on configuration rather than guessing payload formats.

3. **Return `HarvestedArc`, not a bare JSON string**
   — Composition counts and serialization happen once in `HarvestedArc.from_arctrl`.
   The orchestrator must not re-parse RO-Crate JSON to discover studies/assays.

4. **Emit mapping errors as `HarvesterError` objects**
   — Mapping failures are part of the pipeline and must not crash the whole harvest process.
