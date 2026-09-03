## ADDED Requirements

### Requirement: RegalMapper MUST use ResourceView for RDF field access

`RegalMapper` MUST obtain ResearchData field values used for ARC text via the
StableGraph / ResourceView access layer (same Faustregel as Schema.org: RDF
hygiene in StableGraph, ARC policy in the vocabulary mapper). It MUST NOT use
`graph.value` for multi-valued or singular ARC-bound string fields, MUST NOT
persist `str(BNode)` into ARC identifier or comment text, and MUST NOT keep
parallel private copies of the shared literal/resource language and BNode-ranking
helpers once the access layer provides them. Regal-specific policies (PUBLISSO
name splitting, joinedFunding preference, resource base URL, opaque known
predicates, Investigation identifier cascade) MUST remain in the mapper.
Detailed Regal field and stability requirements live in
`openspec/specs/regal-to-arc-mapping/`.

#### Scenario: Regal description and funding come from ResourceView accessors

- **WHEN** a Regal ResearchData graph is mapped after the ResourceView migration
- **THEN** description and funding-related strings in the HarvestedArc MUST
  match ResourceView text / labelled policy and MUST NOT depend on raw
  `graph.value` selection

#### Scenario: Existing Regal harvest-stability tests remain green

- **WHEN** the existing Regal unit tests for funding BNode stability, opaque
  comments, and contact-related blanks run
- **THEN** they MUST pass without weakening blank-node or order invariants

## MODIFIED Requirements

### Requirement: StableGraph MUST be call-scoped on concurrent map_graph

`LinkedDataMapper.map_graph` MUST wrap the graph and pass `StableGraph` into
`_map_graph` as a parameter. Concrete mappers MUST NOT store that wrap (or an
equivalent RDF session) on the shared mapper instance (`self`), because the
linked-data plugin maps concurrently via `asyncio.to_thread` on one mapper.
Per-call helper objects that own `stable`, or threading `stable` through private
methods, are allowed. Requiring a dedicated `_*Run` class per vocabulary is NOT
required. Unit tests MUST cover concurrent `map_graph` calls on one instance for
each vocabulary mapper that uses StableGraph in production (Schema.org and
Regal).

#### Scenario: Concurrent maps on one Schema.org mapper do not cross-talk

- **WHEN** one `GeneralSchemaOrgMapper` instance maps two distinct Dataset graphs
  concurrently in worker threads
- **THEN** each result's Investigation identifier and title MUST match its own
  graph (no swapped or mixed values)

#### Scenario: Concurrent maps on one Regal mapper do not cross-talk

- **WHEN** one `RegalMapper` instance maps two distinct ResearchData graphs
  concurrently in worker threads
- **THEN** each result's Investigation identifier and title MUST match its own
  graph (no swapped or mixed values)
