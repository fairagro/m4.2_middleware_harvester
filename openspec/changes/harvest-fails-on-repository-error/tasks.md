# Tasks

## 1. Tests and fix

- [ ] 1.1 T1: a plugin yielding a repository-level error and no ARCs leads `harvest_arcs` to complete the harvest
      (repro; fails on `main` once asserting FAILED)
- [ ] 1.2 T2: after the fix the fake ApiClient sees `fail`, not `complete`
- [ ] 1.3 T3: 2 ARCs then a repository-level error → FAILED; `harvested_datasets` 2, exactly one repository issue
- [ ] 1.4 T4: only a `RecordProcessingError` → COMPLETED, `failed_datasets` 1
- [ ] 1.5 T5: ERROR log names RDI, harvest id and reason; a second repository in the same run completes

## 2. Verify and close

- [ ] 2.1 T6: dev stack (dmz-web-140): a PlabiPD-style repository error gives a FAILED harvest and leaves `{rdi}.json`
      untouched; note any trailing-ARC rejections from the in-flight race
- [ ] 2.2 Open the api_client issue (drain pending submissions before failing) and link it from #546
- [ ] 2.3 Archive after merge
