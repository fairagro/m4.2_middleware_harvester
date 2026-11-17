# Spec Delta

## ADDED Requirements

### Requirement: Assay Output URI MUST NOT be empty

The schema.org Assay `Measurement` table MUST have an `Output [URI]` column only when a URL is known for the record, and
MUST NOT write an empty `Output [URI]` value. When the table would then have no columns, the Assay MUST NOT have an
annotation table.

#### Scenario: Record without a URL

- **GIVEN** a schema.org Dataset with no `url`, `sameAs`, http(s) `@id`, DOI or source URL
- **WHEN** it is mapped
- **THEN** the Assay table has no `Output [URI]` column and the RO-Crate `@graph` has no `URI` entity with an empty
  value

#### Scenario: Record with a URL

- **GIVEN** a schema.org Dataset with `url` `https://example.org/ds/1`
- **WHEN** it is mapped
- **THEN** `Output [URI]` is `https://example.org/ds/1`, unchanged

#### Scenario: Record without a URL and without comments

- **GIVEN** a schema.org Dataset with no `url`, `sameAs`, http(s) `@id`, DOI or source URL, and no field that yields an
  Assay comment
- **WHEN** it is mapped
- **THEN** the Assay has no annotation table

#### Scenario: Record without a URL but with comments

- **GIVEN** a schema.org Dataset with no `url`, `sameAs`, http(s) `@id`, DOI or source URL, with a licence
- **WHEN** it is mapped
- **THEN** the Assay table has one row with only the comment columns
