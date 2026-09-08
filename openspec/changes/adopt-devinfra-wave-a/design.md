# Adopt Devinfra Wave A — Design

## Context

See `proposal.md` for motivation (#167, Devinfra Wave A, fleet F1). This repo is
mostly **greenfield** for Wave A: no `docs/ai_review_policy.md`, no fixer
skills/commands, no `scripts/ai` / `m42-ai`, no `principles.global.md`, no
surface-bar files. Local exceptions today: `.agents/skills/arctrl/` (replace
with Devinfra), `.agents/skills/config-wrapper/` (keep), and `scripts/bin/git`
(Wave B territory — do not touch in this change). Product principles currently
live as a capability at `openspec/specs/principles/` (SHALL requirements + full
narrative); P3 moves the product overlay to `openspec/principles.md` and deletes
that capability folder.

Explore decisions (including surface overlay model) are on
[issue #167](https://github.com/fairagro/m4.2_middleware_harvester/issues/167).
Pinned SHA matches the middleware_api pilot proposal.

## Goals / Non-Goals

**Goals:**

- Synced Wave A paths match Devinfra at the pinned SHA (no intentional local drift).
- Agents run `/review-fixer` (and create/issue-fixer) via `m42-ai` with
  `scripts/bin/gh` auth matching skill docs.
- Surface-bar **rules** in synced policy; **default path map** in synced
  `.global.md`; **product path rows** only in local `docs/surface-quality-bar.md`.
- Shared foundation only in `principles.global.md`; harvester product contract
  (plugin architecture, module graph, foundation/mapping contract, domain-over-
  plumbing) in `openspec/principles.md`.
- Pointers (`AGENTS.md`, `openspec/config.yaml`) no longer cite
  `openspec/specs/principles/`.

**Non-Goals:**

- Designing Devinfra sync automation or Wave B/C surfaces.
- Changing harvest/runtime behaviour or domain OpenSpec requirements (inspire,
  linked-data, …).
- Keeping a parallel Finder/surface section in `principles.md`.

## Decisions

### D1: Verbatim sync from pinned Devinfra SHA

Copy listed paths from `fairagro/m4.2_middleware_devinfra` at
`906870bd18fa7fef3c5593f75440291e04ceb43e`. Do not hand-edit synced files after
copy.

**Reason:** Same SoT as the API pilot; avoids fleet drift.
**Alternatives:** Wait for #13 (optional); cherry-pick with local edits (forks).

### D2: A + thin Auth-B in one PR

Include `scripts/bin/gh`, `scripts/dev-tokens.sh`, `scripts/set-dev-tokens.sh`;
exclude changing `scripts/bin/git` and the rest of Wave B.

**Reason:** Skills document these wrappers; existing git wrapper stays for a
later Wave B adopt.
**Alternatives:** A-only (auth docs mismatch); full Wave B (too large).

### D3: `m42-ai` via `--project scripts/ai`

Do not add `scripts/ai` to the product root uv workspace.

**Reason:** Matches Devinfra/product template used by the API pilot.
**Alternatives:** Workspace member now (optional later).

### D4: P3 — move `specs/principles` → `openspec/principles.md`

1. Add `openspec/principles.global.md` verbatim from Devinfra.
2. Create `openspec/principles.md` that extends `.global` (read-first; do not
   weaken Type Safety / Supported environment). Migrate product-only content
   from `openspec/specs/principles/spec.md`: Foundation Contract (mapping docs),
   Purpose, plugin architecture, harvester-specific Values (memory-safe, failure
   isolation, stateless, domain-over-plumbing), product Constraints (generator
   contract, `HarvesterError`, quality gates as they apply here), Module
   Dependency Graph, Extension Points, Configuration (product) pointing at
   ConfigWrapper / config-wrapper skill.
3. Drop duplicated shared sections that `.global` already owns.
4. Delete `openspec/specs/principles/` (including any `design.md` if present).
5. Retarget `AGENTS.md` and `openspec/config.yaml` to `openspec/principles.md`
   (+ mention `.global`).

**Reason:** Issue #167 explore lock; align with fleet P3 layout; agents expect
`openspec/principles.md`.
**Alternatives:** Keep capability folder as overlay (rejected); dual-write
`principles.md` + `specs/principles` (drift).

### D5: Surface-bar product overlay (who can hurt whom)

Sync `docs/surface-quality-bar.global.md` verbatim. Create local
`docs/surface-quality-bar.md` mirroring the API pilot’s two-row model, adapted
to the harvester:

| Surface | Typical paths | Bar |
| ------- | ------------- | --- |
| **Operator-facing contracts** | `middleware/harvester/.../main.py`, `orchestrator.py`, `config.py`, `plugin_base.py`, `upload.py`, `reporting.py`, `healthcheck.py`; repository/plugin Config models; operator YAML / ConfigWrapper env overrides | Full boundary: config/CLI/plugin contract/upload-report correctness; fix when in PR |
| **Source adapters + mapping internals** | `middleware/inspire/`, `middleware/linked_data/` (clients, datasets, sitemaps, mappers, pipelines); `nice_http_client.py`; other harvest-domain code not above | Uphold operator/API contracts; third-party care on realistic CSW/HTTP/Solr/Regal paths; dismiss exotic edges |

When both apply, pick the **stricter** (usually operator-facing). Global rows
cover scripts (incl. `scripts/bin/git`), `scripts/ai/`, docs/`*_mapping.md`,
vendor skills, OpenSpec cadence. Keep `.agents/skills/config-wrapper/` on the
docs/agent happy-path bar unless a change touches runtime contracts.

**Reason:** Global `middleware/*/src/` alone is too coarse; API overlay pattern
ports cleanly to operator vs source-adapter.
**Alternatives:** Skip local overlay (rejected); put Finder examples in
principles (superseded by #32).

### D6: Shared `arctrl`; keep `config-wrapper`

Replace `.agents/skills/arctrl/` with Devinfra’s first-party skill. Do not
delete `.agents/skills/config-wrapper/`. No `scan-secrets` present — nothing to
remove. Vendor set `{gh,docker,hadolint,uv}`.

**Reason:** #35 + product-local skill inventory.
**Alternatives:** Keep drifted local arctrl (rejected).

### D7: `skip_specs: true`

No deltas under `openspec/changes/.../specs/`. Deleting `specs/principles/` is
layout migration documented here and in tasks, not a requirement delta package.

**Reason:** Tooling/docs adopt; domain harvest specs unchanged.
**Alternatives:** Invent a principles capability delta (unnecessary noise).

## Risks / Trade-offs

- **[Risk] Legacy `tokens.env` non-b64 lines break after Auth-B** → Mitigation:
  document one-time `source ./scripts/set-dev-tokens.sh` in PR / smoke notes.
- **[Risk] Principles move breaks agent/doc links** → Mitigation: grep and
  update `AGENTS.md`, `openspec/config.yaml`, and any remaining
  `specs/principles` references in the same PR.
- **[Risk] Replacing local arctrl drops product-only tips** → Mitigation: diff
  local vs Devinfra before overwrite; move unique tips to AGENTS or
  config-wrapper if still needed.
- **[Risk] Later #13 sync overlaps manual A** → Mitigation: pin SHA; do not
  hand-edit synced paths after merge.
- **[Risk] API pilot still open** → Mitigation: same SHA already recorded on
  API proposal; if Devinfra `main` moves, re-pin only by explicit decision.

## Migration Plan

1. Pin SHA; copy Wave A paths + thin Auth-B; replace arctrl; add vendor skills.
2. Add `docs/surface-quality-bar.md`; write P3 `openspec/principles.md`; delete
   `openspec/specs/principles/`; retarget pointers; minimal lint excludes.
3. Verify `uv run --project scripts/ai m42-ai --help` / `auth-status` and
   `scripts/ai` tests.
4. Smoke `/review-fixer` on one PR; brief create/issue-fixer entry checks.
5. Diff synced paths against pinned SHA (overlays excepted).

Rollback: revert the adopt PR.

## Open Questions

None that block implementation — explore locks on #167 cover P3 move, timing,
and surface model.
