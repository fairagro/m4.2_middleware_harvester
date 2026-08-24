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

5. **Person contacts require a non-empty given name; Organizations are Comment/Affiliation**
   — ISA contacts are Persons only. Mapping Organization publishers (e.g. Zenodo) as
   `Person(first_name="")` survives initial `ToROCrateJsonString` upload but fails DataHUB
   `arc-export` after ISA Write/load. Mappers therefore emit `Comment("Publisher", …)` (and
   keep creator affiliations on `Person.Affiliation`), refuse placeholder given names, and
   fail closed via `require_nonempty_person_given_names` before returning `HarvestedArc`.

6. **Schema.org Investigation.identifier is catalog-stable or the record is refused**
   — rdflib blank-node labels are parser-internal and change every parse; the API hashes
   `identifier + rdi` into a GitLab path, so a blank node creates a new repo per harvest.
   `GeneralSchemaOrgMapper` therefore uses DOI (including Schema.org `PropertyValue`), then
   `http(s)` URL (including a MyCoRe Receive-URL), then raises a mapping error. Title
   slugs and `str(subject)` on blank nodes are not identifiers. The plugin passes the
   discovered page URL as `map_graph(..., source_url=...)` and the mapper sanitizes it
   into an `arctrl`-compatible identifier.

7. **Schema.org multi-value fields and contacts are harvest-deterministic**
   — Keywords are trimmed/deduped/sorted (`casefold`). Multi-literal `_str` prefers
   `en` > `de` > untagged > other (empty dropped; longer then lex tie-break). Creator/
   author/contributor nodes are sorted before Contacts; Publication authors use
   `F. Last` (no comma) so ARCtrl `#Author_*` nodes stop oscillating with RDF order.
   Non-literal `_obj` selection prefers URIRefs over blank nodes and ranks blank nodes
   by outgoing content signatures (including a bounded nested BNode signature), never by
   parser-local BNode labels.
