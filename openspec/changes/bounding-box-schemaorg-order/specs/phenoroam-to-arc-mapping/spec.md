# Spec Delta

## ADDED Requirements

### Requirement: PhenoRoam bbox MUST become Study Bounding Box in schema.org order

When `PhenoroamRecord.bbox` has west, south, east, and north that each parse as floats, `phenoroam_general` MUST add a
Study Spatial Sampling protocol table with parameter `Bounding Box` whose value is the schema.org `GeoShape.box` string
`south west north east` (same grammar as INSPIRE). The mapper MUST NOT emit the Assay annotation comment
`Geographic Bounding Box` for that bbox. When any required side is missing or unparseable, the mapper MUST omit Study
`Bounding Box` (and MUST NOT emit the Assay geographic bbox comment either). `docs/mappers/phenoroam.md` MUST document
this contract.

#### Scenario: Full bbox becomes Study Bounding Box

- **WHEN** a record has bbox west `6.9895`, east `6.9922`, south `50.6152`, north `50.6165`
- **THEN** the Study Spatial Sampling `Bounding Box` ParameterValue MUST be `50.6152 6.9895 50.6165 6.9922`
- **AND** the Assay table MUST NOT include a `Geographic Bounding Box` comment

#### Scenario: Incomplete bbox omits Bounding Box

- **WHEN** a record has only west and east on `bbox`
- **THEN** the mapped ARC MUST NOT include a Study `Bounding Box` parameter or an Assay `Geographic Bounding Box`
  comment
