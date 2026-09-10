# Adopt Devinfra Wave B — Tasks

Retrospective checklist against issue
[#168](https://github.com/fairagro/m4.2_middleware_harvester/issues/168) / PR
[#180](https://github.com/fairagro/m4.2_middleware_harvester/pull/180). Most items
are already implemented; remaining boxes are merge/verify follow-through.

## 1. Sync / adopt Wave B surfaces

- [x] 1.1 Adopt `versions.env` + `scripts/load-versions-env.sh`
- [x] 1.2 Adopt quality scripts (`quality-check.sh`, `quality-fix.sh`,
      `run-container-structure-test.sh`) + Bake/CST wiring (`docker-bake.hcl`)
- [x] 1.3 Adopt `setup-git-hooks.sh` + `scripts/git-hooks/pre-push`; remove
      shared LFS hook scripts (`setup-git-lfs.sh`, post-* LFS hooks)
- [x] 1.4 Adopt `scripts/devcontainer-post-create.sh` verbatim (no product
      `uv sync --all-packages` patch — see Devinfra #56)
- [x] 1.5 Adopt Dev Container Dockerfile / compose; thin
      `devcontainer.json` overlay; `.devcontainer/.env` → symlink `versions.env`
- [x] 1.6 Adopt Python quality fragments (`ruff.toml`, `mypy.ini`, `.pylintrc`,
      `.bandit`) + markdownlint/Prettier; remove obsolete `ruff.global.toml` /
      pyproject quality blocks as documented
- [x] 1.7 Adopt shared `.vscode/settings.json` baseline (product path overlays
      deferred to Devinfra #57 / #64)

## 2. Product-owned overlays and stubs

- [x] 2.1 Keep product-owned `.pre-commit-config.yaml` with header pointing at
      Devinfra #63; MYPYPATH / pylint / OpenSpec markdownlint globs as local
      deltas (#59)
- [x] 2.2 Document `devcontainer.json` ownership (#65); drop
      `.devcontainer/README.md`; add/update `docs/devcontainer.md`
- [x] 2.3 Add product stubs (`owslib`, `rdflib`) + `stubs/README.md`; arctrl /
      fable stubs local until Devinfra #67
- [x] 2.4 Keep `update-apk-dependencies.sh` product-local; PyPI via
      `uv run python` only (#68)
- [x] 2.5 `extension-pkg-allow-list=lxml` in `.pylintrc` (early #66) so
      `lxml.etree._Element` stays typed without `Any`

## 3. Typing / middleware cleanup enabled by Wave B tooling

- [x] 3.1 Remove obsolete `# type: ignore[import-untyped]` where stubs cover
      imports
- [x] 3.2 Small refactors required for new quality bar (e.g. orchestrator
      extract, registry `@staticmethod` / PLR suppressions) without domain
      behaviour change

## 4. Fleet follow-ups and sibling lock-ins

- [x] 4.1 Open Devinfra follow-ups for adopt friction (#56–#69 as applicable)
- [x] 4.2 Comment / update API Wave B #367 and sql_to_arc Wave B #94 with
      harvester pilot lock-ins
- [x] 4.3 Comment lock-ins on harvester #168

## 5. Verify

- [x] 5.1 `./scripts/quality-check.sh` / pre-push suite green on adopt branch
- [x] 5.2 Open draft PR #180 with `Fixes #168`
- [x] 5.3 `/review-fixer` on PR #180 (dismiss/follow-up; Fixed non-nit 0)
- [ ] 5.4 Mark PR ready / merge when human review complete; rebuild Dev
      Container once on `main`
- [ ] 5.5 Archive this change after merge (`/opsx-archive adopt-devinfra-wave-b`)
