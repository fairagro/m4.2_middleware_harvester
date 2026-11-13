# Spec Delta

## ADDED Requirements

### Requirement: Assay table MUST NOT invent an input source

The Regal Assay `Measurement` table MUST NOT contain an `Input [Source Name]` column, because no source field names the
material the dataset was produced from. `Output [URI]` and the Assay comments are not affected.

#### Scenario: Record mapped without an invented input

- **GIVEN** a Regal ResearchData record with a DOI
- **WHEN** it is mapped
- **THEN** the Assay table has no `Input [Source Name]` column, the RO-Crate `@graph` has no `#Source_Dataset_Source`
  entity, and `Output [URI]` is unchanged
