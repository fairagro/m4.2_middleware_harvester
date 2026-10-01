# INSPIRE-to-ARC Mapping (delta)

## MODIFIED Requirements

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
