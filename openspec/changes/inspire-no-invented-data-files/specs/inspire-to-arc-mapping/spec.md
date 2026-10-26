# Spec Delta

## ADDED Requirements

### Requirement: Study protocols MUST NOT invent Data entities

The INSPIRE Study protocol tables (Data Acquisition, Data Processing) MUST NOT contain `Input [Data]` or `Output [Data]`
columns whose values are not present in the `InspireRecord`. Their parameter columns MUST still be emitted. A Data
Processing table MUST NOT be emitted when it would carry no value from the record. The Assay annotation table's
`Output [URI]` column is not affected by this requirement.

#### Scenario: No fabricated File entities

- **WHEN** a BonaRes-style record with temporal extent, creation dates and lineage is mapped to an ARC
- **THEN** the RO-Crate `@graph` contains no `studies/*/resources/Raw Data` or `studies/*/resources/Processed Data`
  File entities

#### Scenario: Protocol parameters are kept

- **WHEN** the same record is mapped
- **THEN** the Data Acquisition and Data Processing protocols still carry Temporal Extent, Acquisition Date, Processing
  Description, Conformance, Output Format and Processing Date parameters where the record has them

#### Scenario: No processing protocol without processing metadata

- **WHEN** a record's only processing-related value is a creation date
- **THEN** no Data Processing protocol is emitted

#### Scenario: Assay output unchanged

- **WHEN** any record is mapped
- **THEN** the Assay annotation table's `Output [URI]` column has the same value as before this change
