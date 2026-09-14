## Why

Devinfra [#58](https://github.com/fairagro/m4.2_middleware_devinfra/issues/58) landed the fleet **bashrc-free** shell contract
(synced `devcontainer.json` prepends `.venv/bin` + `scripts/bin`; postCreate decrypts `.env` to a file only). Harvester
still ships product-local `scripts/load-env.sh` / `setup-bashrc-load-env.sh` leftovers and lacks `.devcontainer/product.env`
for `MYPYPATH` / `CST_*`. Adopt the contract cleanly so local hooks and CST match CI without mutating `~/.bashrc`.

## What Changes

- Delete deprecated product `scripts/load-env.sh` and `scripts/setup-bashrc-load-env.sh` (and any remaining postStart /
  docs pointers that reintroduce bashrc sourcing).
- Add product-owned `.devcontainer/product.env` with `MYPYPATH` (same roots as reusable CI) and `CST_BAKE_TARGET=harvester`.
- Confirm synced `remoteEnv.PATH` already includes `${workspaceFolder}/.venv/bin` and `${workspaceFolder}/scripts/bin`
  (no hand-edit of synced JSON/Compose).
- Rely on synced `scripts/bin/{k,d,gh,git}` and shared postCreate decrypt; keep personal tokens on `scripts/bin` /
  `set-dev-tokens.sh` only.
- Update product-local docs (`AGENTS.md` if needed) so they no longer recommend sourcing `load-env.sh`.

## Capabilities

### New Capabilities

- (none — `skip_specs: true`)

### Modified Capabilities

- (none — tooling / Dev Container adopt only; no harvester plugin/spec behaviour change)

## Impact

- Developers: after rebuild, PATH comes from Dev Container `remoteEnv` + `product.env`; no bashrc patch required.
- Quality: local mypy/pre-push CST regain overlays without editing synced hooks.
- Non-goals: changing Middleware harvest behaviour, inventing new aliases beyond synced `k`/`d`, reintroducing bashrc
  token loading, hand-editing synced `.devcontainer/devcontainer.json` / `docker-compose.yml`.
