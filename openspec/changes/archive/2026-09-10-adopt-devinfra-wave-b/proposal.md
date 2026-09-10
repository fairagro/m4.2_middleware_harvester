# Adopt Devinfra Wave B — Proposal

## Why

Shared Devinfra Wave B (Dev DX: quality scripts/hooks, `versions.env`, thin Dev
Container, Python quality fragments) is closed upstream
([fairagro/m4.2_middleware_devinfra](https://github.com/fairagro/m4.2_middleware_devinfra)
#7–#10, #28, #39). Issue
[#168](https://github.com/fairagro/m4.2_middleware_harvester/issues/168) asks this
repo to adopt that surface so local scripts/container/quality tooling match the
fleet, with only documented product overlays remaining local. Wave A is already
archived here; Wave B was implemented via `/issue-fixer` on branch
`issue-168-adopt-devinfra-wave-b` / draft PR
[#180](https://github.com/fairagro/m4.2_middleware_harvester/pull/180). This change
folder is a **retrospective** OpenSpec record of that adopt (decisions + task
checklist), not a second implementation pass.

**Devinfra reference (adopt window):** `main` tip around merge of sync inventory
work — document the SHA used in the adopt PR if a pin was recorded; otherwise
treat “Devinfra `main` as of Wave B adopt” as SoT until sync (#13) owns pins.

## What Changes

- Adopt shared Wave B paths: `versions.env`, `load-versions-env.sh`,
  `quality-{check,fix}.sh`, CST runner + Bake wiring, `setup-git-hooks.sh` /
  `scripts/git-hooks/pre-push` (no shared Git LFS — [#39](https://github.com/fairagro/m4.2_middleware_devinfra/issues/39)),
  `devcontainer-post-create.sh`, Dev Container Dockerfile/compose fragments,
  Python quality fragments (`ruff.toml`, `mypy.ini`, `.pylintrc`, `.bandit`,
  markdownlint/Prettier), shared `.vscode/settings.json` baseline.
- Keep **thin product overlays**: `devcontainer.json` (name / workspaceFolder /
  volume `source=`), product-owned `.pre-commit-config.yaml` until
  [#63](https://github.com/fairagro/m4.2_middleware_devinfra/issues/63),
  product stubs (`owslib` / `rdflib`; arctrl stubs pending
  [#67](https://github.com/fairagro/m4.2_middleware_devinfra/issues/67)),
  `update-apk-dependencies.sh` until
  [#68](https://github.com/fairagro/m4.2_middleware_devinfra/issues/68).
- `.devcontainer/.env` → symlink to `../versions.env` (Compose), not a copy.
- Drop local `.devcontainer/README.md` in favour of `docs/devcontainer.md`.
- Typing cleanup enabled by stubs / pylint `extension-pkg-allow-list=lxml`
  (upstream intent [#66](https://github.com/fairagro/m4.2_middleware_devinfra/issues/66)).
- File Devinfra follow-ups for fleet gaps discovered during adopt (#56–#69);
  mirror lock-ins onto sibling Wave B issues (API #367, sql_to_arc #94).

## Capabilities

### New Capabilities

_(none — tooling/Dev DX adopt; `skip_specs: true`)_

### Modified Capabilities

_(none — no domain harvest/mapping requirement changes)_

## Impact

- Dev Container rebuild / postCreate, pre-commit + pre-push quality gates, CST
  Bake path, IDE settings synced from Devinfra.
- Product `middleware/` packages: import stub / ignore cleanup; no intentional
  harvest behaviour change.
- Sibling product Wave B issues receive pilot lock-in comments so decisions are
  not re-litigated.
- Deferred fleet work lives on Devinfra issues (sync overlays, pytestArgs,
  load-env, GH_TOKEN shadow, APK updater, etc.), not as silent local forks.
