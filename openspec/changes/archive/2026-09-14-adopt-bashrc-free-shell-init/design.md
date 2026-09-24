## Context

See proposal.md — Why. Synced Dev Container already has bashrc-free `remoteEnv.PATH` (`.venv/bin` + `scripts/bin`) and
no `postStartCommand` bashrc patch ([docs/devcontainer.md](../../../docs/devcontainer.md)). Product leftovers
(`load-env.sh`, `setup-bashrc-load-env.sh`) and missing `product.env` are the adopt gap for
[#207](https://github.com/fairagro/m4.2_middleware_harvester/issues/207).

## Goals / Non-Goals

**Goals:**

- Remove deprecated bashrc/`load-env` product scripts.
- Ship product-owned `.devcontainer/product.env` for `MYPYPATH` + `CST_BAKE_TARGET`.
- Align product docs with the synced bashrc-free contract.

**Non-Goals:**

- Editing synced `.devcontainer/devcontainer.json` / `docker-compose.yml` / `scripts/bin/*`.
- Changing harvest/middleware runtime behaviour.
- Migrating personal `~/.bashrc` on developer machines beyond documenting “remove old source lines once”.

## Decisions

1. **Delete `load-env.sh` entirely** rather than shrink it. Decrypt already lives in synced
   `scripts/devcontainer-post-create.sh`; aliases `k`/`d` are synced wrappers; PATH is `remoteEnv`. No remaining product
   delta belongs in a sourced shell blob. _Alternative:_ thin stub that only warns — rejected (encourages re-fork).

2. **Delete `setup-bashrc-load-env.sh`**. Synced JSON no longer calls it. _Alternative:_ keep as no-op — rejected (dead
   surface).

3. **Add `.devcontainer/product.env`** (overlay, not synced) with the same `MYPYPATH` roots as reusable CI and
   `CST_BAKE_TARGET=harvester`. Compose already loads it optionally (`required: false`).

4. **`skip_specs: true`** — tooling/Dev Container adopt only.

## Risks / Trade-offs

- [Stale `~/.bashrc` still sources deleted `load-env.sh`] → Mitigation: PR / AGENTS note to remove the old `source …`
  line once; shell still works via `remoteEnv` after rebuild even if bashrc errors until cleaned.
- [Missing rebuild after merge] → Mitigation: call out Dev Container rebuild in PR test plan.
- [Developers without `product.env`] → Mitigation: commit the overlay in-repo (no secrets).
