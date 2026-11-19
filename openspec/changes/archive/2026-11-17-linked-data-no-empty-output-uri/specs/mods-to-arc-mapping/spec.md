# Spec Delta

## ADDED Requirements

### Requirement: Assay Output URI MUST NOT be empty

The MODS Assay `Measurement` table MUST have an `Output [URI]` column only when a URL is known for the record, and MUST
NOT write an empty `Output [URI]` value. When the table would then have no columns, the Assay MUST NOT have an
annotation table.

#### Scenario: Record without a URL

- **GIVEN** a MODS record whose source URL is missing or not http(s)
- **WHEN** it is mapped
- **THEN** the Assay table has no `Output [URI]` column and the RO-Crate `@graph` has no `URI` entity with an empty
  value

#### Scenario: Record with a URL

- **GIVEN** a MODS record harvested from an http(s) source URL
- **WHEN** it is mapped
- **THEN** `Output [URI]` is that source URL, unchanged

#### Scenario: Record without a URL and without comments

- **GIVEN** a MODS record whose source URL is missing or not http(s), and no field that yields an Assay comment
- **WHEN** it is mapped
- **THEN** the Assay has no annotation table

#### Scenario: Record without a URL but with comments

- **GIVEN** a MODS record whose source URL is missing or not http(s), with a licence
- **WHEN** it is mapped
- **THEN** the Assay table has one row with only the comment columns
