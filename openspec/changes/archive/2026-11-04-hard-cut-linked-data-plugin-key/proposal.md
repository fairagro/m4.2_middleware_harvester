# Proposal

## Why

`linked_data:` has been soft-deprecated since #296 / #466 (warn + in-repo YAML on `generic`). Publisso overlays on
fizz/draven migrated (#47 / #48). The remaining plugin key, orchestrator factory, and plugin-only Sitemap/Dataset stack
are migration debt: operators still get a warning path that should no longer exist, and specs still describe deprecated
coexistence.

## What Changes

- **BREAKING:** Remove the repository plugin key `linked_data` from `RepositoryConfig` and the orchestrator
  `PLUGIN_FACTORIES` entry. Config that still sets `linked_data:` MUST fail validation with a clear migration pointer to
  `generic:` + nested `protocol` / sibling `parser` / `mapper` (see `docs/linked_data_to_generic.md`).
- **BREAKING:** Remove `LinkedDataPlugin` and the `middleware/linked_data` workspace package (Sitemap/Dataset registries
  and plugin pipeline that existed only for that key). Shared RDF mappers stay in
  `middleware.payload.linked_data_mapper`; discovery/parsers stay in `middleware.parsing` / `middleware.generic`.
- Drop linked_data-only config lifts/validators (`payload_type` lift, plugin-key deprecation warning,
  `validate_mapper_for_linked_data`, resource_base_url conflict checks tied to the plugin).
- Update OpenSpec / principles module graph; rewrite migration docs from “deprecated shim” to “removed”.
- **BREAKING** note for operators via Conventional Commit (`feat!:` / `BREAKING CHANGE:`) so Release changelog surfaces
  it.

**Non-goals:** Changing `generic` Protocol/Parser/Mapper behaviour. Removing `middleware.payload.linked_data_mapper` or
shared parsers. Auto-migrating private out-of-repo YAML beyond the closed infra issues. Retyping #467 (tracked as Task;
this change uses OpenSpec by operator request).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `harvester-configuration`: Stop accepting `linked_data` as a plugin key; remove deprecation-warning requirement; drop
  legacy `linked_data.payload_type` lift scenarios; keep `generic` / `inspire` / `oai_pmh`.
- `linked-data-harvesting`: Replace deprecated-coexistence / plugin harvest requirements with hard rejection of the
  plugin key (canonical harvest path is `generic`).
- `skipped-datasets`: Move duplicate-discovery `SkippedRecord` obligation from the linked_data plugin to the generic
  plugin (already yields it from Protocol discovery).
- `principles`: Drop `linked_data` from the product module-dependency graph (package removed).

## Impact

- `middleware/harvester` config + orchestrator + tests
- Remove `middleware/linked_data` package (uv workspace members, quality path lists, Docker/devcontainer env if listed)
- `docs/linked_data_to_generic.md`, Helm/example comments that still advertise the shim
- OpenSpec deltas above; `openspec/principles.md` module graph
- Follow-up: close parent #296 when this lands if nothing else remains
