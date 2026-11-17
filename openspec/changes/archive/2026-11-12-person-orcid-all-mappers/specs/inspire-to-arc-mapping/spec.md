# Spec Delta

## ADDED Requirements

### Requirement: Person ORCIDs from contact online resources MUST be Person.ORCID

When mapping an ISO `CI_ResponsibleParty` to an ARC Person, `InspireMapper` MUST set `Person.ORCID` to the bare ORCID iD
when `online_resource_url` (else `online_resource_name`, when that alone is ORCID-shaped) normalizes via
`middleware.payload.person_contacts.orcid_id`. When `Person.ORCID` is set from that resource, the mapper MUST NOT also
append a Person Comment whose value is that ORCID URL/iD (including Comments named `ORCID` or the online-resource name).
Non-ORCID online resources MUST keep the existing Person Comment behaviour (`online_resource_name` or `Online Resource`
→ URL). Field tables in `docs/mappers/inspire.md` MUST describe ORCID → `Person.ORCID` (not Comment-only).

#### Scenario: ORCID onlineResource becomes Person.ORCID

- **WHEN** a person contact has `online_resource_url` `https://orcid.org/0000-0002-1825-0097`
- **THEN** `Person.ORCID` MUST be `0000-0002-1825-0097` and the Person MUST NOT have a Comment whose value is that ORCID
  URL or bare iD

#### Scenario: Non-ORCID website stays a Comment

- **WHEN** a person contact has `online_resource_url` `https://example.org/people/jane`
- **THEN** `Person.ORCID` MUST stay empty and the Person MUST keep an online-resource Comment with that URL

#### Scenario: Bare ORCID iD in online resource name

- **WHEN** a person contact has no usable `online_resource_url` but `online_resource_name` is `0000-0002-1825-0097`
- **THEN** `Person.ORCID` MUST be `0000-0002-1825-0097` and that iD MUST NOT be duplicated as a Person Comment
