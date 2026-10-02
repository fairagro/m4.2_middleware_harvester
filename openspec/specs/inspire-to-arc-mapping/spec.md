# INSPIRE-to-ARC Mapping

## Purpose

Transforms the fully populated `InspireRecord` object into ARC investigation components (ISA).

**Authoritative Mapping Source:** [docs/inspire_mapping.md](../../../docs/inspire_mapping.md) defines the conceptual
mapping rules. This spec captures the implementation contract.

**Skill Reference:** Agents must load `.agents/skills/arctrl/SKILL.md` when writing or modifying code that constructs
`ArcInvestigation`, `ArcStudy`, or `ArcAssay` objects.

## Requirements

### Requirement: Map each InspireRecord to exactly one ArcInvestigation with title, description,…

The system SHALL map each `InspireRecord` to exactly one `ArcInvestigation` with title, description, contacts,
publications, and ontology annotations as defined in the authoritative mapping source. The mapping implementation SHALL
live in `middleware.payload` as the shared `inspire_general` `DataMapper` (accepting `PayloadKind.inspire_record`).
Protocol plugins MUST NOT embed a second ISO→ARC implementation.

#### Scenario: Satisfies — Map each InspireRecord to exactly one ArcInvestigation with title, description,…

- **WHEN** the conditions described by this requirement apply
- **THEN** Map each `InspireRecord` to exactly one `ArcInvestigation` with title, description, contacts, publications,
  and ontology annotations as defined in the authoritative mapping source

#### Scenario: Shared mapper owns the mapping

- **WHEN** an INSPIRE (or future ISO) harvest path maps a record to ARC
- **THEN** mapping is performed by the registered `inspire_general` DataMapper in `middleware.payload`

### Requirement: Create one ArcStudy per record containing a Spatial Sampling protocol…

The system SHALL create one `ArcStudy` per record containing a Spatial Sampling protocol (omitted for
`nonGeographicDataset`) and a Data Acquisition protocol.

#### Scenario: Satisfies — Create one ArcStudy per record containing a Spatial Sampling protocol…

- **WHEN** the conditions described by this requirement apply
- **THEN** Create one `ArcStudy` per record containing a Spatial Sampling protocol (omitted for `nonGeographicDataset`)
  and a Data Acquisition protocol

### Requirement: Create one ArcAssay per record containing a Data Processing protocol

The system SHALL create one `ArcAssay` per record containing a Data Processing protocol.

#### Scenario: Satisfies — Create one ArcAssay per record containing a Data Processing protocol

- **WHEN** the conditions described by this requirement apply
- **THEN** Create one `ArcAssay` per record containing a Data Processing protocol

### Requirement: Serialize the resulting ARC via arc.ToROCrateJsonString() and return the JSON…

The system SHALL serialize the resulting ARC via `arc.ToROCrateJsonString()` and return the JSON string.

#### Scenario: Satisfies — Serialize the resulting ARC via arc.ToROCrateJsonString() and return the JSON…

- **WHEN** the conditions described by this requirement apply
- **THEN** Serialize the resulting ARC via `arc.ToROCrateJsonString()` and return the JSON string

### Requirement: Skip the Spatial Sampling protocol when record.hierarchy == "nonGeographicDataset"

The system SHALL skip the Spatial Sampling protocol when `record.hierarchy == "nonGeographicDataset"`.

#### Scenario: Satisfies — Skip the Spatial Sampling protocol when record.hierarchy == "nonGeographicDataset"

- **WHEN** the conditions described by this requirement apply
- **THEN** Skip the Spatial Sampling protocol when `record.hierarchy == "nonGeographicDataset"`

### Requirement: Skip records whose hierarchy is not in ["dataset", "series", "nonGeographicDataset"]

The system SHALL skip records whose hierarchy is not in `["dataset", "series", "nonGeographicDataset"]`.

#### Scenario: Satisfies — Skip records whose hierarchy is not in ["dataset", "series", "nonGeographicDataset"]

- **WHEN** the conditions described by this requirement apply
- **THEN** Skip records whose hierarchy is not in `["dataset", "series", "nonGeographicDataset"]`

### Requirement: Publication authors MUST come from author-role contacts in initial-space-last form

`InspireMapper` MUST fill `Publication.authors` from Investigation contacts whose role is `author`, matched
case-insensitively (the CSW role `author` is stored as NCIT label `Author`), in contact order. Each author MUST be
formatted `F. Last` (or the single available name part) and joined by `; `, via the shared
`middleware.payload.person_contacts.publication_authors` helper also used by the Regal and Schema.org mappers. The
`Last, F.` form MUST NOT be used, because the RO-Crate writer splits `Publication.authors` on `,`.

#### Scenario: Author role is matched despite the NCIT label

- **WHEN** a record has a contact `John Doe` with role `author` and a DOI resource identifier
- **THEN** the DOI Publication MUST have authors `J. Doe`

#### Scenario: Several authors survive RO-Crate serialization

- **WHEN** a record has author contacts `John Doe` and `Rita Roe` and a DOI resource identifier
- **THEN** the Publication authors MUST be `J. Doe; R. Roe`, and the RO-Crate MUST contain exactly one `#Author_*` node,
  `#Author_J. Doe; R. Roe`
