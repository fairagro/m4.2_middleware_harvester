# Proposal

## Why

Nested `generic.protocol` (shared `http` + type-as-key children) has been canonical since the protocol type-as-key
change. Deprecated flat fields (`protocol_type`, `sitemap_url`, `http`, `page_size`) still lift with a warning. In-repo
operator examples already use nested form; the migration window is over enough to hard-remove the flat tree (#383).

## What Changes

- **BREAKING:** Remove flat `protocol_type` / `sitemap_url` / `http` / `page_size` from
  `middleware.generic.config.Config`, plus the lift/conflict validator and deprecation warning copy for that tree.
- Require nested `protocol:` only; update tests and commented YAML examples that still exercise the flat tree.
- Update OpenSpec: drop flat-lift requirements; keep nested-only scenarios (and trim “or deprecated flat…” wording).

**Non-goals:** Removing `generic.jsonld_parse_threshold_bytes` (separate deprecation). Removing `linked_data:` (#467).
Changing Protocol behaviour beyond config surface.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `generic-harvesting`: Remove flat-lift requirement; require nested `protocol` only.
- `harvester-configuration`: Nested-only generic protocol config / `source_url` from `entry_url`.
- `harvest-protocol`: Drop “or deprecated flat config lifts…” from registry scenarios.
- `sitemap-mycore-solr`: Drop deprecated flat `protocol_type` / `sitemap_url` acceptance wording.
- `dcat-ap-protocol`: Drop deprecated flat `protocol_type: dcat_ap` / `sitemap_url` lift wording.
- `ckanext-dcat-to-arc-mapping`: Nested-only composition scenario (no flat protocol wording).

## Impact

- `middleware/generic` config + unit tests; some harvester config tests
- `dev_environment/config_example.yaml` (remove deprecated flat commented example)
- Docs that mention flat lift (`docs/linked_data_to_generic.md` deprecated flat form notes)
