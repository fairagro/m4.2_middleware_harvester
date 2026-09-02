# Stable Graph — Design

## Key Decisions

1. **Spec-home is `stable-graph`, not vocabulary mapping**
   — ResourceView is shared RDF hygiene infrastructure (like `nice-http-client`).
   MappingContext and ARC identifier / publisher policies stay on the mapper ABC
   and vocabulary mappers.

2. **MappingContext on `map_graph`, never on StableGraph.wrap**
   — Discovery `source_url` / `harvest_source_id` are harvest-identity context.
   No ResourceView accessor needs them; wrapping them into StableGraph would
   couple RDF hygiene to harvest identity.

3. **Soft API: lift battle-tested Schema.org accessor semantics**
   — Language ranks, BNode content signatures, dual schema.org namespaces, and
   text vs resource policies match the former Schema.org private helpers rather
   than inventing a third policy during extract.

4. **`doi()` is a graph brick; Investigation.identifier cascade stays mapper-local**
   — Literal / IRI / typed Schema.org `PropertyValue` DOI extraction (when
   `term_namespaces` are configured) lives in StableGraph; choosing identifier
   vs Publication vs Alternate Identifier stays in the vocabulary mapper.

5. **StableGraph is call-scoped (no `self._stable`)**
   — The plugin maps concurrently via `asyncio.to_thread` on one shared mapper.
   The ABC passes `stable` into `_map_graph`; per-call helper objects are
   allowed. A dedicated `_*Run` class per vocabulary is not required.
