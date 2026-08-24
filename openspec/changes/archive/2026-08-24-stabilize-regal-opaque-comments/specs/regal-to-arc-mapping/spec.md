## ADDED Requirements

### Requirement: Regal opaque Comments MUST NOT embed rdflib blank-node labels

When mapping Regal `ResearchData` to ARC Investigation Comments from predicates that are not otherwise handled, the mapper MUST NOT persist rdflib blank-node labels (`N` plus 32 hex digits, or `_:…`) as Comment text or Comment identity. For a non-Literal object: if the node is a blank node and has no `skos:prefLabel`, the Comment MUST be omitted; Literals, `http(s)`/`URIRef` objects, and nodes with `skos:prefLabel` MAY still become Comments. The same blank-node rule MUST apply to analogous Regal label helpers that currently fall back to stringifying an object node (including OAI/catalog/funding label paths that use `prefLabel or str(obj)`).

#### Scenario: Opaque unknown predicate with unlabelled blank node is skipped

- **WHEN** a Regal ResearchData subject has an unknown predicate whose object is a blank node without `skos:prefLabel`
- **THEN** mapping MUST NOT append an Investigation Comment for that predicate/object, and the resulting ARC JSON MUST NOT contain Comment text matching an rdflib blank-node label

#### Scenario: Opaque blank node with prefLabel remains

- **WHEN** a Regal ResearchData subject has an unknown predicate whose object is a blank node with `skos:prefLabel` `"Stable Label"`
- **THEN** mapping MUST append an Investigation Comment whose text is `Stable Label`

#### Scenario: Opaque Literal and URIRef remain

- **WHEN** a Regal ResearchData subject has an unknown predicate whose object is a Literal or a URIRef
- **THEN** mapping MUST append an Investigation Comment using the literal value or the URI string

### Requirement: Regal contributorOrder MUST NOT become an Investigation Comment

The predicate `http://hbz-nrw.de/regal#contributorOrder` (`regal:contributorOrder`) MUST be treated as known mapping metadata and MUST NOT be emitted as an opaque Investigation Comment. Per [`docs/regal_mapping.md`](../../../../docs/regal_mapping.md), `contributorOrder` is intended to order Contacts when stable order keys are available; implementing that ordering is optional for this change and MUST NOT use blank-node strings as order keys.

#### Scenario: contributorOrder blank node does not create a Comment

- **WHEN** a Regal ResearchData graph includes `regal:contributorOrder` pointing at a blank node without `skos:prefLabel`
- **THEN** the mapped ARC MUST NOT contain an Investigation Comment named `contributorOrder`, and Comment text / `@id` values MUST NOT match an rdflib blank-node label

#### Scenario: Two harvests of the same logical payload yield the same Comment set for contributorOrder

- **WHEN** the same Regal ResearchData payload (including `contributorOrder` blank nodes) is mapped twice with freshly allocated blank-node identities
- **THEN** both mappings MUST produce the same set of Investigation Comment names and texts with respect to `contributorOrder` (no harvest-unstable `contributorOrder` Comment)
