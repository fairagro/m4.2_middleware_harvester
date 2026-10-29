# Spec Delta

## MODIFIED Requirements

### Requirement: Create one ArcAssay per record for Measurement output

The system SHALL create one `ArcAssay` per record for the Measurement annotation table (dataset URI / online resources).
The Assay MUST have no annotation table when that table would have no columns (see "Assay table MUST NOT invent an
input source"). The Data Processing protocol table MUST live on the Study, not on the Assay.

#### Scenario: Assay is Measurement-only; Data Processing is on the Study

- **WHEN** an InspireRecord with a `dataSetURI` is mapped
- **THEN** the Study contains the Data Processing protocol table and the Assay contains the Measurement annotation table
  (not a Data Processing protocol)

### Requirement: Assay output URI MUST NOT be invented

The INSPIRE Assay annotation table MUST have an `Output [URI]` column only when the `InspireRecord` has a `dataSetURI`
or at least one online resource. The value is the `dataSetURI` when present, otherwise the first online resource URL. A
record with neither MUST produce an Assay table without an `Output [URI]` column and MUST NOT produce any placeholder
URI. The table keeps its single row with the Graphic Overview comment where present.

#### Scenario: No URI available

- **WHEN** a record with no `dataSetURI` and no online resources is mapped
- **THEN** the Assay table has no `Output [URI]` column and the RO-Crate `@graph` has no `@type: URI` entity whose `@id`
  ends in `_dataset`

#### Scenario: dataSetURI present

- **WHEN** a record with a `dataSetURI` is mapped
- **THEN** `Output [URI]` is the `dataSetURI`

#### Scenario: Only online resources

- **WHEN** a record with online resources and no `dataSetURI` is mapped
- **THEN** `Output [URI]` is the first online resource URL and the Online Resource comments skip it

#### Scenario: Row kept without URI

- **WHEN** a record with no URI but a graphic overview is mapped
- **THEN** the Assay table has one row with the Graphic Overview comment and no `Input [Source Name]` column

## ADDED Requirements

### Requirement: Assay table MUST NOT invent an input source

The INSPIRE Assay `Measurement` table MUST NOT contain an `Input [Source Name]` column, because no INSPIRE field names
the material the measurement started from. When the table has no `Output [URI]` and no comment columns, the Assay MUST
NOT have an annotation table. `Output [URI]` and the comment columns are not affected.

#### Scenario: Record with a dataset URI

- **GIVEN** an InspireRecord with a `dataSetURI`
- **WHEN** it is mapped
- **THEN** the Assay table has no `Input [Source Name]` column, the RO-Crate `@graph` has no `#Source_Dataset_Source`
  entity, and `Output [URI]` is the `dataSetURI`

#### Scenario: Record without Assay data

- **GIVEN** an InspireRecord with no `dataSetURI`, no online resources and no graphic overview
- **WHEN** it is mapped
- **THEN** the Assay has no annotation table
