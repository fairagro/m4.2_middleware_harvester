# Adopt Devinfra Wave B — Design

## Context

See `proposal.md` for motivation (#168, Devinfra Wave B). Wave A already shipped
AI-review / Auth-B helpers. This change adopts Dev DX scripts, container base,
`versions.env`, and quality fragments. Implementation landed first via
issue-fixer / PR #180; design below records **locked decisions** from that
pilot (also summarized on API #367 / sql_to_arc #94).

Constraints: never hand-edit synced Devinfra paths after adopt
([devinfra#57](https://github.com/fairagro/m4.2_middleware_devinfra/issues/57));
Linux Dev Container is the supported environment; Python tooling via `uv` only.

## Goals / Non-Goals

**Goals:**

- Dev DX scripts/container/quality fragments match Devinfra; only documented
  overlays remain product-local.
- `versions.env` is the pin SoT for Dev Container / Bake / CST.
- Pre-commit + CI use fragment configs (`ruff.toml`, `mypy.ini`, `.pylintrc`)
  with path overlays via hook/CI args (`MYPYPATH`, `--source-roots`), not by
  editing synced fragments.
- Pilot lock-ins are written down so API / sql_to_arc Wave B does not re-debate.

**Non-Goals:**

- Wave C reusable CI / sync automation (#13).
- Shared Git LFS (removed upstream #39) — product-local LFS only if needed.
- Changing domain harvest / mapping OpenSpec requirements.
- Solving every fleet gap inside this PR (file Devinfra issues instead).

## Decisions

### D1: Manual adopt now, then accept sync

Adopt from Devinfra `main` in this PR rather than waiting for the first sync PR
from [#13](https://github.com/fairagro/m4.2_middleware_devinfra/issues/13).

**Reason:** Wave B was unblocked; harvester needed the DX surface immediately.
**Alternatives:** Wait for sync-only (slower); cherry-pick with local edits (forks).

### D2: Synced verbatim vs product-owned until overlay split

| Path | Ownership |
| ---- | --------- |
| `.devcontainer/Dockerfile`, compose fragments, `versions.env`, quality fragments (`ruff.toml`, `mypy.ini`, `.pylintrc`, `.bandit`, markdownlint/Prettier), shared scripts listed in Wave B / `docs/quality.md`, `.vscode/settings.json` | **Verbatim sync** — do not hand-edit |
| `.pre-commit-config.yaml` | **Product-owned** until [#63](https://github.com/fairagro/m4.2_middleware_devinfra/issues/63) |
| `.devcontainer/devcontainer.json` | **Product-owned thin overlay** until [#65](https://github.com/fairagro/m4.2_middleware_devinfra/issues/65) (name, workspaceFolder, volume `source=`) |

**Reason:** Avoid post-sync re-patching; encode ownership in file headers.
**Alternatives:** Treat everything as synced and re-patch after every sync (rejected).

### D3: `.devcontainer/.env` → symlink to `../versions.env`

Compose reads build-args from `.devcontainer/.env`; keep a symlink, not a copy.

**Reason:** Single pin file; no drift between Compose and Bake.
**Alternatives:** Duplicate env file (drift); bake-only without Compose env (breaks DC).

### D4: Drop `.devcontainer/README.md`; use `docs/devcontainer.md`

**Reason:** Fleet doc location; avoid stale DC-local README.
**Alternatives:** Keep both (duplicate).

### D5: `ruff.toml` verbatim — no product extend overlay for Wave B

Ship Devinfra `ruff.toml` as the only Ruff config; remove `ruff.global.toml` /
product extend dance from the Wave A transitional layout where possible.

**Reason:** `extend` replaces whole `per-file-ignores` tables; fleet wants one
SoT. Preview/debt ignores belong upstream or as temporary Devinfra policy.
**Alternatives:** Keep product overlay (drift); wait for cleaner Devinfra ruff (delay).

### D6: Path overlays only on hook/CI invocation

Do not put `MYPYPATH` / pylint `--source-roots` / `extension-pkg-allow-list`
into synced fragments as product-specific values except when the fleet agrees
(e.g. [#66](https://github.com/fairagro/m4.2_middleware_devinfra/issues/66) for
`lxml`). Product pre-commit / reusable workflow args carry harvester roots.

**Reason:** Sync overwrite safety (`docs/quality.md`).
**Alternatives:** Fork `.pylintrc` per product (rejected).

### D7: OpenSpec markdown ignores stay in product pre-commit until #59

Synced `.markdownlint-cli2.jsonc` stays verbatim; OpenSpec path ignores are
passed as negated globs on the product-owned markdownlint hook
([#59](https://github.com/fairagro/m4.2_middleware_devinfra/issues/59)).

**Reason:** IDE/cli2 vs hook divergence is tracked upstream; do not edit synced
cli2 in the consumer.
**Alternatives:** Patch synced ignores locally (sync drift).

### D8: Stubs policy

- Prefer shared `stubs/arctrl` (+ `fable_library`) via
  [#67](https://github.com/fairagro/m4.2_middleware_devinfra/issues/67).
- Product-local stubs for high-churn imports without shared stubs yet (`owslib`,
  `rdflib`).
- One-off libs: single `# type: ignore[import-untyped]` rather than a stub tree.
- Keep real `lxml.etree._Element` types; enable pylint introspection via
  `extension-pkg-allow-list=lxml` ([#66](https://github.com/fairagro/m4.2_middleware_devinfra/issues/66))
  — never `type X = Any`.

### D9: Do not patch synced `devcontainer-post-create.sh` for workspace uv sync

Fleet post-create `uv sync` coverage for product workspaces is
[#56](https://github.com/fairagro/m4.2_middleware_devinfra/issues/56). Use thin
product wrappers (`uv-sync-dev.sh` / `install-dev-hooks.sh`) instead of editing
the synced script.

### D10: `load-env.sh` remains product-local until #58

Do not run hook repair from every shell `load-env` invocation.

### D11: APK/PyPI pin helper

Keep `scripts/update-apk-dependencies.sh` product-local until
[#68](https://github.com/fairagro/m4.2_middleware_devinfra/issues/68) /
[#52](https://github.com/fairagro/m4.2_middleware_devinfra/issues/52). PyPI JSON
parse **only** via `uv run python` (no bare `python3` / `resolve_python`).

### D12: Agent `GH_TOKEN` shadow

Cursor agent env may shadow `/commandhistory/tokens.env`
([#69](https://github.com/fairagro/m4.2_middleware_devinfra/issues/69)). Workaround:
`env -u GH_TOKEN …` until wrapper policy lands.

## Risks / Trade-offs

- **[Risk] Synced `.vscode` `pytestArgs: ["scripts/ai/tests"]` hides product tests** →
  Track [#57](https://github.com/fairagro/m4.2_middleware_devinfra/issues/57); do not
  fork settings in consumer.
- **[Risk] Product-owned pre-commit drifts from Devinfra skeleton** → Header +
  [#63](https://github.com/fairagro/m4.2_middleware_devinfra/issues/63); intentional
  whole-`middleware/` hooks match CI.
- **[Risk] Retrospective OpenSpec vs already-merged code** → Tasks marked done
  against PR #180; archive when #168 closes / PR merges; do not re-implement.

## Migration Plan

1. Merge PR #180 (draft → ready when review cycle done).
2. Rebuild Dev Container once; run `./scripts/quality-check.sh` + pre-push CST.
3. Sibling repos: apply lock-in comment on Wave B issues (done for API #367 /
   sql_to_arc #94).
4. After Devinfra #56–#69 land, accept sync PRs; drop local emergency patches
   (e.g. early `#66` pylintrc line) when overwritten by sync.

## Open Questions

_(none deferrable — fleet gaps are filed as Devinfra issues.)_
