# Proposal

## Why

Client-produced RO-Crate can fail DataHUB `arc-export` only after upload. The shared
`fairagro-middleware-arc-validation` package now runs that same Docker gate locally; this harvester still has no per-RDI
fixture suite or CI job that calls it, so mapping regressions that break DataHUB are not caught in client CI.

## What Changes

- Depend on `fairagro-middleware-arc-validation` (PyPI ≥14.2.0).
- Add pre-baked representative RO-Crate fixtures under `tests/fixtures/arc_export/<rdi>/` for one RDI per major mapper
  family used in shipping examples: **inspire** (e.g. bonares-shaped), **schema.org/generic** (e.g. openagrar/edal),
  **regal** (e.g. publisso). Defer oai_pmh / phenoroam until those are treated as active in this MVP.
- Add `system_local` pytest that loads each fixture and asserts `validate_rocrate(...).ok` (readable `cause_excerpt` on
  failure).
- Keep commit-stage/pre-push free of Docker (`system_local` already deselected); add a Feature-PR CI job with Docker and
  a pinned `FAIRAGRO_ARC_EXPORT_IMAGE` digest.
- Document Docker requirement and how to add a fixture when a production/DataHUB failure appears.
- Git LFS only if a fixture is large enough to need it (not assumed for MVP JSON).

## Capabilities

### New Capabilities

- `arc-export-fixtures`: Per-RDI RO-Crate fixture gate via `fairagro-middleware-arc-validation` (`system_local` + CI
  Docker job); regression loop when DataHUB `arc-export` fails.

### Modified Capabilities

- (none)

## Impact

- Dependencies: `fairagro-middleware-arc-validation` on the package that owns the tests (likely `harvester` or workspace
  root/dev)
- New tests under `middleware/harvester/tests/system_local/` (or equivalent) + fixture tree
- Feature PR workflow: dedicated job with Docker
- Docs: short operator/dev note (README or `docs/`); OpenSpec `arc-export-fixtures`
- Non-goals: mocking Docker; running this suite on every commit locally; full live harvest→map in MVP (pre-baked crates)
