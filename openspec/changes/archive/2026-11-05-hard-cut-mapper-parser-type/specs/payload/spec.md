## MODIFIED Requirements

### Requirement: Register phenoroam_general mapper type

The system SHALL register a DataMapper implementation under registry key `phenoroam_general` selectable via repository
`mapper` type-as-key (`mapper.phenoroam_general`).

#### Scenario: Unknown mapper type still fails closed

- **WHEN** the active mapper type is not registered
- **THEN** configuration validation fails before harvest

### Requirement: Provide mods_general DataMapper registration

The system SHALL register mapper type `mods_general` in the shared DataMapper registry with `accepts` kind
`mods_record`, implementing behaviour defined under `mods-to-arc-mapping` / `docs/mappers/mods.md`.

#### Scenario: Registry resolves mods_general

- **WHEN** repository config selects nested `mapper.mods_general`
- **THEN** registry resolution returns the MODS DataMapper implementation
