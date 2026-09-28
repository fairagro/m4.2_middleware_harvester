## ADDED Requirements

### Requirement: ResourceView property reads may resolve against a fallback-subject chain

A ResourceView MAY be constructed with an ordered chain of fallback subjects. When the view's primary subject yields no
objects for the requested predicates, the system SHALL retry the read against each fallback subject in chain order and
return the first non-empty result. Results from different subjects MUST NOT be merged. The chain MUST be applied
per-read, so two different properties MAY resolve against two different subjects.

A view's identity accessors — its underlying node, its public IRI, and its RDF type test — MUST ignore the chain and
report only the primary subject.

Views returned by resource accessors MUST NOT inherit the chain: traversal that leaves the primary subject resolves
against that object alone.

The chain MUST be applied at most one level deep — a fallback subject's own chain (if any) MUST NOT be consulted.

#### Scenario: Absent property resolves against the fallback subject

- **GIVEN** a primary subject with no `schema:description` and a fallback subject with `schema:description` "Soil
  moisture across three sites"
- **WHEN** the description is read through a view built with that fallback chain
- **THEN** the value is "Soil moisture across three sites"

#### Scenario: Present property does not fall back

- **GIVEN** a primary subject with `schema:creator` naming one Person and a fallback subject with `schema:creator`
  naming twelve Persons
- **WHEN** the creators are read through a view built with that fallback chain
- **THEN** exactly the primary subject's one Person is returned, and the fallback's twelve are not appended

#### Scenario: Identity never falls back

- **GIVEN** a primary subject `https://example.org/rec/1#record` with a fallback subject `https://example.org/paper/9`
- **WHEN** the view's node, IRI and RDF type test are read
- **THEN** they describe `https://example.org/rec/1#record` only

#### Scenario: Nested views are plain

- **GIVEN** a primary subject whose `schema:creator` Person has no `schema:affiliation`, and a fallback subject whose
  own `schema:affiliation` is "UFZ"
- **WHEN** the affiliation is read from the Person view reached through the primary subject
- **THEN** no affiliation is returned — the Person view does not inherit the chain

#### Scenario: Chain order decides

- **GIVEN** a primary subject with no `schema:url`, a first fallback with `schema:url`
  `https://example.org/a`, and a second fallback with `schema:url` `https://example.org/b`
- **WHEN** the url is read through a view built with both fallbacks in that order
- **THEN** the value is `https://example.org/a`

#### Scenario: Ordering guarantees survive the fallback

- **GIVEN** the same logical set of fallback literals presented in two different RDF object iteration orders
- **WHEN** a plural literal accessor resolves through the chain
- **THEN** it returns the same ordered list both times

## MODIFIED Requirements

### Requirement: DOI helper accepts Literal, IRI, and typed PropertyValue nodes

The access layer SHALL provide a DOI extraction helper that accepts a literal or IRI whose normalized value starts with
`10.` (optional `https://doi.org/` / `http://doi.org/` / `doi:` prefix MAY be stripped). When wrap-time
`term_namespaces` are configured, the helper MUST also accept an RDF node that has `rdf:type` Schema.org `PropertyValue`
(in any configured term namespace), whose `propertyID` indicates DOI (identifiers.org DOI URI or contains `doi`,
case-insensitive), and whose value starts with `10.`. Nodes that carry `propertyID`/`value` without that `PropertyValue`
type MUST NOT yield a DOI via this path. The helper MUST NOT invent identifiers, MUST NOT return blank-node labels, and
MUST NOT decide ARC Investigation.identifier / Publication / Comment policy — that remains vocabulary-mapper
responsibility.

When the view carries a fallback-subject chain, the DOI helper SHALL fall back when the primary subject yields **no
parsed DOI**, which is a weaker condition than yielding no objects: a subject MAY carry an identifier node that
contains no DOI, and that MUST NOT prevent the fallback.

#### Scenario: PropertyValue DOI is extracted

- **WHEN** an identifier node is a PropertyValue with DOI `propertyID` and value `10.3220/253-2025-42` and Schema.org
  term namespaces are configured
- **THEN** the DOI helper MUST return `10.3220/253-2025-42`

#### Scenario: DOI-like fields without PropertyValue type yield no DOI

- **WHEN** a node has Schema.org `propertyID`/`value` that would otherwise look like a DOI PropertyValue, but has no
  `rdf:type` PropertyValue
- **THEN** the DOI helper MUST return no DOI

#### Scenario: Blank node without DOI fields yields no DOI

- **WHEN** the node is an unlabelled blank node with no DOI PropertyValue fields
- **THEN** the DOI helper MUST return no DOI

#### Scenario: Occupied identifier without a DOI still falls back

- **GIVEN** a primary subject whose `schema:identifier` is a `schema:PropertyValue` carrying only a landing-page url and
  no DOI, and a fallback subject with `schema:identifier` DOI "10.5678/xyz"
- **WHEN** the DOI helper reads through the chain
- **THEN** the normalized DOI "10.5678/xyz" is returned

#### Scenario: Primary DOI wins over fallback DOI

- **GIVEN** a primary subject with DOI "10.1111/primary" and a fallback subject with DOI "10.2222/fallback"
- **WHEN** the DOI helper reads through the chain
- **THEN** only "10.1111/primary" is returned
