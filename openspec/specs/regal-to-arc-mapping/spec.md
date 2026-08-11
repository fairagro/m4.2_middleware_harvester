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
