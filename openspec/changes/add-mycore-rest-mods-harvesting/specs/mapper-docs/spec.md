## ADDED Requirements

### Requirement: MODS base mapper document

The system SHALL keep a base mapping document `docs/mappers/mods.md` for the `mods_general` DataMapper, with front
matter `payload_kind: mods_record` and the required base sections, listed in `docs/mappers/README.md`. It MUST describe
MODS elements (not MyCoRe internals or parser APIs) and ARC targets.

#### Scenario: MODS document is indexed

- **WHEN** a contributor opens `docs/mappers/README.md`
- **THEN** `mods.md` is listed as the base document for `mods_record`
