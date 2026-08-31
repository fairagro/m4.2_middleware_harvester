## ADDED Requirements

### Requirement: RegalMapper MUST use ResourceView for ARC-bound RDF field access

`RegalMapper` MUST obtain ResearchData field values used for ARC text
(titles, descriptions, dates, contacts' RDF properties, funding strings,
keywords, licenses, labelled resources, opaque Investigation Comment text, and
analogous Study/Assay protocol parameters) via the StableGraph / ResourceView
access layer supplied to `_map_graph`. It MUST wrap the graph with a Regal
label policy that includes `skos:prefLabel` for labelled-node resolution. It
MUST NOT use `graph.value` for ARC-bound string fields, MUST NOT persist
`str(BNode)` into ARC text, and MUST NOT keep parallel private copies of
shared literal/resource / BNode-safe string helpers once ResourceView provides
them. Regal-specific ARC policy — PUBLISSO `Family, Given` splitting,
`joinedFunding` preference over flat funding fields, resource base URL /
compact Regal id handling, opaque known-predicate filtering, and Investigation
identifier cascade — MUST remain in the mapper. Authoritative field placement
remains [`docs/regal_mapping.md`](../../../../docs/regal_mapping.md).

#### Scenario: Title and description come from ResourceView accessors

- **WHEN** a Regal ResearchData graph is mapped after the ResourceView migration
- **THEN** Investigation title and description strings in the HarvestedArc MUST
  match ResourceView text / multi-literal policy and MUST NOT depend on raw
  `graph.value` selection for those fields

#### Scenario: Private string helpers are gone

- **WHEN** the Regal mapper implementation is reviewed after this change
- **THEN** it MUST NOT define private `_str` / `_strs` / `_term_text` /
  `_labelled_nodes` (or equivalent duplicate BNode-stringifying helpers) for
  ARC field extraction

#### Scenario: Existing Regal BNode and opaque stability tests remain green

- **WHEN** the existing Regal unit tests for funding BNode omission, opaque
  unlabelled blank-node skip, and double-map funding/comment stability run
- **THEN** they MUST pass without weakening blank-node or order invariants

### Requirement: Regal multi-value and contact order MUST be harvest-stable

When multiple RDF objects contribute to hash-relevant ARC content (Investigation
Contacts from `dcterms:creator` / `dcterms:contributor`, multi-value string
fields joined into Comments or protocol parameters, labelled keyword /
institution lists, and opaque Investigation Comments for unknown predicates),
`RegalMapper` MUST emit a deterministic order that does not depend on rdflib
iteration order or parser-local blank-node labels. Implementing
`regal:contributorOrder`-based Contact sorting remains optional and out of
scope for this requirement.

#### Scenario: Creator blank-node order permutation yields same Contacts

- **WHEN** the same logical Regal ResearchData payload with multiple blank-node
  creators is mapped twice with permuted RDF object order / freshly allocated
  blank-node identities
- **THEN** both mappings MUST produce the same ordered Investigation Contact
  names (and MUST NOT embed rdflib blank-node labels)

#### Scenario: Opaque unknown predicates are order-stable

- **WHEN** a Regal ResearchData subject has multiple unknown predicates with
  Literal or labelled objects and the triples are presented in different orders
  across two parses
- **THEN** both mappings MUST produce the same set and relative order of opaque
  Investigation Comment names and texts for those predicates

## MODIFIED Requirements

### Requirement: Regal mapper string helpers MUST NOT persist rdflib blank-node labels

`RegalMapper` string extraction used for ARC fields (including Funding Program,
Project ID, Funder, and any other values obtained via StableGraph / ResourceView
text accessors) MUST NOT return or embed rdflib blank-node labels (`N` plus 32
hex digits, or `_:…`). For each RDF object:

- Literal → use the literal text;
- URIRef → use the IRI string;
- blank node → use `skos:prefLabel` when present; otherwise omit that object.

Unlabelled blank nodes MUST be skipped rather than stringified. Authoritative
field placement for funding remains [`docs/regal_mapping.md`](../../../../docs/regal_mapping.md) §6.
Private Regal-only duplicates of this policy MUST NOT remain after the
ResourceView migration.

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
