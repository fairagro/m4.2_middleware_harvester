## Why

OpenAgrar (and similar Schema.org/Regal sources) map Organization publishers such as Zenodo to ISA `Person` contacts with an empty given name. That RO-Crate uploads fine, but DataHUB `arc-export` fails after ISA Write/load with `Person must have a given name`. Authors are correct; the bogus org-as-person contact breaks the CI path.

## What Changes

- Require every mapped Person contact to have a non-empty given name (trim; missing/null/`""` invalid).
- Stop mapping Organizations as Person contacts with empty/missing given names.
- Represent organizations via Investigation `Comment("Publisher", …)` (optional separate URL comment) and/or `Person.Affiliation` when the source affiliation belongs to a person.
- Forbid placeholder given names (`.`, `n/a`, org name as givenName).
- Fail closed: if any Person contact would lack a non-empty given name after mapping, count the record as failed in the harvest report and do not upload the ARC.
- Update `GeneralSchemaOrgMapper` and `RegalMapper` accordingly; add fixtures/tests covering the OpenAgrar-like shape and the author-without-given-name failure path.

## Capabilities

### New Capabilities

- `person-contact-given-name`: Normative rules for Person given-name validity, Organization representation (Comment / Affiliation), and fail-closed mapping when given name is missing.

### Modified Capabilities

- `linked-data-mapper`: Schema.org mapper MUST NOT emit Organization publishers as empty-given-name Persons; MUST emit Publisher comments and preserve creator affiliations.
- `regal-to-arc-mapping`: Regal contact mapping MUST apply the same given-name / Organization rules (no Person with empty first_name from org/label splits).

## Impact

- Code: `middleware/linked_data/.../general_schema_org_mapper.py`, `regal_mapper.py`, possibly a small shared validation helper in linked_data; unit tests under `middleware/linked_data/tests/`.
- Specs: new `person-contact-given-name`; deltas for `linked-data-mapper` and `regal-to-arc-mapping`; optionally touch `docs/regal_mapping.md` for contact/org wording.
- Non-goals: Middleware API ingest changes; new Organization contact type in arctrl/ISA; work in `m4.2_advanced_middleware_api` (shared helper later if needed).
- Domains affected: `linked-data-mapper`, `regal-to-arc-mapping`, new `person-contact-given-name` (related: harvest-report counting via existing fail path / `RecordProcessingError`).
