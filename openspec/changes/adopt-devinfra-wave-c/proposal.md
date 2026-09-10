# Adopt Devinfra Wave C — Proposal

## Why

Devinfra Wave C reusable CI (#11, #12) and the product-app Bake layout (#28 / #36)
are on `main`. Issue
[#169](https://github.com/fairagro/m4.2_middleware_harvester/issues/169) asks this
repo to call those reusables and stop maintaining forked local
`reusable-*.yml` / Helm release scripts. Sync automation (#13) remains open —
manual adopt now, then accept sync PRs later.

**Golden rule (this change):** never hand-edit synced Devinfra files. Prefer a
generic Devinfra SoT; else `.global` + product-local split; local edits to a
shared file only as last resort **and** documented upstream.

## What Changes

- Point product callers (`feature-pull-request`, `pre-release`, `release`) at
  Devinfra `reusable-code-quality` / `reusable-build` / `reusable-check` /
  `reusable-release` (`@main` for early adopt; pin later if desired).
- Adopt **Bake product-app layout**: sync `docker/Dockerfile.product-app.base`
  verbatim; keep thin product-local `docker/Dockerfile.harvester` + root
  `docker-bake.hcl`; drop monolith build assumptions.
- Switch Helm callers to Devinfra `reusable-helm-pre-release` /
  `reusable-helm-release` with chart inputs; delete or thin local Helm workflow
  bodies that duplicate shared logic.
- Delete local forked `.github/workflows/reusable-{code-quality,check,build,release}.yml`
  once callers are green.
- Keep product-only workflows local (`codeql.yml`, etc.).
- Document sync path (#13) in PR / AGENTS briefly; do not invent sync automation.
- Optional later: markdown in reusable code-quality (#40) — out of MVP.

## Capabilities

### New Capabilities

_(none — tooling/CI adopt; `skip_specs: true`)_

### Modified Capabilities

_(none)_

## Impact

- GitHub Actions callers and Docker/Helm release paths.
- Image build contract moves to Bake + shared base stages (BREAKING vs old
  monolith `docker build -f Dockerfile.harvester` in CI).
- CST / `scripts/run-container-structure-test.sh` must keep working with Bake
  targets after layout change.
- No domain harvest/mapping behaviour change.
