## ADDED Requirements

### Requirement: Support PayloadKind phenoroam_record

The system SHALL extend `PayloadKind` with `phenoroam_record` for typed PhenoRoam intermediate records produced by the
`phenoroam_xml` parser and accepted by the `phenoroam` DataMapper.

#### Scenario: phenoroam mapper accepts phenoroam_record

- **WHEN** `mapper.type` is `phenoroam`
- **THEN** the mapper’s `accepts` kind is `phenoroam_record`

### Requirement: Register phenoroam mapper type

The system SHALL register a DataMapper implementation under registry key `phenoroam` selectable via repository
`mapper.type`.

#### Scenario: Unknown mapper type still fails closed

- **WHEN** `mapper.type` is not registered
- **THEN** configuration validation fails before harvest
