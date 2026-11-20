# Spec Delta

## ADDED Requirements

### Requirement: Spatial Sampling table MUST NOT invent a source

The Regal Study `Spatial Sampling` table MUST NOT contain an `Input [Source Name]` column, because no source field names
a source material. Its parameter columns (`Location`, `Coordinates`) and its `Selected Location(s)` output MUST be
unchanged, and the table MUST still be omitted when the record has no spatial information.

#### Scenario: Record with spatial information mapped without an invented source

- **GIVEN** a Regal record with `recordingLocation` and/or `recordingCoordinates` (Publisso)
- **WHEN** it is mapped
- **THEN** the `Spatial Sampling` table has no `Input [Source Name]` column, the RO-Crate `@graph` has no
  `#Source_Geographic_Region` entity, and its parameter columns (`Location`, `Coordinates`) keep their values

#### Scenario: Record without spatial information has no Spatial Sampling table

- **GIVEN** a Regal record without spatial information
- **WHEN** it is mapped
- **THEN** the Study has no `Spatial Sampling` table
