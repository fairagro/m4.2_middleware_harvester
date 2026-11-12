# Tasks

## 1. INSPIRE Person.ORCID

- [x] 1.1 In `InspireMapper.map_person` / `_add_person_comments`, set `Person.ORCID` via `orcid_id` from
      `online_resource_url` (else ORCID-shaped `online_resource_name`) and skip the Person Comment for that ORCID value;
      keep Comments for non-ORCID online resources — verify with new unit tests in `test_inspire_mapper.py` covering
      ORCID URL, bare iD name, and non-ORCID website
- [x] 1.2 Update `docs/mappers/inspire.md` contact/onlineResource rows so ORCID → `Person.ORCID` (not Comment-only) —
      verify the doc wording matches the scenarios in the inspire delta spec

## 2. MODS Person.ORCID normalization

- [x] 2.1 In `mods/mapper.py` `_map_person`, pass ORCID through `orcid_id` before `Person.create` (omit invalid) —
      verify with unit tests for URL → bare iD and non-ORCID identifier unchanged as GND Comment
- [x] 2.2 Update `docs/mappers/mods.md` ORCID row to state bare `Person.ORCID` via `orcid_id` — verify doc matches the
      mods delta scenarios

## 3. Regression / quality

- [x] 3.1 Run focused payload unit tests (`test_inspire_mapper`, `test_mods_mapper`, existing schema.org/regal ORCID
      tests) and `uv run ruff format` / `ruff check` on touched files — verify green
- [x] 3.2 `openspec validate person-orcid-all-mappers --strict` — verify passes
