# Spec Delta

## ADDED Requirements

### Requirement: Assay Output URI MUST NOT be empty

The PhenoROAM Assay `Measurement` table MUST have an `Output [URI]` column only when a URL is known for the record, and
MUST NOT write an empty `Output [URI]` value. When the table would then have no columns, the Assay MUST NOT have an
annotation table.

#### Scenario: Record without a URL

- **GIVEN** a PhenoROAM record with no catalog id
- **WHEN** it is mapped
- **THEN** the Assay table has no `Output [URI]` column and the RO-Crate `@graph` has no `URI` entity with an empty
  value

#### Scenario: Record with a URL

- **GIVEN** a PhenoROAM record with a catalog id
- **WHEN** it is mapped
- **THEN** `Output [URI]` is its landing URL, unchanged

#### Scenario: Record without a URL and without comments

- **GIVEN** a PhenoROAM record with no catalog id, and no field that yields an Assay comment
- **WHEN** it is mapped
- **THEN** the Assay has no annotation table

#### Scenario: Record without a URL but with comments

- **GIVEN** a PhenoROAM record with no catalog id, with a licence
- **WHEN** it is mapped
- **THEN** the Assay table has one row with only the comment columns
