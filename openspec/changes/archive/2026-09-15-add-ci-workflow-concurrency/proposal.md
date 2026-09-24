## Why

Rapid PR pushes can overlap Feature-PR CI runs because `.github/workflows/feature-pull-request.yml` has no
workflow-level `concurrency`. Manual `pre-release` / `release` / Helm callers likewise lack a serialize policy, so
overlapping `workflow_dispatch` runs can race. Sibling products (API, sql_to_arc) already use the standard caller
pattern; Harvester [#182](https://github.com/fairagro/m4.2_middleware_harvester/issues/182) tracks adopt here. Devinfra
[#76](https://github.com/fairagro/m4.2_middleware_devinfra/issues/76) will document the snippet in `docs/ci.md` —
product YAML is not on the sync allowlist, so this change lands the caller blocks now from the agreed acceptance
criteria.

## What Changes

- Add workflow-level `concurrency` to `feature-pull-request.yml`: group by PR number, `cancel-in-progress: true`.
- Add workflow-level `concurrency` to `pre-release.yml`, `release.yml`, `helm-pre-release.yml`, and `helm-release.yml`:
  serialize groups (`${{ github.workflow }}-${{ github.ref }}`), `cancel-in-progress: false`.
- Do not wait on synced `docs/ci.md` text (Devinfra #76 still open); match API/sql_to_arc callers.

## Capabilities

### New Capabilities

- (none — `skip_specs: true`)

### Modified Capabilities

- (none — CI caller YAML only; no harvester plugin behaviour change)

## Impact

- Feature PRs: newer pushes cancel superseded runs (saves minutes; aligns with siblings).
- Release/Helm dispatch: overlapping runs queue instead of canceling mid-publish.
- Non-goals: changing reusable workflows in Devinfra, required-check names, or detect-changes filters.
