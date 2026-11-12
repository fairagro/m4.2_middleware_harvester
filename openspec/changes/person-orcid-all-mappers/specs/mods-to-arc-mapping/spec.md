# Spec Delta

## ADDED Requirements

### Requirement: Creator ORCID identifiers MUST become Person.ORCID via orcid_id

When a MODS `name` carries a `nameIdentifier` of type ORCID (parsed onto the intermediate contact), `mods_general` MUST
set ARCtrl `Person.ORCID` to the bare iD returned by `middleware.payload.person_contacts.orcid_id` for that value (URL
or bare iD). Values that do not normalize MUST NOT be written to `Person.ORCID`. GND and other non-ORCID identifiers
MUST remain Person Comments per `docs/mappers/mods.md`. The mapping doc MUST state that ORCID goes to `Person.ORCID`,
not an `ORCID` Comment.

#### Scenario: ORCID URL normalizes to bare iD

- **WHEN** a MODS creator has `nameIdentifier` type `orcid` with value `https://orcid.org/0000-0002-1825-0097`
- **THEN** the contact's `Person.ORCID` MUST be `0000-0002-1825-0097`

#### Scenario: Non-ORCID nameIdentifier is not Person.ORCID

- **WHEN** a MODS creator has only a non-ORCID `nameIdentifier` (e.g. GND)
- **THEN** `Person.ORCID` MUST stay empty and the GND MUST remain a Person Comment when mapped
