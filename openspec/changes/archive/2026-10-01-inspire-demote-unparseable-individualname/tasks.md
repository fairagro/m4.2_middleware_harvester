## 1. INSPIRE mapper

- [x] 1.1 In `InspireMapper._add_contacts`, demote an `individualName` whose split yields no given name to a role-named
      Investigation Comment (`<organisationName> (<individualName>)` or the raw `individualName`), deduplicated with
      organisation-only Comments; do not call `map_person` for it
- [x] 1.2 Keep the `map_person` `ValueError` as an invariant guard for direct callers; update docstrings

## 2. Tests

- [x] 2.1 Unit tests: `RTH` + organisation → Comment `Deutscher Wetterdienst (RTH)`, no Contacts; `RTH` alone → Comment
      `RTH`; repeated DWD entries deduplicated; mixed parseable Person + `RTH`; `map_investigation` on a DWD-like record
      succeeds

## 3. Docs

- [x] 3.1 Update `docs/inspire_mapping.md` individualName row and Person (Contacts) section

## 4. Validation

- [x] 4.1 `uv run ruff format middleware/` and `uv run pytest middleware/inspire`
- [x] 4.2 `openspec validate inspire-demote-unparseable-individualname`
