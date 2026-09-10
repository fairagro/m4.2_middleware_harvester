# Adopt Devinfra Wave C — Design

## Context

See `proposal.md`. Wave A/B already adopted. Local CI still `uses:` forked
reusables under `.github/workflows/`. Devinfra `docs/ci.md` defines caller
patterns and the Bake product-app contract (no monolith fallback).

## Goals / Non-Goals

**Goals:**

- Callers use Devinfra reusables with explicit `workflow_call` inputs (no silent
  repo Variables for identity).
- Product-app image: synced base + thin last stage + product `docker-bake.hcl`.
- Helm uses Devinfra Helm reusables.
- Golden rule enforced: no consumer patches to synced trees.

**Non-Goals:**

- Implementing Devinfra sync (#13) or CI markdown (#40).
- Changing CodeQL / other product-only workflows beyond necessary secrets/perms.
- Renaming GHCR image history (preserve `image_base_name` used in production).

## Decisions

### D1: Pin `@main` for early adopt

Call Devinfra workflows at `@main`. Freeze to SHA/tag in a follow-up when the
fleet wants a locked contract.

**Reason:** Issue #169 / Devinfra docs allow `@main` while CI surface moves.
**Alternatives:** SHA pin now (safer, more churn on every Devinfra fix).

### D2: Golden rule order for gaps

1. Make Devinfra reusable/base generic enough for harvester + API + sql_to_arc.
2. Else split `.global` / product-local (document in Devinfra).
3. Else last-resort consumer exception **documented in Devinfra** — never a
   silent local fork of a synced file.

**Reason:** User lock-in + Wave B pilot policy (#57).

### D3: Bake layout before switching `reusable-build`

Adopt `docker/Dockerfile.product-app.base` (verbatim sync), rewrite
`Dockerfile.harvester` as last stage, expand `docker-bake.hcl` per Devinfra
examples, then point build/check/release at Devinfra.

**Reason:** Devinfra build is Bake-only (BREAKING #36).
**Alternatives:** Switch quality-only first (rejected for this MVP — `go` full).

### D4: Caller inputs

Use Devinfra-documented inputs, e.g.:

- `components: '["harvester"]'`
- `python_package_root: middleware` (code-quality)
- `image_base_name: <current GHCR base>` — preserve existing naming from local
  `IMAGE_BASE_NAME` / `vars` default (`fairagro-advanced-middleware` unless
  product docs say otherwise; confirm against current published tags)
- Helm: `chart_dir` / chart name inputs per Devinfra Helm reusables

### D5: Delete local reusable forks after green

Remove
`reusable-{code-quality,check,build,release}.yml` from the product repo once
callers reference Devinfra. Do not keep “just in case” copies (drift).

### D6: Helm in same MVP

Replace local `helm-pre-release.yml` / `helm-release.yml` bodies with thin
callers to Devinfra Helm reusables (or equivalent `uses:` pattern from
`docs/ci.md`).

### D7: Sync #13

After adopt, ongoing shared-file updates come via sync PRs; fix upstream, never
hand-edit allowlisted paths. Mention in PR summary.

### D8: Healthcheck binary stays product-local (no synced-base patch)

Synced `Dockerfile.product-app.base` builds **one** primary onedir binary.
Harvester also needs a PyInstaller `--onefile` `healthcheck` (liveness-probe
spec + Helm probe path). Per golden rule we **do not** fork the synced base.

**Approach:** product-local `docker/Dockerfile.harvester-healthcheck` + Bake
targets `harvester-wheels` / `harvester-healthcheck`, wired into last stage via
Bake `contexts.healthcheck_bins`. Upstream:
[devinfra#71](https://github.com/fairagro/m4.2_middleware_devinfra/issues/71).

## Risks / Trade-offs

- **[Risk] Bake adopt breaks CST / local smoke** → Align
  `run-container-structure-test.sh` / Bake target names; smoke `docker buildx bake`
  before deleting local build workflow.
- **[Risk] `image_base_name` mismatch** → Read current release tags / vars;
  pass explicit input (`fairagro-advanced-middleware`).
- **[Risk] Helm chart paths differ** → `helm/harvester` + Chart.yaml `name`.
- **[Risk] Dual Bake targets slower locally** → Accept until Devinfra secondary
  binary lands.

## Migration Plan

1. Land Bake + thin Dockerfile + bake.hcl.
2. Switch callers; run feature-PR CI on the branch.
3. Delete local reusable forks.
4. Switch Helm; smoke pre-release path if secrets allow (or dry-run review).
5. Human marks PR ready; rebuild not required for CI adopt (optional DC rebuild).

## Open Questions

_(none — `image_base_name` confirmed during apply from existing workflow/vars.)_
