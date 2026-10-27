# Spec Delta

## ADDED Requirements

### Requirement: Data Processing protocol MUST NOT invent input or output entities

The Regal mapper's Study "Data Processing" protocol table MUST NOT contain `Input` or `Output` columns whose values are
not present in the source record. Its parameter columns MUST still be emitted. The Assay annotation table's
`Output [URI]` column is not affected by this requirement.

#### Scenario: No fabricated entities

- **WHEN** a Regal ResearchData record with funding and license metadata is mapped to an ARC
- **THEN** the RO-Crate `@graph` contains no `Raw Data` or `Published Dataset` File entities

#### Scenario: Protocol parameters are kept

- **WHEN** the same record is mapped
- **THEN** the Data Processing protocol still carries the Processing Description, Funder, Funding Program, Project ID
  and License parameters where the record has them

#### Scenario: Assay output unchanged

- **WHEN** any record is mapped
- **THEN** the Assay annotation table's `Output [URI]` column has the same value as before this change
