## 1. Shared validation

- [x] 1.1 Add a small linked_data helper that rejects Investigation contacts whose FirstName is missing/null/whitespace-only (no placeholder substitution)
- [x] 1.2 Call the helper at the end of contact assembly in both Schema.org and Regal mappers so `map_graph` fails before returning `HarvestedArc`

## 2. GeneralSchemaOrgMapper

- [x] 2.1 Stop mapping Organization publishers (and Organization-typed creator/contributor nodes) to Person contacts with empty given name
- [x] 2.2 Emit Investigation `Comment("Publisher", …)` (optional separate URL comment) for Organization publishers; keep creator affiliations on `Person.Affiliation`

## 3. RegalMapper

- [x] 3.1 Ensure creator/contributor mapping never appends Person with empty FirstName from org-/label-only `prefLabel` splits; use Comment/Affiliation for org agents or fail closed
- [x] 3.2 Align contact wording in `docs/regal_mapping.md` with the given-name / org rules (override LastName-only contact reading)

## 4. Tests

- [x] 4.1 Fixture/test: OpenAgrar-like Schema.org graph (Person creators with givenName + Organization publisher Zenodo) → ARC without empty-given Person; Publisher as Comment; Write/load/`ToROCrateJsonString` (or equivalent) does not fail with `Person must have a given name`
- [x] 4.2 Test: record with author lacking given name → mapping fails; no HarvestedArc / no upload path
- [x] 4.3 Regal unit coverage for org-/label-only agent that must not become empty-given Person (comment/affiliation or fail)

## 5. Validation

- [x] 5.1 Run `uv run ruff format middleware/` and `uv run pytest middleware/linked_data/tests/unit/test_mapper.py middleware/linked_data/tests/unit/test_regal_mapper.py -v`
