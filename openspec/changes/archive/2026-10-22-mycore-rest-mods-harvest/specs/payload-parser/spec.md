## ADDED Requirements

### Requirement: Register mods_xml parser type

The system SHALL register a PayloadParser implementation under registry key `mods_xml` selectable via repository
`parser` type-as-key (`parser.mods_xml`) or deprecated `parser.type: mods_xml`, with `produces` kind `mods_record`.

#### Scenario: mods_xml produces mods_record

- **WHEN** the active parser type is `mods_xml`
- **THEN** the parser’s `produces` kind is `mods_record`

#### Scenario: generic can compose mods_xml with mods_general mapper

- **WHEN** a `generic` repository sets nested `parser.mods_xml` and nested `mapper.mods_general`
- **THEN** startup kind alignment succeeds
