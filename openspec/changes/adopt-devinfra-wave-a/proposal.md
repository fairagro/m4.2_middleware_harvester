# Adopt Devinfra Wave A — Proposal

## Why

Shared Devinfra Wave A (AI review / agent stack) is extracted and closed upstream
([fairagro/m4.2_middleware_devinfra](https://github.com/fairagro/m4.2_middleware_devinfra)
issues #4–#6, #14–#16, plus [#32](https://github.com/fairagro/m4.2_middleware_devinfra/issues/32)
surface-bar split and [#35](https://github.com/fairagro/m4.2_middleware_devinfra/issues/35)
canonical arctrl skill). This harvester repo has **no** Wave A stack yet (greenfield
adopt aside from a local arctrl skill and product `config-wrapper`). Issue
[#167](https://github.com/fairagro/m4.2_middleware_harvester/issues/167) asks to adopt
the shared stack without local drift on synced paths, reusing the fleet matrix from
the middleware_api pilot ([#366](https://github.com/fairagro/m4.2_advanced_middleware_api/issues/366)).
Wave A prereqs on Devinfra are **done**; sync automation (#13) remains optional.
Start **now** on the same pinned SHA as the API pilot (do not wait for API PR merge).

**Pinned Devinfra SHA for this adopt:** `906870bd18fa7fef3c5593f75440291e04ceb43e`
(document the same value in the adopt PR description).

## What Changes

- Copy synced Wave A paths from Devinfra at the **pinned SHA**: policy,
  `docs/surface-quality-bar.global.md`, Bugbot/Copilot entries,
  `/review-fixer` + `/create-issue` + `/issue-fixer` skills/commands/prompts,
  thin fixer docs, first-party `.agents/skills/arctrl/`, vendor skills
  `{gh,docker,hadolint,uv}`, `scripts/ai/` / `m42-ai`,
  `openspec/principles.global.md`.
- Add product-local `docs/surface-quality-bar.md` overlay (operator-facing vs
  source-adapter surfaces — see design; do **not** put product rows in `.global.md`).
- **Thin Auth-B** (same PR): sync `scripts/bin/gh`, `scripts/dev-tokens.sh`,
  `scripts/set-dev-tokens.sh`; leave existing `scripts/bin/git` untouched.
- **P3 principles:** add `.global` verbatim; **move** product content from
  `openspec/specs/principles/` into `openspec/principles.md` as the overlay;
  **remove** the `specs/principles` capability; retarget `AGENTS.md` /
  `openspec/config.yaml` pointers. Do not weaken Type Safety / Supported
  environment from `.global`.
- Replace local `.agents/skills/arctrl/` with the shared first-party skill; keep
  product-local `.agents/skills/config-wrapper/`.
- Minimal lint-exclude updates for new vendor skills; thin `AGENTS.md` pointers.
- Smoke-test `/review-fixer` (and briefly create/issue-fixer entrypoints).

### Non-goals

- Full Wave B (changing `scripts/bin/git`, quality/pre-commit skeleton, Dev
  Container) or Wave C (CI `uses:`).
- Root `pyproject.toml` uv workspace membership for `m42-ai` (use
  `uv run --project scripts/ai …`).
- Forking product examples into synced `docs/ai_review_policy.md` or
  `docs/surface-quality-bar.global.md`.
- Blocking on Devinfra sync automation (#13).
- Changing harvest/runtime behaviour under `middleware/**`.

## Capabilities

### New Capabilities

- _none — `skip_specs: true`._ Shared agent/tooling behaviour is owned by
  Devinfra specs; this change does not add product domain requirements under
  `openspec/specs/`.

### Modified Capabilities

- _none as requirement deltas._ Removing `openspec/specs/principles/` is a
  **docs/layout** migration into `openspec/principles.md` (P3); no new SHALL
  scenarios are introduced under `openspec/changes/.../specs/`.

## Impact

- **Docs / agent stack:** new synced paths under `docs/` (incl. surface-bar
  `.global`), `.cursor/`, `.github/`, `.agents/skills/` (incl. `arctrl`),
  `scripts/ai/`, `openspec/principles.global.md`.
- **Local docs:** new `openspec/principles.md`, `docs/surface-quality-bar.md`;
  update `AGENTS.md`, `openspec/config.yaml`.
- **Removed:** `openspec/specs/principles/` (content moved to `principles.md`).
- **Auth helpers:** `scripts/bin/gh`, `scripts/dev-tokens.sh`,
  `scripts/set-dev-tokens.sh` (may require one `source ./scripts/set-dev-tokens.sh`
  for legacy non-`b64:` token store lines).
- **Unchanged:** `middleware/**` runtime, `scripts/bin/git`, product OpenSpec
  domain specs (except deleting `specs/principles/`), Wave B/C surfaces,
  `.agents/skills/config-wrapper/`.
- **Fleet:** decision comment on #167; same SHA as API pilot proposal.
