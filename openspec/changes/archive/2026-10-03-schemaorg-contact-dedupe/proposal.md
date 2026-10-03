## Why

`GeneralSchemaOrgMapper` added `contributor` Persons without checking existing contacts. e!DAL's `author` array is the
creators plus the contributors, so every e!DAL contributor became two contacts (author and contributor). In the DataHUB
export 205/338 e!DAL records had duplicate persons. Tracked as GitHub
[#406](https://github.com/fairagro/m4.2_middleware_harvester/issues/406).

## What Changes

- One contact per person across `creator`, `author` and `contributor`: same ORCID, else same given and family name
  (case-insensitive), unless both carry different ORCIDs. A repeated person adds its role to the existing contact, and a
  contact without ORCID takes the repeated entry's ORCID.
- `add_contact` in `middleware.payload.person_contacts` gets `match_name`; the Schema.org mapper uses it, the Regal
  mapper keeps ORCID-only matching.

## Capabilities

### Modified Capabilities

- `schemaorg-to-arc-mapping`: one contact per person.

## Impact

- e!DAL ARCs with contributors change once after deploy (fewer contacts; contributors carry author and contributor).
