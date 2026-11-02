## ADDED Requirements

### Requirement: Support PayloadKind mods_record

The system SHALL extend `PayloadKind` with `mods_record` for typed MODS intermediate records (value type owned by
`middleware.payload`) produced by the `mods_xml` parser and accepted by the `mods_general` DataMapper.

#### Scenario: mods_general accepts mods_record

- **WHEN** the active mapper type is `mods_general`
- **THEN** the mapper's `accepts` kind is `mods_record`

### Requirement: Register mods_general mapper type

The system SHALL register a DataMapper under registry key `mods_general`, selectable via repository
`mapper.mods_general`, with no mapper-specific settings.

#### Scenario: Empty type child validates

- **WHEN** a repository sets `mapper: { mods_general: {} }`
- **THEN** configuration validation succeeds

#### Scenario: Unknown field fails closed

- **WHEN** a repository sets an unknown field under `mapper.mods_general`
- **THEN** configuration validation fails before harvest
