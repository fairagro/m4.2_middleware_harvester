# INSPIRE-to-ARC Mapping

## Purpose

Transforms the fully populated `InspireRecord` object into ARC investigation components (ISA).

**Authoritative Mapping Source:** [docs/inspire_mapping.md](../../../../docs/inspire_mapping.md) defines the conceptual mapping rules. This spec captures the implementation contract.

**Skill Reference:** Agents must load `.agents/skills/arctrl/SKILL.md` when writing or modifying code that constructs `ArcInvestigation`, `ArcStudy`, or `ArcAssay` objects.

## Requirements

### Requirement: Map each InspireRecord to exactly one ArcInvestigation with title, description,…
The system SHALL map each `InspireRecord` to exactly one `ArcInvestigation` with title, description, contacts, publications, and ontology annotations as defined in the authoritative mapping source.

#### Scenario: Satisfies — Map each InspireRecord to exactly one ArcInvestigation with title, description,…
- **WHEN** the conditions described by this requirement apply
- **THEN** Map each `InspireRecord` to exactly one `ArcInvestigation` with title, description, contacts, publications, and ontology annotations as defined in the authoritative mapping source

### Requirement: Create one ArcStudy per record containing a Spatial Sampling protocol…
The system SHALL create one `ArcStudy` per record containing a Spatial Sampling protocol (omitted for `nonGeographicDataset`) and a Data Acquisition protocol.

#### Scenario: Satisfies — Create one ArcStudy per record containing a Spatial Sampling protocol…
- **WHEN** the conditions described by this requirement apply
- **THEN** Create one `ArcStudy` per record containing a Spatial Sampling protocol (omitted for `nonGeographicDataset`) and a Data Acquisition protocol

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
