## Why

Some ISO `CI_ResponsibleParty` entries put an org unit or acronym in `individualName` instead of a person name. DWD CDC
records (`urn:x-wmo:md:de.dwd.cdc::…`) use `individualName='RTH'`. `split_display_name` yields no given name for such
single-token labels, and the INSPIRE mapper currently fails the whole record closed, so these datasets never upload
(harvest report: `INSPIRE individualName must yield a non-empty given name (individualName='RTH', last_name='RTH')`).

Schema.org and Regal already demote organization-like labels to Investigation Comments, and INSPIRE already does so for
organisationName-only contacts. This change closes the remaining gap (issue #354).

## What Changes

- When `individualName` is present but its split yields no non-empty given name, the INSPIRE mapper emits a role-named
  Investigation Comment instead of failing the record. The value is `<organisationName> (<individualName>)` when an
  organisation is present, else the raw `individualName`. The Comment is deduplicated together with organisation-only
  Comments.
- No Person with an empty given name is ever emitted; the generic fail-closed guard stays as defense-in-depth.
- `docs/inspire_mapping.md` is updated to match.

## Capabilities

### Modified Capabilities

- `person-contact-given-name`: INSPIRE ISO field rule 1 and the shared-splitting requirement change from fail-closed to
  Comment demotion for unparseable `individualName`.

## Non-goals

- No change to the Schema.org or Regal mappers or to `split_display_name`.
- No new Organization contact type.
- Email/phone/address of a demoted contact are not preserved (same as the organisation-only path today).

## Impact

- `middleware/inspire/src/middleware/inspire/mapper.py` (`_add_contacts`, `map_person` docstring)
- `middleware/inspire/tests/unit/test_mapper_comprehensive.py`
- `docs/inspire_mapping.md`
