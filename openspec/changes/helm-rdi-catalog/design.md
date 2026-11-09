# Design

## Context

See proposal.md — Why. Today `helm/harvester/templates/configmap.yaml` does `toYaml .Values.config` with no transform.
Infra umbrellas own a map-shaped catalog and cannot rewrite this dependency’s template.

## Goals / Non-Goals

**Goals:**

- Materialize `rdi_catalog` → `config.repositories` in-chart
- Fail closed when both non-empty sources are set
- Keep list-only installs unchanged
- Deterministic YAML (sort by key)

**Non-Goals:**

- Append/merge of catalog into an explicit list
- Changing Python plugin config models
- Unifying Middleware API `known_rdis`

## Decisions

1. **Fail when both non-empty** — Matches issue comment lock-in. Empty list + catalog is allowed (catalog wins by being
   the only populated source). Alternative rejected: silent append.

2. **Build effective config in a named helper** — e.g. `harvester.configYaml` that deep-copies/merges `config`, replaces
   `repositories` when catalog is active, then `toYaml`s. Keeps `configmap.yaml` one line and testable via
   `helm template`.

3. **`enabled` defaults** — Treat missing `enabled` as false (safe; only explicit true harvests). Document in values
   comments.

4. **Chart version bump** — Patch bump `Chart.yaml` `version` in this change so OCI consumers can pin the new contract.

5. **Verification** — Add small values fixtures under `helm/harvester/fixtures/` and assert with `helm template` in
   tasks (lint hook already smokes bare chart).

6. **Defaults favour the catalog** — Example RDIs live under `rdi_catalog` with `enabled: false`; `config.repositories`
   defaults to `[]`. Legacy list-only overlays must set `rdi_catalog: null` (Helm map merge does not clear keys with
   `{}`).

## Risks / Trade-offs

- **[Risk] Helm template deep-copy quirks** → Prefer `mustMergeOverwrite` / `deepCopy` patterns already common in
  charts; keep transforms minimal.
- **[Risk] Operators forget to clear example `config.repositories` when adopting catalog** → Fail-both surfaces
  leftovers immediately.

## Migration Plan

1. List-only: no change.
2. Catalog adopters: set `config.repositories: []` (or omit) and populate `rdi_catalog`.
3. Infra bumps chart dependency after OCI publish.
