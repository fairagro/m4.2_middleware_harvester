# Spec Delta

## ADDED Requirements

### Requirement: Assay output URI MUST NOT be invented

The INSPIRE Assay annotation table MUST have an `Output [URI]` column only when the `InspireRecord` has a `dataSetURI`
or at least one online resource. The value is the `dataSetURI` when present, otherwise the first online resource URL. A
record with neither MUST produce an Assay table without an `Output [URI]` column and MUST NOT produce any placeholder
URI. The table keeps its single row with `Input [Source Name]` and the Graphic Overview comment where present.

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
- **THEN** the Assay table has one row with `Input [Source Name]` and the Graphic Overview comment

## MODIFIED Requirements

### Requirement: Study protocols MUST NOT invent Data entities

The INSPIRE Study protocol tables (Data Acquisition, Data Processing) MUST NOT contain `Input [Data]` or `Output [Data]`
columns whose values are not present in the `InspireRecord`. The Data Acquisition table MUST have its `Input [Sample]`
"Selected Location" column only when the Spatial Sampling protocol is emitted for the record, because that protocol
produces the sample. Their parameter columns MUST still be emitted. A Data Processing table MUST NOT be emitted when it
would carry no value from the record. The Assay annotation table's `Output [URI]` column is governed by the requirement
"Assay output URI MUST NOT be invented".

#### Scenario: No fabricated File entities

- **WHEN** a BonaRes-style record with temporal extent, creation dates and lineage is mapped to an ARC
- **THEN** the RO-Crate `@graph` contains no `studies/*/resources/Raw Data` or `studies/*/resources/Processed Data` File
  entities

#### Scenario: Protocol parameters are kept

- **WHEN** the same record is mapped
- **THEN** the Data Acquisition and Data Processing protocols still carry Temporal Extent, Acquisition Date, Processing
  Description, Conformance, Output Format and Processing Date parameters where the record has them

#### Scenario: No dangling Selected Location for non-geographic records

- **WHEN** a `nonGeographicDataset` record with a temporal extent is mapped
- **THEN** the Data Acquisition table has no Input column and the RO-Crate `@graph` has no "Selected Location" Sample

#### Scenario: No dangling Selected Location without spatial info

- **WHEN** a geographic record without bounding box, CRS or resolution is mapped
- **THEN** no Spatial Sampling protocol is emitted and the Data Acquisition table has no Input column

#### Scenario: Selected Location kept when Spatial Sampling exists

- **WHEN** a geographic record with a bounding box is mapped
- **THEN** Spatial Sampling outputs "Selected Location" and the Data Acquisition table takes it as Input

#### Scenario: No processing protocol without processing metadata

- **WHEN** a record's only processing-related value is a creation date
- **THEN** no Data Processing protocol is emitted

#### Scenario: Assay output unchanged

- **WHEN** a record with a `dataSetURI` or online resources is mapped
- **THEN** the Assay annotation table's `Output [URI]` column has the same value as before this change
