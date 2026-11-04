# Design

## Context

See proposal.md — Why. Soft-deprecation (#466) left `RepositoryConfig.linked_data`, `LinkedDataPlugin` in
`PLUGIN_FACTORIES`, payload_type lift / mapper validators, and the full `middleware/linked_data` package. Equivalent
harvest paths already run via `generic` + Protocol/Parser/Mapper. Infra Publisso overlays no longer use the key.

## Goals / Non-Goals

**Goals:**

- Reject `linked_data:` at config load (clear migration error; no warn-and-continue)
- Remove orchestrator factory wiring and the `middleware/linked_data` workspace package
- Align OpenSpec + `openspec/principles.md` module graph; update migration docs

**Non-Goals:**

- Changing generic Protocol/Parser/Mapper behaviour
- Removing `middleware.payload.linked_data_mapper` (name is historical; shared RDF mappers stay)
- Rewriting archive history under `openspec/changes/archive/`

## Decisions

1. **Delete the workspace package, not a hollow stub** — After the plugin key is gone, nothing outside
   `middleware/linked_data` imports it. Drop the package from the uv workspace, harvester dependency, quality path
   lists, and tests. Alternative: keep the package unregistered — rejected; dead code and import-linter noise.

2. **Remove the Pydantic field (fail closed on unknown key / explicit reject)** — Prefer removing
   `RepositoryConfig.linked_data` so a leftover YAML key fails model validation. Add a focused `model_validator` or
   pre-parse check **only if** the default extra-forbid message is too opaque; message MUST name `generic:` +
   `docs/linked_data_to_generic.md`. Alternative: keep the field and always raise — rejected; invites reintroducing the
   type.

3. **Delete deprecation / lift paths with the field** — Remove `warn_deprecated_linked_data_plugin`,
   `linked_data.payload_type` lift, `validate_mapper_for_linked_data`, and resource_base_url conflict checks that only
   apply to that plugin. Alternative: keep lifts for one release — rejected; this change is the hard cut.

4. **`linked-data-harvesting` capability: reject + remove plugin requirements** — ADDED requirement that the plugin key
   is rejected; REMOVED all LinkedDataPlugin harvest / registry / coexistence / mycore_solr-under-linked_data
   requirements. Behaviour for former linked_data sources is owned by `generic-harvesting` and protocol/parser specs.
   Alternative: leave harvest requirements as documentation — rejected; archive would leave false SHALLs.

5. **`skipped-datasets`: rename obligation to generic** — REMOVED linked_data duplicate-discovery requirement; ADDED
   equivalent for generic (Protocol `discover()` already yields `SkippedRecord` on duplicate identity).

6. **Principles** — Update `openspec/specs/principles` (drop `linked_data` from protocol-plugin lists) **and** the
   narrative module graph in `openspec/principles.md` / AGENTS.md during apply (overlay is not only the delta spec).

7. **BREAKING signal** — Ship with `feat!:` (or `BREAKING CHANGE:` footer) so git-cliff / Release changelog surfaces the
   cut. No separate CHANGELOG.md file unless the repo already maintains one.

## Risks / Trade-offs

- [Out-of-repo YAML still on `linked_data:`] → Expected BREAKING; migration doc + validation error; fizz/draven already
  migrated.
- [Missed references in quality env / Docker / import-linter] → Grep `middleware.linked_data` / workspace member lists
  in apply checklist.
- [Confusion: `payload.linked_data_mapper` remains] → Docs MUST say the **plugin key** is removed; shared mapper package
  name is unchanged.

## Migration Plan

1. Operators already on `generic:` — no action.
2. Any remaining `linked_data:` → convert per `docs/linked_data_to_generic.md` before upgrading.
3. Ship removal; no dual-read window.
