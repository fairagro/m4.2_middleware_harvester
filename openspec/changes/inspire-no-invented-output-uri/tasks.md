# Tasks

## 1. Tests and fix

- [ ] 1.1 T1: a minimal record without URIs has no `@type: URI` entity ending in `_dataset` in the RO-Crate
- [ ] 1.2 T2: the `{}` case of `test_assay_output_uri_is_unchanged` expects no `Output [URI]` column
- [ ] 1.3 T3: `dataSetURI` and online-resource cases are unchanged
- [ ] 1.4 T4: a no-URI record with a graphic overview keeps a one-row table with Input and the comment
- [ ] 1.5 Update `docs/mappers/inspire.md` (Output [URI] lines) and the `_create_assay_table` docstring
- [ ] 1.6 Count BonaRes/GDI-DE records hitting the fallback in a container run; diff source vs container ARC for one

## 2. Close

- [ ] 2.1 Comment on #353 with the PR (leave it open)
- [ ] 2.2 Archive after merge
