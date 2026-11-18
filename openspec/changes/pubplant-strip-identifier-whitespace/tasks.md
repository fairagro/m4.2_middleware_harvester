# Tasks

## 1. Tests and fix

- [x] 1.1 T1: a one-record array with `https://doi.org/10.1038/ s41597-026-06582-z` in `@id`/`identifier` is harvested
      (repro; fails on `main` with `JSON-LD produced an empty graph`)
- [x] 1.2 T2: the mapped ARC carries the DOI without whitespace (golden: tiny array → expected ARC)
- [ ] 1.3 T3: the spaced element and its fixed twin get the same discovery identifier
- [ ] 1.4 T4: an element without whitespace gets the same identifier and payload as before
- [ ] 1.5 T5: one WARNING per repaired element, naming the original value

## 2. Verify and close

- [ ] 2.1 T6: dev stack, live PlabiPD harvest: the 3 records are harvested and the failed count drops by 3
- [ ] 2.2 `uv run ruff format middleware/` and `uv run pytest middleware/generic`
- [ ] 2.3 Archive after merge
