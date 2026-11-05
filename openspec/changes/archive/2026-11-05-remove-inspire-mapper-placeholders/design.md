# Design

## Context

See proposal.md — Why. Soft-lift lives in `RepositoryConfig.lift_inspire_mapper_placeholders`
(`middleware/harvester/config.py`). Infra #54 / #55 and in-repo YAML already use `inspire.placeholders`.

## Goals / Non-Goals

**Goals:**

- Delete the inspire←`mapper.placeholders` lift and warning (no replacement reject validator)
- Keep `mapper.placeholders` for linked-data / shared mappers; keep `inspire.placeholders` as the only inspire path
- Specs/docs/tests match “lift gone”

**Non-Goals:**

- Fail-closed dedicated message when inspire still sets `mapper.placeholders` (AC suggested it; operator lock-in: remove
  only — leftover field is inert for inspire because the plugin reads `inspire.placeholders`)
- Hard-cutting omitted-`mapper` soft-default for inspire

## Decisions

1. **Delete the lift; do not add a reject validator** — Soft-lift was the only inspire-specific handling of
   `mapper.placeholders`. After removal, setting it on an inspire repo still validates as ordinary `MapperConfig` data
   but is not copied into `inspire.placeholders` and is unused by the INSPIRE parser. A dedicated “move to
   inspire.placeholders” before/after validator would be a new special case for a removed feature (same bar as
   `mapper.type` / `linked_data` hard-cuts). Alternative: reject when inspire + `mapper.model_fields_set` contains
   `placeholders` — rejected per operator.

2. **Conflict check goes with the lift** — Differing `mapper.placeholders` vs `inspire.placeholders` was only enforced
   inside the lift. After removal there is nothing to reconcile.

3. **Commit as `feat!:`** — Surfaces the behaviour break (no more lift).

## Risks / Trade-offs

- [Out-of-repo YAML still on `mapper.placeholders` for inspire] → Placeholders no longer apply (empty default) until
  operators set `inspire.placeholders`; infra already migrated.
- [Silent unused `mapper.placeholders` on inspire] → Accepted trade-off vs a migration-only reject validator.

## Migration Plan

1. Operators already on `inspire.placeholders` — no action.
2. Operators still on `mapper.placeholders` for inspire — move the block under `inspire:` before upgrade.
3. Ship removal; no dual-read window beyond this PR.
