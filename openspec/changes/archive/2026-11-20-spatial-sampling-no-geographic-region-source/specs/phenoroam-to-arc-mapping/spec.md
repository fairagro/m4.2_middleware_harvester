# Spec Delta

## ADDED Requirements

### Requirement: Spatial Sampling table MUST NOT invent a source

The PhenoROAM Study `Spatial Sampling` table MUST NOT contain an `Input [Source Name]` column, because no source field
names a source material. Its parameter columns (`Bounding Box`) and its `Selected Location` output MUST be unchanged,
and the table MUST still be omitted when the record has no spatial information.

#### Scenario: Record with spatial information mapped without an invented source

- **GIVEN** a PhenoROAM record with a complete bbox
- **WHEN** it is mapped
- **THEN** the `Spatial Sampling` table has no `Input [Source Name]` column, the RO-Crate `@graph` has no
  `#Source_Geographic_Region` entity, and its parameter columns (`Bounding Box`) keep their values

#### Scenario: Record without spatial information has no Spatial Sampling table

- **GIVEN** a PhenoROAM record without spatial information
- **WHEN** it is mapped
- **THEN** the Study has no `Spatial Sampling` table
