## 1. Feature PR concurrency

- [ ] 1.1 Add workflow-level `concurrency` to `.github/workflows/feature-pull-request.yml`
      (`group: feature-pr-${{ github.event.pull_request.number }}`, `cancel-in-progress: true`)

## 2. Release / Helm serialize

- [ ] 2.1 Add `concurrency` to `pre-release.yml` (`group: ${{ github.workflow }}-${{ github.ref }}`,
      `cancel-in-progress: false`)
- [ ] 2.2 Same for `release.yml`
- [ ] 2.3 Same for `helm-pre-release.yml`
- [ ] 2.4 Same for `helm-release.yml`

## 3. Verify

- [ ] 3.1 Spot-check YAML against API/sql_to_arc sibling snippets
- [ ] 3.2 `openspec validate --changes` (or equivalent if change was hand-scaffolded)
- [ ] 3.3 Pause for user commit/push; draft PR with `Fixes #182`
