## 1. Decision record

- [x] 1.1 Confirm real production CSW scale: `dev_environment/config.all-rdis.yaml` (bonares, ~27 records),
      `helm/harvester/values.yaml` (example config only; no production values in this repo), `csw_thread_pool_size`
      default and its `<10` concurrent-repositories rationale (`openspec/specs/csw-harvesting/design.md`,
      `openspec/specs/csw-threadpool/design.md`).
- [x] 1.2 Write decision 7 in this change's `design.md`, to be folded into `openspec/specs/csw-harvesting/design.md` on
      archive.
- [x] 1.3 `openspec validate defer-csw-http-pooling --strict`

## 2. Close out PR #347 and issue #19

- [x] 2.1 Reply on PR #347 conceding the review, with the concrete numbers (bonares ~27 records / ~10 per page ⇒
      ~0.2-0.3s once daily, vs. the 151-record benchmark's ~1.2s).
- [x] 2.2 Close PR #347 without merging.
- [x] 2.3 Close issue #19's pooling half, linking this change once archived.

## 3. Land and archive

- [x] 3.1 Commit on `chore/defer-csw-http-pooling`, open a PR (#355), get it merged (no code changes, so no quality-gate
      run beyond `openspec validate`).
- [x] 3.2 `openspec archive defer-csw-http-pooling`, confirm decision 7 lands in
      `openspec/specs/csw-harvesting/design.md`.
