## MODIFIED Requirements

### Requirement: Dataset Processing protocol MUST NOT invent input or output entities

The ckanext-dcat mapper's Study "Dataset Processing" protocol table MUST NOT contain `Input` or `Output` columns whose
values are not present in the source record. Its remaining parameter columns MUST still be emitted where applicable. The
Assay annotation table's `Output [URI]` column is governed by "Assay Output URI MUST come from a distribution URL". The
protocol MUST NOT carry a Keywords parameter; keywords belong on Investigation Comments per `keyword-comments`.

#### Scenario: No fabricated entities

- **WHEN** a ckanext-dcat dataset with keywords and languages is mapped to an ARC
- **THEN** the RO-Crate `@graph` contains no `Published Dataset` File entity and no `Raw Data` Source

#### Scenario: Protocol parameters are kept

- **WHEN** the same record is mapped
- **THEN** the Dataset Processing protocol still carries the Processing Description and Language parameters where the
  dataset has them, and MUST NOT carry a Keywords parameter

#### Scenario: Assay output unchanged

- **WHEN** a record with a distribution access or download URL is mapped
- **THEN** the Assay annotation table's `Output [URI]` column has the same value as before this change; records without
  such a URL follow "Assay Output URI MUST come from a distribution URL"

## ADDED Requirements

### Requirement: ckanext-dcat mapper MUST follow keyword-comments contract

`CkanextDcatMapper` MUST emit Investigation keyword Comments for `dcat:keyword` values according to `keyword-comments`
(aggregate separator `", "`). `docs/mappers/ckanext-dcat.md` MUST match.

#### Scenario: DCAT keywords become Investigation Comments

- **WHEN** a dataset has `dcat:keyword` values `Soil` and `Water`
- **THEN** the Investigation MUST include aggregate `Keywords` and per-term `keyword [Soil]` / `keyword [Water]`
