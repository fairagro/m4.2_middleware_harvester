# Spec Delta

## ADDED Requirements

### Requirement: Spatial Sampling table MUST NOT invent a source

The INSPIRE Study `Spatial Sampling` table MUST NOT contain an `Input [Source Name]` column, because no source field
names a source material. Its parameter columns (`Bounding Box`, `Coordinate Reference System`, spatial resolution) and
its `Selected Location` output MUST be unchanged, and the table MUST still be omitted when the record has no spatial
information.

#### Scenario: Record with spatial information mapped without an invented source

- **GIVEN** a geographic INSPIRE record with a bounding box (BonaRes)
- **WHEN** it is mapped
- **THEN** the `Spatial Sampling` table has no `Input [Source Name]` column, the RO-Crate `@graph` has no
  `#Source_Geographic_Region` entity, and its parameter columns (`Bounding Box`, `Coordinate Reference System`, spatial
  resolution) keep their values
- **AND** the `Data Acquisition` table still takes `Selected Location` as input

#### Scenario: Record without spatial information has no Spatial Sampling table

- **GIVEN** an INSPIRE record without spatial information
- **WHEN** it is mapped
- **THEN** the Study has no `Spatial Sampling` table
