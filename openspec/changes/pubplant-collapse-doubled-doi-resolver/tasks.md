# Tasks

## 1. Tests and fix

- [x] 1.1 T1: a one-record array with `@id` `https://doi.org/doi.org/10.1093/dnares/dsx047` and `identifier`
      `doi.org/10.1093/dnares/dsx047` yields an ARC with the publication DOI `10.1093/dnares/dsx047` (repro; on `main`
      `Publications == []`)
- [x] 1.2 T2: the ARC contains no `doi.org/doi.org`; the link is `https://doi.org/10.1093/dnares/dsx047`
- [x] 1.3 T3: the doubled element and its fixed twin get the same discovery identifier and payload
- [x] 1.4 T4: a well-formed element keeps its identifier and payload (covered by the existing #661 test; no new test)
- [x] 1.5 T5: other stacks (`doi.org/…` without scheme, `https://dx.doi.org/https://doi.org/…`) are repaired; a
      free-text `identifier` is untouched
- [x] 1.6 T6: one WARNING per repaired element, naming the original values

## 2. Verify and close

- [x] 2.1 T7: end-to-end against a local API, live PlabiPD harvest: the record's ARC carries `10.1093/dnares/dsx047`,
      exactly one WARNING, harvested count unchanged
- [x] 2.2 `uv run ruff format middleware/` and `uv run pytest middleware/generic`
- [ ] 2.3 Archive after merge
