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

### Requirement: The ARC licence MUST come from gmd:otherConstraints

`InspireMapper` MUST set `ARC.License` via `middleware.payload.arc_license.inspire_license`, keeping ARCtrl's default
`LICENSE` path. The licence content MUST be, in order: the first `gmx:Anchor/@xlink:href` that is not an
`inspire.ec.europa.eu` code-list URI; the first GeoNode licence text `Name (id): description`; the first text that
contains a URL on a known licence host. A GeoNode `Not Specified` entry, access notes and other free text MUST NOT
become a licence; then the ARCtrl default "ALL RIGHTS RESERVED BY THE AUTHORS" stays.

#### Scenario: GeoNode licence text

- **WHEN** `otherConstraints` is `CC-BY (CC-BY): https://creativecommons.org/licenses/by/4.0/ (…/legalcode)` followed by
  a disclaimer
- **THEN** the RO-Crate licence node text MUST be the `CC-BY (CC-BY): …` constraint

#### Scenario: No licence specified

- **WHEN** `otherConstraints` is `Not Specified: The original author did not specify a license.`
- **THEN** the RO-Crate licence node text MUST be "ALL RIGHTS RESERVED BY THE AUTHORS"

#### Scenario: Written ARC keeps the licence as a file

- **WHEN** the RO-Crate is read with `ARC.from_rocrate_json_string` and written with `ARC.Write`
- **THEN** the ARC MUST contain a `LICENSE` file with the licence text and no directory named after a URL

### Requirement: The dataset date MUST come from the citation, not gmd:dateStamp

`InspireMapper` MUST set Investigation and Study `SubmissionDate` from the citation `CI_Date` entries: the earliest
`publication` date, else the latest `revision` date, else the earliest `creation` date; without any of these it MUST
stay empty. `gmd:dateStamp` MUST NOT be used as a dataset date; it MUST be kept as the Investigation Comment
`Metadata Date`.

#### Scenario: BonaRes record

- **WHEN** a record has `dateStamp` 2026-08-18T12:06:54Z and a citation `publication` date 2026-05-19T16:11:37Z
- **THEN** `SubmissionDate` MUST be 2026-05-19T16:11:37Z and the `Metadata Date` Comment 2026-08-18T12:06:54Z

#### Scenario: No publication date

- **WHEN** a record has `creation` and `revision` dates only
- **THEN** `SubmissionDate` MUST be the latest `revision` date

#### Scenario: No citation date

- **WHEN** a record has no typed citation date
- **THEN** `SubmissionDate` MUST be empty

### Requirement: DOIs MUST be bare and normalised

`InspireMapper` MUST pass each citation resource identifier code (else its URL) through
`middleware.payload.dois.normalize_doi`, which strips any number of `doi:`, `https://doi.org/`, `https://dx.doi.org/`
and `https://www.doi.org/` prefixes and returns the bare `10.<registrant>/<suffix>` DOI. Each distinct DOI
(case-insensitive) MUST become one Publication with that bare DOI. Codes that are not DOIs MUST NOT become Publications.
The Schema.org and Regal mappers MUST use the same helper.

#### Scenario: GeoNode stacked prefixes

- **WHEN** a resource identifier code is `doi:https://doi.org/10.4228/zalf.vjcp-vep3` with URL
  `https://dx.doi.org/https://doi.org/10.4228/zalf.vjcp-vep3`
- **THEN** the RO-Crate citation `identifier` MUST be `10.4228/zalf.vjcp-vep3`

#### Scenario: Not a DOI

- **WHEN** a resource identifier code is an ISBN or `doi:https://www.ncbi.nlm.nih.gov/…`
- **THEN** no Publication MUST be created for it

### Requirement: Organisation-only creators MUST use `Creator Organization`

An organisation-only `CI_ResponsibleParty` (or an individualName without a given name) whose role is `author`,
`originator` or `principalInvestigator` MUST become the Investigation Comment `Creator Organization` (see
`person-contact-given-name`). Other roles MUST keep the Comment named after the role.

#### Scenario: Thünen Atlas

- **WHEN** a record's only contacts are the organisation `Thünen-Institut Zentrum für Informationsmanagement` as
  originator, author and pointOfContact
- **THEN** the Investigation MUST have one Comment `Creator Organization` and one Comment `Point of Contact` for it, and
  no Person contact

#### Scenario: Owner is not a creator

- **WHEN** an organisation-only contact has role `owner`
- **THEN** it MUST be the Comment `Owner`, not `Creator Organization`

### Requirement: Placeholder values in optional INSPIRE fields MUST be treated as absent

`InspireRecord` and its nested models MUST treat a value of an optional field as absent when the whole value matches
`value_bounds.placeholder_values` (case-insensitive, surrounding whitespace ignored) or is an unrendered `$var`,
`${var}` or `{{var}}` template: a scalar MUST fall back to the field default and list items MUST be removed. The default
list MUST be `None`, `null`, `N/A`, `No abstract provided`, `Keine Zusammenfassung vorhanden` and
`No information provided`. Required fields (`identifier`, `title`, `abstract`) MUST keep their value.

#### Scenario: GeoNode "None" in optional elements

- **WHEN** a record has `purpose` "None", `supplementalInformation` "No information provided" and `graphicOverview`
  ["None", "https://example.com/thumb.png"]
- **THEN** `purpose` and `supplemental_information` MUST be `None` and `graphic_overviews` MUST be
  ["https://example.com/thumb.png"], and the record MUST validate

#### Scenario: Placeholder abstract

- **WHEN** a record has the abstract "No abstract provided"
- **THEN** `abstract` MUST stay "No abstract provided"

#### Scenario: Configured list

- **WHEN** `value_bounds.placeholder_values` is ["Keine Angabe"]
- **THEN** `purpose` "keine angabe" MUST be absent and `edition` "None" MUST be kept
