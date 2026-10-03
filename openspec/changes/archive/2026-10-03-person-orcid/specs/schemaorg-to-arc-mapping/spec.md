## ADDED Requirements

### Requirement: Person contacts MUST keep their ORCID

`GeneralSchemaOrgMapper` MUST set `Person.ORCID` (bare iD, via `middleware.payload.person_contacts.orcid_id`) from the
Person `@id` when it is an orcid.org URL, else from `schema:identifier`: an ORCID string or URL, or a `PropertyValue`
whose `value` is an orcid.org URL or whose `propertyID` names ORCID. Contacts MUST be added via `add_contact`, so a
repeated ORCID adds its role to the existing contact. When a `creator` without ORCID and an `author` with ORCID match by
name, the merged contact MUST keep the ORCID.

#### Scenario: e!DAL author with ORCID

- **WHEN** an `author` has `@id` `https://orcid.org/0000-0003-4387-4923` and an `identifier` PropertyValue (`propertyID`
  `orcid`)
- **THEN** the contact's `Person.ORCID` MUST be `0000-0003-4387-4923` and its RO-Crate `@id`
  `http://orcid.org/0000-0003-4387-4923`

#### Scenario: Non-ORCID identifiers

- **WHEN** a Person has a non-orcid.org `@id` or a bare iD-shaped value under another `propertyID`
- **THEN** `Person.ORCID` MUST stay empty

#### Scenario: Creator and author merge keeps ORCID

- **WHEN** the same person is a `creator` without ORCID and an `author` with ORCID
- **THEN** there MUST be one contact, and it MUST carry the ORCID
