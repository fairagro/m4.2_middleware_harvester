## Why

ARC Persons need a given name (DataHUB `arc-export`, #120), so organisations that author a dataset become Investigation
Comments. Each mapper named them differently (INSPIRE: the ISO role, e.g. `Originator`, `Author`; Schema.org: `Author`,
repeated when e!DAL lists the organisation as both creator and author; Regal: `Creator` with `name (id)`), so the hub
cannot show them as the creator. Thünen Atlas has no individual contacts at all (151/151 records without a creator).
ARCtrl drops RO-Crate `Organization` creators when the API parses the crate, so a Comment is the only representation
that survives today. Tracked as GitHub [#411](https://github.com/fairagro/m4.2_middleware_harvester/issues/411).

## What Changes

- New shared helper `middleware.payload.person_contacts.add_creator_organization`: one Investigation Comment
  `Creator Organization` per organisation (case-insensitive), plus `Creator Organization URL` when a URL is known.
- INSPIRE: organisation-only contacts with role author, originator or principalInvestigator use it; other roles keep
  their role-named Comment (`owner` holds rights, it is not a creator).
- Schema.org: `Organization` creators / authors use it (was `Author`). Regal: organisation-label creators use it (was
  `Creator` with `name (id)`; the `@id` is now the URL Comment).
- Contributor and publisher organisations are unchanged.

## Capabilities

### Modified Capabilities

- `person-contact-given-name`: one Comment name for organisational creators.
- `inspire-to-arc-mapping`: ISO creator roles.

## Impact

- Thünen Atlas live (151 records): 96 records get a `Creator Organization` (it survives ARCtrl's RO-Crate round-trip);
  the other 55 give creators as an e-mail address only (`individualName` and `organisationName` nil). e!DAL
  10.5447/ipk/2016/12: one `Creator Organization: IBSC` instead of two `Author` Comments.
- The hub still has to show `Creator Organization` as the creator; asked on #411.
