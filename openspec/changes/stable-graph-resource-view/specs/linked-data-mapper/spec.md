## ADDED Requirements

### Requirement: map_graph accepts optional MappingContext

The system SHALL provide a `MappingContext` value object that carries discovery
context for a single map operation: optional `source_url` (discovered landing
page URL) and optional `harvest_source_id` (RDI-native catalog id). The
`LinkedDataMapper.map_graph` method MUST accept an `rdflib.Graph` and an
optional `MappingContext` (or equivalent named parameter) instead of separate
loose `source_url` / `harvest_source_id` keyword arguments. Implementations that
do not use discovery context MAY ignore the context value. MappingContext MUST
NOT be passed into StableGraph wrap.

#### Scenario: Schema.org map with harvest context

- **WHEN** `map_graph` is called with a mappable Schema.org graph and a
  MappingContext that sets `harvest_source_id`
- **THEN** the mapper MUST be able to read that harvest source id from the
  context when planning Investigation.identifier

#### Scenario: Regal map ignores unused context

- **WHEN** `map_graph` is called on RegalMapper with a MappingContext
- **THEN** mapping MUST still succeed when the graph is mappable; unused context
  fields MUST NOT cause failure

### Requirement: GeneralSchemaOrgMapper MUST use ResourceView for RDF field access

`GeneralSchemaOrgMapper` MUST obtain Dataset field values used for ARC text
(identifiers bricks, titles, descriptions, keywords, contacts' RDF properties,
comments from graph literals/resources) via the StableGraph / ResourceView
access layer. It MUST NOT use `graph.value` for multi-valued string fields, MUST
NOT persist `str(BNode)` into ARC identifier or comment text, and MUST NOT keep
parallel private copies of the shared literal/resource language and BNode-ranking
helpers once the access layer provides them. Schema.org-specific policies that
compose API bricks — Investigation identifier cascade, multi-DOI alternate
comments, publisher preferring Organization/named resources over literals, and
semantic contact sort — MUST remain in the mapper (see existing Schema.org
requirements in this capability and `openspec/specs/stable-graph/`).

#### Scenario: Description and keywords come from ResourceView accessors

- **WHEN** a Schema.org Dataset is mapped after the StableGraph migration
- **THEN** description and keyword strings in the HarvestedArc MUST match the
  ResourceView literal policy (language preference / stable plural order) and
  MUST NOT depend on raw `graph.value` selection

#### Scenario: Existing Schema.org harvest-stability tests remain green

- **WHEN** the existing Schema.org unit tests for identifier stability,
  keyword/description determinism, contacts/authors, and publisher comments run
- **THEN** they MUST pass without weakening blank-node or order invariants

## MODIFIED Requirements

### Requirement: LinkedDataMapper.map_graph returns HarvestedArc

The system SHALL provide a `LinkedDataMapper` ABC whose `map_graph` method
accepts an `rdflib.Graph` and an optional `MappingContext` and returns a
`HarvestedArc`. Implementations MUST build the value via
`HarvestedArc.from_arctrl` (or equivalent) so the orchestrator receives
serialized ARC JSON plus composition counts without re-parsing RO-Crate JSON.
The mapper MUST NOT return a bare JSON string.

#### Scenario: Successful map produces HarvestedArc

- **WHEN** `map_graph` is called with a mappable graph
- **THEN** the return type is `HarvestedArc`, not `str`

#### Scenario: Map without context remains valid

- **WHEN** `map_graph` is called with a mappable graph and no MappingContext
- **THEN** the return type is still `HarvestedArc` when the vocabulary mapper
  can resolve required fields without discovery context
