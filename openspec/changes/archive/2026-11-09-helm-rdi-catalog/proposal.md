# Proposal

## Why

Infra cannot turn a shared `rdi_catalog` map (enabled flags + URL overlays) into this chart’s `config.repositories` list
without forking the ConfigMap template (#578 / infra #44). The chart must optionally materialize that list at render
time so umbrella charts stay thin.

## What Changes

- Add optional top-level `rdi_catalog` values map; when non-empty, render `config.repositories` from enabled entries
  (`rdi` = map key, strip `enabled`, stable-sort by key).
- **BREAKING (render):** If both a non-empty `rdi_catalog` and a non-empty `config.repositories` are set,
  `helm template` / install **fails** (one source of truth — issue comment lock-in).
- Back-compat: absent/empty `rdi_catalog` keeps today’s `toYaml .Values.config` behaviour.
- Document in `values.yaml` (and NOTES/README if needed); bump chart `version`; add `helm template` fixtures proving
  catalog, list-only, and fail-both paths.

## Capabilities

### New Capabilities

- `helm-harvester-chart`: Helm chart values/render contract for harvester ConfigMap config, including optional
  `rdi_catalog` → `config.repositories` materialization and mutual exclusion with an explicit repositories list.

### Modified Capabilities

- (none)

## Impact

- `helm/harvester/` templates, helpers, `values.yaml`, `Chart.yaml` version
- OpenSpec `helm-harvester-chart`
- Consumers: fairagro/m4.2_infrastructure (dependency bump after OCI publish)
- Non-goals: unifying API `known_rdis`; changing harvester app plugin semantics; inventing merge/append when both
  sources are set
