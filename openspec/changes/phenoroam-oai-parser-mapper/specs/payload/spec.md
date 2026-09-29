## ADDED Requirements

### Requirement: Support PayloadKind phenoroam_record

The system SHALL extend `PayloadKind` with `phenoroam_record` for typed PhenoRoam intermediate records produced by the
`phenoroam_xml` parser and accepted by the `phenoroam_general` DataMapper.

#### Scenario: phenoroam_general mapper accepts phenoroam_record

- **WHEN** `mapper.type` is `phenoroam_general`
- **THEN** the mapper’s `accepts` kind is `phenoroam_record`

### Requirement: Register phenoroam_general mapper type

The system SHALL register a DataMapper implementation under registry key `phenoroam_general` selectable via repository
`mapper.type`.

#### Scenario: Unknown mapper type still fails closed

- **WHEN** `mapper.type` is not registered
- **THEN** configuration validation fails before harvest
