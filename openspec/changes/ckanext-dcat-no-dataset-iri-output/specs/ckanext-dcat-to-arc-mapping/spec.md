# Spec Delta

## MODIFIED Requirements

### Requirement: Dataset Processing protocol MUST NOT invent input or output entities

The ckanext-dcat mapper's Study "Dataset Processing" protocol table MUST NOT contain `Input` or `Output` columns whose
values are not present in the source record. Its parameter columns MUST still be emitted. The Assay annotation table's
`Output [URI]` column is governed by "Assay Output URI MUST come from a distribution URL".

#### Scenario: No fabricated entities

- **WHEN** a ckanext-dcat dataset with keywords and languages is mapped to an ARC
- **THEN** the RO-Crate `@graph` contains no `Published Dataset` File entity and no `Raw Data` Source

#### Scenario: Protocol parameters are kept

- **WHEN** the same record is mapped
- **THEN** the Dataset Processing protocol still carries the Processing Description, Keywords and Language parameters
  where the dataset has them

#### Scenario: Assay output unchanged

- **WHEN** a record with a distribution access or download URL is mapped
- **THEN** the Assay annotation table's `Output [URI]` column has the same value as before this change; records without
  such a URL follow "Assay Output URI MUST come from a distribution URL"

## ADDED Requirements

### Requirement: Assay Output URI MUST come from a distribution URL

The ckanext-dcat mapper MUST set the Assay `Measurement` table's `Output [URI]` to the first distribution
`dcat:accessURL` or `dcat:downloadURL` when there is one. When the dataset has no such URL, the table MUST NOT contain
an `Output [URI]` column and MUST NOT fall back to the `dcat:Dataset` IRI; it MUST still contain one row with
`Input [Source Name]` and the distribution comments the dataset has. The Investigation `Landing Page` comment is not
affected.

#### Scenario: Dataset without a distribution URL

- **GIVEN** a `dcat:Dataset` with IRI `https://ckan.example.org/dataset/abc` and no distribution access or download URL
- **WHEN** it is mapped
- **THEN** the Assay table has no `Output [URI]` column and the RO-Crate has no `URI` entity for
  `https://ckan.example.org/dataset/abc`

#### Scenario: Dataset with a distribution URL

- **GIVEN** a `dcat:Dataset` with a distribution whose `dcat:accessURL` is `https://data.example.org/file.csv`
- **WHEN** it is mapped
- **THEN** the Assay table's `Output [URI]` is `https://data.example.org/file.csv`

#### Scenario: Table and landing page kept without a URL

- **GIVEN** a `dcat:Dataset` with an http(s) IRI and one titled distribution without an access or download URL
- **WHEN** it is mapped
- **THEN** the Assay table has one row with `Input [Source Name]` and a `Distribution Title` comment, and the
  Investigation keeps its `Landing Page` comment
