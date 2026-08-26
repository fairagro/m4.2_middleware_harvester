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
   Display-string splits (when structured given/family fields are absent) go through shared
   `person_names.split_display_name` (`nameparser`), not per-mapper heuristics, so particles,
   titles/suffixes, and `Family, Given` forms stay consistent across Schema.org and Regal.
   Single-token labels remain unlabeled agents (`given=None`) so org-like literals still fail
   closed or become Comments.

6. **Schema.org Investigation.identifier is harvest-stable or the record is refused**
   — rdflib blank-node labels are parser-internal and change every parse; the API hashes
   `identifier + rdi` into a GitLab path, so a blank node creates a new repo per harvest.
   `GeneralSchemaOrgMapper` therefore keys `Investigation.identifier` to the **harvest unit**
   (discovered page), not to a DOI that may be shared across pages or duplicated on one page.
   Resolution order: `harvest_source_id` from discovery when supplied (e.g. MyCoRe Solr `id` on
   `UrlDiscoveryResult`), else sanitized discovered page URL, else canonical `http(s)` URL from
   `schema:url` / `sameAs` / Dataset `@id`, else a single extracted DOI as last resort, else
   mapping error. DOIs (including Schema.org `PropertyValue`) always appear in Publication and/or
   Investigation Comments; they are not the primary identifier when harvest context exists. Title
   slugs and `str(subject)` on blank nodes are not identifiers. The plugin passes
   `map_graph(..., context=MappingContext(source_url=..., harvest_source_id=...))`.

7. **Schema.org multi-value fields and contacts are harvest-deterministic**
   — Keywords are trimmed/deduped/sorted (`casefold`). Multi-literal `_str` prefers
   `en` > `de` > untagged > other (empty dropped; longer then lex tie-break). Creator/
   author/contributor nodes are sorted before Contacts; Publication authors use
   `F. Last` (no comma) so ARCtrl `#Author_*` nodes stop oscillating with RDF order.
   Non-literal `_obj` selection prefers URIRefs over blank nodes and ranks blank nodes
   by outgoing content signatures (including a bounded nested BNode signature), never by
   parser-local BNode labels.

8. **Schema.org multi-DOI pages preserve all DOIs in metadata**
   — When one harvested page lists multiple DOIs, the lexicographic minimum (`casefold`) is
   the canonical Publication DOI; non-canonical DOIs become `Alternate Identifier` Comments.
   `Investigation.identifier` remains the harvest source key (`harvest_source_id` or page URL)
   when discovery context is supplied, so multi-DOI order in JSON-LD cannot flip `arc_id` between runs.

9. **RDF field access goes through StableGraph / ResourceView; discovery via MappingContext**
   — `LinkedDataMapper.map_graph` wraps via subclass `_stable_wrap` and passes the
   resulting `StableGraph` **explicitly** into `_map_graph(graph, context, stable)`.
   Mappers must not store the wrap on `self` (the plugin maps concurrently with
   `asyncio.to_thread` on one shared mapper instance). Schema.org keeps the wrap on a
   per-call helper (`_SchemaOrgRun`); Regal migration onto ResourceView is a follow-up.
   `StableGraph.wrap` takes generic `term_namespaces` / `label_predicates`; Schema.org
   passes `SCHEMA_ORG_NAMESPACES` from `_stable_wrap`. Discovery context is a required
   frozen `MappingContext` on `map_graph`, never part of StableGraph wrap. Callers without
   discovery pass an explicit empty `MappingContext()`. Identifier cascade and
   publisher-invert policy stay mapper-local, composed from API bricks (`doi`, `http_iri`,
   accessors).

10. **StableGraph vs LinkedDataMapper boundary (Faustregel)**
   — **StableGraph / ResourceView** answer: what is *stably* in the RDF? They know the
   graph, nodes, literals, and wrap policy; they must not encode discovery,
   Investigation.identifier cascade, or Person/Comment policy.
   — **LinkedDataMapper** answers: how does that become a *HarvestedArc*? It owns the
   plugin contract (`map_graph`, registry), `MappingContext`, wrap hand-off into
   `_map_graph`, and shared ARC-oriented helpers (`sanitize_identifier`,
   `to_identifier_slug`, `pick_canonical_doi`, `resolve_harvest_source_identifier`).
   — Place a function by dependency: if it is explainable with only Graph + policy →
   StableGraph; if it needs harvest/ARC identity or “what becomes the Investigation?” →
   mapper ABC or vocabulary mapper. Do not re-wrap ResourceView methods on the ABC
   (`stable.view(node)["name"]` / `stable.sort_key` instead of mapper `schema_text` /
   `node_key` facades).
   — **`doi()` stays on ResourceView**: extracting a DOI from Literal / IRI / a
   PropertyValue-*shaped* node is still graph reading (optional when
   `term_namespaces` are configured). Choosing whether that DOI becomes
   `Investigation.identifier`, a Publication DOI, or an Alternate Identifier Comment
   remains mapper policy.

11. **StableGraph is call-scoped; never store it on the shared mapper instance**
   — The linked-data plugin keeps one mapper and maps datasets concurrently via
   `asyncio.to_thread(self._mapper.map_graph, …)`. Instance fields such as
   `self._stable` would cross-talk between threads. Therefore:
   - `map_graph` MUST wrap once and pass `StableGraph` into `_map_graph` as a
     parameter (ABC contract).
   - Concrete mappers MUST NOT assign the wrap (or a ResourceView session) to
     `self` for the duration of mapping.
   - Allowed patterns: a **per-call** helper object that owns `stable`
     (e.g. Schema.org `_SchemaOrgRun`), or threading `stable` through private
     methods. Requiring a `_*Run` class for every vocabulary is NOT required.
   - Regression: unit tests MUST exercise concurrent `map_graph` on one mapper
     instance with distinct graphs and assert identifiers / titles do not mix.

12. **Schema.org refuses missing Dataset titles (no Untitled invent)**
   — ISA/ARC titles and Study/Assay identifier slugs come from `schema:name`.
   Inventing `Untitled Dataset` / `untitled` / `dataset` hides bad source
   metadata and still produces an uploadable ARC. Schema.org therefore fail-
   closes with a mapping error (plugin → `RecordProcessingError` / harvest
   report). `to_identifier_slug` returns `None` for blank/unusable input;
   Regal may keep its own Untitled display policy separately.
