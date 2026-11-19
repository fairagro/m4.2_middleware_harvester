# Spec Delta

## MODIFIED Requirements

### Requirement: Regal contacts MUST resolve rdf:List creator and contributor values in list order

The Publisso/Regal JSON-LD context declares `creator` and `contributor` with `"@container": "@list"`, so a parsed record
has one `dcterms:creator` / `dcterms:contributor` triple whose object is an `rdf:List` head. `RegalMapper` MUST map
every list member through the same contact path as a directly attached value (literal → label; resource →
`skos:prefLabel` "Family, Given", `Person.ORCID` for `orcid.org` IRIs, organization labels → Comment), and MUST keep
list order (source author order). Directly attached values (no list) keep their StableGraph order. A list head MUST NOT
be treated as an agent itself. A creator or contributor resource without `skos:prefLabel` MUST be skipped with a logged
warning (never silently, never with a blank-node label in the message or ARC) and MUST attach a corresponding dataset
warning on the yielded `HarvestedArc` when mapping still succeeds.

#### Scenario: Real Publisso creator list keeps order and ORCIDs

- **WHEN** the `/find` record `frl:6420709` (six creators as JSON-LD `@list`, four with ORCID `@id`) is mapped
- **THEN** the Investigation MUST have six author Contacts in source order (Janke, Willink, Hempel, Amon B., Römer, Amon
  T.) and `Person.ORCID` only on the four ORCID creators

#### Scenario: Contributor list with an organization label

- **WHEN** a `dcterms:contributor` list contains a person (`Hempel, Sabrina`) and an organization (`NFDI4Health`)
- **THEN** the person MUST become a contributor Contact and the organization a `Contributor` Investigation Comment

#### Scenario: Empty list

- **WHEN** `dcterms:creator` is `rdf:nil` (JSON-LD `"creator": []`)
- **THEN** no Contact is created and no warning is logged
- **AND** the yielded `HarvestedArc` carries no contact-skip warning for that empty list

#### Scenario: Unlabelled list member

- **GIVEN** a creator list member has no `skos:prefLabel` and the rest of the record still maps successfully
- **WHEN** the mapper processes contacts
- **THEN** it MUST be skipped with a warning, and the other members MUST still be mapped
- **AND** the yielded `HarvestedArc` carries a dataset warning about the skipped contact
