## ADDED Requirements

### Requirement: Recover absent Dataset metadata from schema:isBasedOn

When a `schema:Dataset` provides no value for a mapped property, the system SHALL resolve that property from the
Dataset's `schema:isBasedOn` targets instead, and SHALL use the Dataset's own value whenever it has one. Resolution is
per-property: different properties MAY resolve against different subjects. Values from the Dataset and from an
`isBasedOn` target MUST NOT be merged into one field.

Multiple `isBasedOn` targets MUST be consulted in deterministic subject order (`StableGraph` sort key), never in RDF
triple insertion order. Only one hop is followed: an `isBasedOn` target's own `isBasedOn` MUST NOT be consulted.

`Investigation.identifier` resolution is unaffected — the identifier cascade continues to resolve against the Dataset
itself, so two Datasets derived from the same work MUST NOT collide.

Every property resolved from an `isBasedOn` target MUST be recorded as an Investigation Comment naming the property and
`isBasedOn` as its source. A recovered value MUST NOT be indistinguishable from a value the provider stated on the
Dataset.

Title resolution is explicitly excluded: the title-fallback cascade (see "Title fallback cascade when schema:name is
missing") is unchanged, and a Dataset with a non-empty `schema:name` keeps that name even when an `isBasedOn` target
carries a different one.

#### Scenario: Thin Dataset recovers description, contacts, url and DOI

- **GIVEN** a `schema:Dataset` with a `schema:name` but no `schema:description`, `schema:creator`, `schema:url`, or DOI,
  whose `schema:isBasedOn` is a `schema:ScholarlyArticle` with an abstract, two authors, a url, and DOI "10.1234/abc"
- **WHEN** the mapper processes the Dataset
- **THEN** the Investigation carries the article's description, both contacts, the url, and a publication with DOI
  "10.1234/abc"
- **AND** an Investigation Comment records `isBasedOn` as the source for each recovered property

#### Scenario: Dataset's own values are preserved

- **GIVEN** a `schema:Dataset` with its own `schema:description` and one `schema:creator`, whose `schema:isBasedOn`
  target has a different description and twelve authors
- **WHEN** the mapper processes the Dataset
- **THEN** the Investigation carries the Dataset's description and exactly its one contact
- **AND** no `isBasedOn` source Comment is added for those properties

#### Scenario: Title is never taken from isBasedOn

- **GIVEN** a `schema:Dataset` with `schema:name` "Knowledge Library metadata for Soil carbon in arable systems" whose
  `schema:isBasedOn` target has `schema:name` "Soil carbon in arable systems"
- **WHEN** the mapper processes the Dataset
- **THEN** the Investigation title is "Knowledge Library metadata for Soil carbon in arable systems"

#### Scenario: Identifier still resolves from the Dataset

- **GIVEN** two `schema:Dataset` subjects with distinct `@id` values whose `schema:isBasedOn` is the same article with
  DOI "10.1234/abc"
- **WHEN** the mapper processes the graph
- **THEN** two Investigations are produced with distinct identifiers derived from their own `@id` values
- **AND** neither identifier is "10.1234/abc"

#### Scenario: Datasets without isBasedOn are unaffected

- **GIVEN** a `schema:Dataset` with no `schema:isBasedOn`
- **WHEN** the mapper processes the Dataset
- **THEN** the resulting ARC is identical to the ARC produced before this capability existed
