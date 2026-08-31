# Regal-to-ARC Mapping

## Purpose

Transforms a Regal `ResearchData` RDF graph (from inline `/find` JSON-LD) into ARC
investigation components (ISA).

**Authoritative Mapping Source:** [docs/regal_mapping.md](../../../docs/regal_mapping.md)
defines the conceptual mapping rules. This spec captures the implementation contract.

**Skill Reference:** Agents must load `.agents/skills/arctrl/SKILL.md` when writing or
modifying code that constructs `ArcInvestigation`, `ArcStudy`, or `ArcAssay` objects.

## Requirements

### Requirement: Map each Regal ResearchData graph to exactly one ArcInvestigation with…
The system SHALL map each Regal `ResearchData` graph to exactly one `ArcInvestigation` with title, description, contacts, publications, and comments as defined in the authoritative mapping source.

#### Scenario: Satisfies — Map each Regal ResearchData graph to exactly one ArcInvestigation with…
- **WHEN** the conditions described by this requirement apply
- **THEN** Map each Regal `ResearchData` graph to exactly one `ArcInvestigation` with title, description, contacts, publications, and comments as defined in the authoritative mapping source

### Requirement: Create one ArcStudy per record containing a Data Collection protocol…
The system SHALL create one `ArcStudy` per record containing a Data Collection protocol (when applicable) and a Data Processing protocol.

#### Scenario: Satisfies — Create one ArcStudy per record containing a Data Collection protocol…
- **WHEN** the conditions described by this requirement apply
- **THEN** Create one `ArcStudy` per record containing a Data Collection protocol (when applicable) and a Data Processing protocol

### Requirement: Create a Spatial Sampling protocol on the Study only when…
The system SHALL create a Spatial Sampling protocol on the Study only when `recordingCoordinates` and/or `recordingLocation` are present.

#### Scenario: Satisfies — Create a Spatial Sampling protocol on the Study only when…
- **WHEN** the conditions described by this requirement apply
- **THEN** Create a Spatial Sampling protocol on the Study only when `recordingCoordinates` and/or `recordingLocation` are present

### Requirement: Create one ArcAssay per record with a single-row annotation table…
The system SHALL create one `ArcAssay` per record with a single-row annotation table (`Output [URI]`, license/language/`hasPart` comments as specified).

#### Scenario: Satisfies — Create one ArcAssay per record with a single-row annotation table…
- **WHEN** the conditions described by this requirement apply
- **THEN** Create one `ArcAssay` per record with a single-row annotation table (`Output [URI]`, license/language/`hasPart` comments as specified)

### Requirement: Serialize the resulting ARC via arc.ToROCrateJsonString() and return the JSON…
The system SHALL serialize the resulting ARC via `arc.ToROCrateJsonString()` and return the JSON string.

#### Scenario: Satisfies — Serialize the resulting ARC via arc.ToROCrateJsonString() and return the JSON…
- **WHEN** the conditions described by this requirement apply
- **THEN** Serialize the resulting ARC via `arc.ToROCrateJsonString()` and return the JSON string

### Requirement: Reject (mapping error) graphs that are not Regal ResearchData or…
The system SHALL reject (mapping error) graphs that are not Regal ResearchData or that lack both `@id` and `doi`.

#### Scenario: Satisfies — Reject (mapping error) graphs that are not Regal ResearchData or…
- **WHEN** the conditions described by this requirement apply
- **THEN** Reject (mapping error) graphs that are not Regal ResearchData or that lack both `@id` and `doi`

### Requirement: Implement mapping in a dedicated Regal mapper registered under the…
The system SHALL implement mapping in a dedicated Regal mapper registered under the Regal `payload_type`; do not reuse `GeneralSchemaOrgMapper`.

#### Scenario: Satisfies — Implement mapping in a dedicated Regal mapper registered under the…
- **WHEN** the conditions described by this requirement apply
- **THEN** Implement mapping in a dedicated Regal mapper registered under the Regal `payload_type`; do not reuse `GeneralSchemaOrgMapper`

### Requirement: Edge case — - Missing title
The system SHALL handle this edge case: when - Missing title, then use `prefLabel` if present; otherwise `"Untitled"`. - `prefLabel` without `", "` → entire string as `Person.LastName`. - Empty `hasPart` → omit Online Resource comment columns. - Duplicate funder information in flat and `joinedFunding` fields → prefer `joinedFunding`.

#### Scenario: Edge case — - Missing title
- **WHEN** - Missing title
- **THEN** use `prefLabel` if present; otherwise `"Untitled"`. - `prefLabel` without `", "` → entire string as `Person.LastName`. - Empty `hasPart` → omit Online Resource comment columns. - Duplicate funder information in flat and `joinedFunding` fields → prefer `joinedFunding`

### Requirement: Regal Person contacts MUST satisfy given-name rules

`RegalMapper` MUST apply the `person-contact-given-name` rules to contacts
derived from `dcterms:creator` / `dcterms:contributor` (literal or labelled
nodes). A `skos:prefLabel` without `", "` that yields an empty given name MUST
NOT produce a Person contact with empty first name; such a contact MUST cause
fail-closed mapping failure for that record unless the node is treated as an
organization and represented via Comment / Affiliation instead of Person.

Authoritative field tables remain in [docs/regal_mapping.md](../../../docs/regal_mapping.md);
this requirement overrides any reading that allows empty FirstName on contacts.

#### Scenario: Comma-split prefLabel with given name succeeds

- **WHEN** a creator node has `prefLabel` `Fuerst, Julia`
- **THEN** the mapper MUST emit a Person with LastName `Fuerst` and FirstName
  `Julia`

#### Scenario: Org-style prefLabel without given name is not an empty-given Person

- **WHEN** a creator or contributor node has a `prefLabel` with no `", "`
  separator (entire label would become LastName with empty FirstName), and the
  node represents an organization/institution rather than a parseable person
- **THEN** the mapper MUST NOT append a Person with empty FirstName; it MUST
  either represent the agent via Investigation comment / Affiliation or fail
  closed per `person-contact-given-name`

#### Scenario: Person-like label without given name fails closed

- **WHEN** a creator would map to a Person with empty FirstName and is not
  represented as an organization comment/affiliation instead
- **THEN** `map_graph` MUST raise a mapping error and MUST NOT return a
  HarvestedArc

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

### Requirement: Regal mapper string helpers MUST NOT persist rdflib blank-node labels

`RegalMapper` string extraction used for ARC fields (including Funding Program, Project ID, Funder, and any other values obtained via the mapper's single- and multi-value string helpers) MUST NOT return or embed rdflib blank-node labels (`N` plus 32 hex digits, or `_:…`). For each RDF object:

- Literal → use the literal text;
- URIRef → use the IRI string;
- blank node → use `skos:prefLabel` when present; otherwise omit that object.

Unlabelled blank nodes MUST be skipped rather than stringified. Authoritative field placement for funding remains [`docs/regal_mapping.md`](../../../docs/regal_mapping.md) §6.

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

### Requirement: Regal contributorOrder MUST NOT become an Investigation Comment

The predicate `http://hbz-nrw.de/regal#contributorOrder` (`regal:contributorOrder`) MUST be treated as known mapping metadata and MUST NOT be emitted as an opaque Investigation Comment. Per [`docs/regal_mapping.md`](../../../docs/regal_mapping.md), `contributorOrder` is intended to order Contacts when stable order keys are available; implementing that ordering is optional and MUST NOT use blank-node strings as order keys.

#### Scenario: contributorOrder blank node does not create a Comment

- **WHEN** a Regal ResearchData graph includes `regal:contributorOrder` pointing at a blank node without `skos:prefLabel`
- **THEN** the mapped ARC MUST NOT contain an Investigation Comment named `contributorOrder`, and Comment text / `@id` values MUST NOT match an rdflib blank-node label

#### Scenario: Two harvests of the same logical payload yield the same Comment set for contributorOrder

- **WHEN** the same Regal ResearchData payload (including `contributorOrder` blank nodes) is mapped twice with freshly allocated blank-node identities
- **THEN** both mappings MUST produce the same set of Investigation Comment names and texts with respect to `contributorOrder` (no harvest-unstable `contributorOrder` Comment)
