## ADDED Requirements

### Requirement: Accept nested mycore_rest protocol settings

The system SHALL accept nested `generic.protocol.mycore_rest` with at least `entry_url` (list endpoint including
operator filters) and optional `page_size` (or equivalent paging control) consistent with other paginated protocols.

#### Scenario: mycore_rest entry_url required

- **WHEN** `protocol.mycore_rest` is selected without `entry_url`
- **THEN** configuration validation fails

### Requirement: Accept mods_xml parser and mods_general mapper keys

The system SHALL accept repository sibling `parser.mods_xml` and `mapper.mods_general` (type-as-key) as valid
registrations alongside existing parser/mapper keys.

#### Scenario: OpenAgrar-style composition validates

- **WHEN** a repository configures `generic` + `protocol.mycore_rest` + `parser.mods_xml` + `mapper.mods_general`
- **THEN** configuration validation succeeds when kinds align (`mods_record`)
