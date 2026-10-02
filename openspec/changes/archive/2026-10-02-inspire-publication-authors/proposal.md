## Why

INSPIRE Publications never carried authors. `_add_role` maps the CSW role `author` to the NCIT label `Author`, but
`_add_publications` filtered on `role.Name == "author"`, so no contact matched. Fixing only the match would expose a
second bug: the `Last, F.` author string is split on `,` by the RO-Crate writer into fragment `#Author_ J.; Roe` Person
nodes (seen for Regal in #403 / #418).

Tracked as GitHub [#420](https://github.com/fairagro/m4.2_middleware_harvester/issues/420).

## What Changes

- New shared helper `person_contacts.publication_authors(investigation)`: author-role contacts (case-insensitive),
  contact order, `F. Last` joined by `; `.
- `InspireMapper`, `RegalMapper` and `GeneralSchemaOrgMapper` use it instead of three copies of the formatting logic.
  Regal and Schema.org output is unchanged (they already used `F. Last`; Regal gains the first-name-only fallback
  Schema.org had).

## Capabilities

### Modified Capabilities

- `inspire-to-arc-mapping`: Publication authors from author-role contacts, `F. Last` form.

## Impact

- INSPIRE ARCs with a DOI/ISBN resource identifier and author contacts gain a Publication author string, so their
  content changes once after deploy.
