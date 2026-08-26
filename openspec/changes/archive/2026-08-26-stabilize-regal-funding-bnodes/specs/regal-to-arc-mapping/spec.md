## ADDED Requirements

### Requirement: Regal mapper string helpers MUST NOT persist rdflib blank-node labels

`RegalMapper` string extraction used for ARC fields (including Funding Program, Project ID, Funder, and any other values obtained via the mapper's single- and multi-value string helpers) MUST NOT return or embed rdflib blank-node labels (`N` plus 32 hex digits, or `_:…`). For each RDF object:

- Literal → use the literal text;
- URIRef → use the IRI string;
- blank node → use `skos:prefLabel` when present; otherwise omit that object.

Unlabelled blank nodes MUST be skipped rather than stringified. Authoritative field placement for funding remains [`docs/regal_mapping.md`](../../../../docs/regal_mapping.md) §6.

#### Scenario: Flat fundingProgram blank node without prefLabel is omitted

- **WHEN** a Regal ResearchData graph has `regal:fundingProgram` pointing at a blank node without `skos:prefLabel` (and no `joinedFunding` that supplies a stable program)
- **THEN** the mapped ARC MUST NOT contain a Funding Program value matching an rdflib blank-node label, and MUST NOT invent a program string from `str(BNode)`

#### Scenario: Flat fundingProgram blank node with prefLabel is kept

- **WHEN** a Regal ResearchData graph has `regal:fundingProgram` pointing at a blank node with `skos:prefLabel` `"NFDI Consortium"`
- **THEN** the mapped ARC MUST include Funding Program text `NFDI Consortium`

#### Scenario: Joined fundingProgramJoined blank node without prefLabel is omitted

- **WHEN** `joinedFunding` is present and `fundingProgramJoined` (or `projectIdJoined`) resolves to a blank node without `skos:prefLabel`
- **THEN** that program/project value MUST be omitted from Data Processing parameters and MUST NOT appear as an rdflib blank-node label in the ARC JSON

#### Scenario: Two mappings with fresh blank-node ids yield stable funding fields

- **WHEN** the same logical Regal funding payload (blank-node objects for program/project, with or without prefLabels as in the fixture) is mapped twice with freshly allocated blank-node identities
- **THEN** both mappings MUST produce the same Funding Program / Project ID / Funder string values (no harvest-unstable `N…` labels)
