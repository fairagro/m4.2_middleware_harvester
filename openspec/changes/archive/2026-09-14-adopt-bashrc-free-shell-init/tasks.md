## 1. Remove deprecated shell-init scripts

- [x] 1.1 Delete `scripts/load-env.sh`
- [x] 1.2 Delete `scripts/setup-bashrc-load-env.sh`
- [x] 1.3 Grep for remaining references (`load-env`, `setup-bashrc-load-env`, bashrc `source`) in product-owned files
      (`AGENTS.md`, `docs/` overlays if any) and update/remove them

## 2. Product Dev Container overlay

- [x] 2.1 Add `.devcontainer/product.env` with: -
      `MYPYPATH=stubs:middleware/inspire/src:middleware/harvester/src:middleware/linked_data/src:middleware/linked_data/tests/unit:middleware/inspire/tests/unit` -
      `CST_BAKE_TARGET=harvester`
- [x] 2.2 Confirm synced `devcontainer.json` `remoteEnv.PATH` already prepends `.venv/bin` and `scripts/bin` (no edit)
- [x] 2.3 Confirm synced Compose still has optional `env_file: product.env`

## 3. Verify

- [x] 3.1 Confirm `scripts/bin/{k,d,gh,git}` present from sync
- [x] 3.2 Spot-check: `uv run pre-commit run mypy --all-files` with `product.env` / `MYPYPATH` available
- [x] 3.3 `openspec validate --changes`
- [x] 3.4 Pause for user commit/push; draft PR with `Fixes #207`
