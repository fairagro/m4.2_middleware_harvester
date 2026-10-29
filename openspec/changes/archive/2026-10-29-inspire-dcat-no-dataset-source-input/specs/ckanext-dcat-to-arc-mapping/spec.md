# Spec Delta

## MODIFIED Requirements

### Requirement: Map dcat:Dataset to ARC Investigation, Study and Assay

The mapper SHALL build an ARC Investigation from the `dcat:Dataset` (title, description, identifier slug derived from
the dataset IRI) with Investigation comments for source identifier, modified date, keywords, language, publisher,
contact point, spatial extent and — when configured — the data catalog (`catalog_name` / `catalog_url`). It SHALL add
one Study (`<id>_study`) with a dataset-processing table and one Assay (`<id>_assay`) with a distribution table; the
Assay has no table when the distribution table would have no columns (see "Assay table MUST NOT invent an input
source").

#### Scenario: Dataset with distribution

- **WHEN** a dataset graph has a title and one `dcat:Distribution`
- **THEN** the ARC root carries the title and a stable identifier derived from the dataset IRI

### Requirement: Assay Output URI MUST come from a distribution URL

The ckanext-dcat mapper MUST set the Assay `Measurement` table's `Output [URI]` to the first distribution
`dcat:accessURL` or `dcat:downloadURL` when there is one. When the dataset has no such URL, the table MUST NOT contain
an `Output [URI]` column and MUST NOT fall back to the `dcat:Dataset` IRI; it MUST still contain one row with the
distribution comments the dataset has. The Investigation `Landing Page` comment is not affected.

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
- **THEN** the Assay table has one row with a `Distribution Title` comment and no `Input [Source Name]` column, and the
  Investigation keeps its `Landing Page` comment

## ADDED Requirements

### Requirement: Assay table MUST NOT invent an input source

The ckanext-dcat Assay `Measurement` table MUST NOT contain an `Input [Source Name]` column, because no DCAT-AP property
names the material the distribution was produced from. When the table has no `Output [URI]` and no comment columns, the
Assay MUST NOT have an annotation table. `Output [URI]` and the distribution comments are not affected.

#### Scenario: Dataset with a distribution URL

- **GIVEN** a `dcat:Dataset` with a distribution whose `dcat:accessURL` is `https://data.example.org/file.csv`
- **WHEN** it is mapped
- **THEN** the Assay table has no `Input [Source Name]` column, the RO-Crate `@graph` has no `#Source_Dataset_Source`
  entity, and `Output [URI]` is `https://data.example.org/file.csv`

#### Scenario: Dataset without distributions

- **GIVEN** a `dcat:Dataset` with an http(s) IRI and no `dcat:distribution`
- **WHEN** it is mapped
- **THEN** the Assay has no annotation table and the Investigation keeps its `Landing Page` comment
