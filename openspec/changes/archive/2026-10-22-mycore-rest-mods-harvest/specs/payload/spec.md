## ADDED Requirements

### Requirement: Provide mods_record PayloadKind

The system SHALL include `mods_record` in `PayloadKind` for structured MODS-derived domain records (value type owned by
`middleware.payload` or an agreed shared model consumed by `mods_general`).

#### Scenario: mods_record is available

- **WHEN** a producer or mapper declares its kind
- **THEN** `mods_record` is a valid `PayloadKind` value

### Requirement: Provide mods_general DataMapper registration

The system SHALL register mapper type `mods_general` in the shared DataMapper registry with `accepts` kind
`mods_record`, implementing behaviour defined under `mods-to-arc-mapping` / `docs/mappers/mods.md`.

#### Scenario: Registry resolves mods_general

- **WHEN** repository config selects nested `mapper.mods_general` (or deprecated `mapper.type: mods_general`)
- **THEN** registry resolution returns the MODS DataMapper implementation
