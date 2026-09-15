## 1. Feature PR concurrency

- [x] 1.1 Add workflow-level `concurrency` to `.github/workflows/feature-pull-request.yml`
      (`group: feature-pr-${{ github.event.pull_request.number }}`, `cancel-in-progress: true`)

## 2. Release / Helm serialize

- [x] 2.1 Add `concurrency` to `pre-release.yml` (`group: ${{ github.workflow }}-${{ github.ref }}`,
      `cancel-in-progress: false`)
- [x] 2.2 Same for `release.yml`
- [x] 2.3 Same for `helm-pre-release.yml`
- [x] 2.4 Same for `helm-release.yml`

## 3. Verify

- [x] 3.1 Spot-check YAML against API/sql_to_arc sibling snippets
- [x] 3.2 `openspec validate --changes` (or equivalent if change was hand-scaffolded)
- [x] 3.3 Pause for user commit/push; draft PR with `Fixes #182`
