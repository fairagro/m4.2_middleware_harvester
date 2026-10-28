# Tasks

## 1. Tests and fix

- [x] 1.1 T1: a plugin yielding a repository-level error and no ARCs leads `harvest_arcs` to complete the harvest
      (repro; fails on `main` once asserting FAILED)
- [x] 1.2 T2: after the fix the fake ApiClient sees `fail`, not `complete`
- [x] 1.3 T3: 2 ARCs then a repository-level error → FAILED; `harvested_datasets` 2, exactly one repository issue
- [x] 1.4 T4: only a `RecordProcessingError` → COMPLETED, `failed_datasets` 1
- [x] 1.5 T5: ERROR log names RDI and reason (harvest id once api_client attaches it, see 2.2); a second repository in
      the same run completes

## 2. Verify and close

- [ ] 2.1 T6: end-to-end against a local API: a PlabiPD-style repository error gives a FAILED harvest and leaves
      `{rdi}.json` untouched; note any trailing-ARC rejections from the in-flight race
- [ ] 2.2 Open the api_client issue (drain pending submissions before failing; attach `harvest_id` to the exception
      `harvest_arcs` re-raises) and link it from #546
- [ ] 2.3 Archive after merge
