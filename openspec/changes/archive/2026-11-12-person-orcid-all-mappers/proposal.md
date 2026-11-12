# Proposal

## Why

Middleware catalog materialize (API #551) will pass through Person `identifier` when RO-Crate Persons carry a resolvable
PID. That only works if every harvester mapper that emits ARC Persons fills ARCtrl `Person.ORCID` when the source has an
ORCID — not only Schema.org (#405) / Regal, and not as an opaque `ORCID` Comment. ISA-XLSX lacks an ORCID column; ARCtrl
still serialises `Person.ORCID` into RO-Crate.

## What Changes

- **INSPIRE:** When a contact `online_resource_url` (or name) is an ORCID URL/iD, set `Person.ORCID` via shared
  `orcid_id`; do **not** also emit a Person Comment for that ORCID value (B1). Non-ORCID online resources stay Comments.
- **MODS:** Normalize parsed `nameIdentifier[@type=orcid]` through `orcid_id` before `Person.create(orcid=…)` (bare iD;
  reject non-ORCID noise).
- **Schema.org / Regal:** Keep existing `Person.ORCID` contracts; no requirement change unless gaps appear while
  applying.
- **Docs:** Update `docs/mappers/inspire.md` and `docs/mappers/mods.md` so ORCID → `Person.ORCID` (not Comment-only).
- **Tests:** Unit coverage for INSPIRE ORCID onlineResource and MODS ORCID normalization (URL vs bare iD).

### Non-goals

- **PhenoRoam:** Source `pr:blockPerson` has no ORCID/identifier today → no parser/model/mapper change in this slice.
- **ckanext-dcat:** Mapper emits no Person creators today → no ORCID work until Person agents exist.
- Middleware API #551 export pass-through itself (coordinate only).
- Inventing ORCID from email/name or inventing PhenoRoam fields.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `inspire-to-arc-mapping`: Person contacts MUST set `Person.ORCID` when contact online resource is an ORCID; MUST NOT
  duplicate that value as an `ORCID` / online-resource Comment when the field is set.
- `mods-to-arc-mapping`: Creator ORCID identifiers MUST be normalized via `orcid_id` into `Person.ORCID` (bare iD).

## Impact

- Code: `middleware/payload/.../inspire/mapper.py`, `mods/mapper.py`; possibly shared `person_contacts` only if helpers
  need a thin wrapper; unit tests under `middleware/payload/tests/`.
- Docs: `docs/mappers/inspire.md`, `docs/mappers/mods.md`.
- Specs: deltas under `inspire-to-arc-mapping`, `mods-to-arc-mapping`.
- Issue: [#626](https://github.com/fairagro/m4.2_middleware_harvester/issues/626); lock-ins A2 B1 C2.
- Downstream: enables Search Hub / basic-layout person identifiers once API #551 lands.
