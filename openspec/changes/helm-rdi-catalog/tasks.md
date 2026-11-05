# Tasks

## 1. Chart render path

- [ ] 1.1 Add `_helpers.tpl` (or equivalent) helper that builds effective config from `rdi_catalog` /
      `config.repositories` with fail-both, enabled filter, `rdi` from key, strip `enabled`, sort by key; wire
      `configmap.yaml` to render it; verify `helm template` with a catalog fixture lists only enabled RDIs in key order
- [ ] 1.2 Document `rdi_catalog` and mutual exclusion in `values.yaml` (commented example); bump `Chart.yaml` `version`;
      verify comments mention fail-both and `helm lint helm/harvester` succeeds
- [ ] 1.3 Add fixture values for list-only success, catalog success, and both-set failure; verify list-only still
      templates, catalog renders expected YAML, and both-set exits non-zero with a clear `fail` message

## 2. Validate

- [ ] 2.1 Run `openspec validate helm-rdi-catalog` and focused `helm lint` / `helm template` smoke; verify validate
      succeeds
