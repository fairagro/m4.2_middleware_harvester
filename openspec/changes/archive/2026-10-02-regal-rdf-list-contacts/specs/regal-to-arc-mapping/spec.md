## ADDED Requirements

### Requirement: Regal contacts MUST resolve rdf:List creator and contributor values in list order

The Publisso/Regal JSON-LD context declares `creator` and `contributor` with `"@container": "@list"`, so a parsed
record has one `dcterms:creator` / `dcterms:contributor` triple whose object is an `rdf:List` head. `RegalMapper` MUST
map every list member through the same contact path as a directly attached value (literal → label; resource →
`skos:prefLabel` "Family, Given", ORCID Comment for `orcid.org` IRIs, organization labels → Comment), and MUST keep
list order (source author order). Directly attached values (no list) keep their StableGraph order. A list head MUST
NOT be treated as an agent itself. A creator or contributor resource without `skos:prefLabel` MUST be skipped with a
logged warning (never silently, never with a blank-node label in the message or ARC).

#### Scenario: Real Publisso creator list keeps order and ORCIDs

- **WHEN** the `/find` record `frl:6420709` (six creators as JSON-LD `@list`, four with ORCID `@id`) is mapped
- **THEN** the Investigation MUST have six author Contacts in source order (Janke, Willink, Hempel, Amon B., Römer,
  Amon T.) and ORCID Comments only on the four ORCID creators

#### Scenario: Contributor list with an organization label

- **WHEN** a `dcterms:contributor` list contains a person (`Hempel, Sabrina`) and an organization (`NFDI4Health`)
- **THEN** the person MUST become a contributor Contact and the organization a `Contributor` Investigation Comment

#### Scenario: Empty list

- **WHEN** `dcterms:creator` is `rdf:nil` (JSON-LD `"creator": []`)
- **THEN** no Contact is created and no warning is logged

#### Scenario: Unlabelled list member

- **WHEN** a creator list member has no `skos:prefLabel`
- **THEN** it MUST be skipped with a warning, and the other members MUST still be mapped

### Requirement: Regal Publication authors MUST use initial-space-last form without commas

The RO-Crate writer splits `Publication.authors` on `,`. `RegalMapper` MUST format each author as `F. Last` joined by
`; ` (same rule as `GeneralSchemaOrgMapper` in `linked-data-mapper`), and MUST NOT use the `Last, F.` form.

#### Scenario: Publication authors for frl:6420709

- **WHEN** `frl:6420709` is mapped
- **THEN** the Publication authors string MUST be `D. Janke; D. Willink; S. Hempel; B. Amon; A. Römer; T. Amon` and no
  `#Author_*` node MUST start with a stray `" "` fragment
