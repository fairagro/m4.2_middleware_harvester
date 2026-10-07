## Why

`GeneralSchemaOrgMapper` dropped person ORCIDs: e!DAL landing pages give them as the Person `@id` and as an `identifier`
PropertyValue, but the mapper read only names, email, url, affiliation and address. The Regal mapper kept ORCIDs, but
only as a Person `ORCID` Comment, which the RO-Crate writer flattens into a `disambiguatingDescription` string. Tracked
as GitHub [#405](https://github.com/fairagro/m4.2_middleware_harvester/issues/405).

## What Changes

- Both mappers set ARCtrl's `Person.ORCID` (bare iD). ARCtrl writes it as the RO-Crate Person `@id`
  (`http://orcid.org/<iD>`) and reads it back from there. The Regal `ORCID` Comment is replaced.
- Schema.org: ORCID from the Person `@id`, else from `identifier` (ORCID string or URL; PropertyValue whose value is an
  orcid.org URL, or whose `propertyID` names ORCID).
- Shared helpers in `middleware.payload.person_contacts`: `orcid_id` (normalise an iD / orcid.org URL) and `add_contact`
  (one contact per ORCID; a repeated ORCID adds its role to the existing contact, since ARCtrl would otherwise merge the
  two Person nodes and give both contacts both roles on read-back).
- Schema.org `creator` without ORCID plus `author` with ORCID (same name) keeps the ORCID on the merged contact.

## Capabilities

### Modified Capabilities

- `schemaorg-to-arc-mapping`: person ORCID.
- `regal-to-arc-mapping`: ORCID as `Person.ORCID` instead of a Comment.

## Impact

- e!DAL and Publisso ARCs with ORCID persons change once after deploy (Person `@id` becomes the ORCID URL).
- Publisso `/find` (92 records): 319 ORCID Person `@id`s for 321 source ORCID entries; the other 2 are creator and
  contributor at once and now are one contact with both roles.
- Export of the identifier into the basic-layout dump is API-side: fairagro/m4.2_advanced_middleware_api#551.
