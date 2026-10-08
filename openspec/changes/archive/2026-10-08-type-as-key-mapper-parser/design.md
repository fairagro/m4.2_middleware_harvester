# Design

## Context

See proposal.md — Why. Protocol already ships nested type-as-key under `generic.protocol`. Mapper and parser remain
`{ type: … }` discriminators. Soft-deprecate preserves operator YAML; hard-cut is a separate issue.

## Goals / Non-Goals

**Goals:**

- One config idiom for protocol / mapper / parser selection
- Legacy `{ type: … }` keeps working with a clear warning
- Shared vs type-local fields match the protocol pattern (`placeholders` shared; Regal/DCAT fields under type child)

**Non-Goals:**

- linked_data sitemap/dataset type-as-key
- Removing the lift path in this change

## Decisions

1. **Exactly one type-named child** — Mirror `ProtocolConfig`: validation fails if zero or multiple mapper/parser type
   keys are set (after lift). Active type is the single set child name.

2. **Shared siblings** — `mapper.placeholders` stays a sibling of the type key (applies to all mappers). Parser has no
   cross-type shared sibling today unless a future field appears; `jsonld_parse_threshold_bytes` / `allowed_context_url`
   live under JSON-LD type children only (ignored / absent for e.g. `phenoroam_xml`).

3. **Legacy lift in model validators** — Prefer lift inside `MapperConfig` / `ParserConfig` (`mode="before"` or after)
   so every consumer sees nested shape post-validation. Emit one `logger.warning` per config object that still used
   `type:`. Accessors used by plugins (`mapper.type`, `parser.type`) become properties reading the active child (or thin
   helpers) so call sites need minimal churn.

4. **Type-specific field ownership**

   | Field                                                  | Location                               |
   | ------------------------------------------------------ | -------------------------------------- |
   | `placeholders`                                         | `mapper` sibling                       |
   | `resource_base_url`                                    | under `regal_general` (and only there) |
   | `catalog_name` / `catalog_url`                         | under `ckanext_dcat`                   |
   | `allowed_context_url` / `jsonld_parse_threshold_bytes` | under `jsonld` / `html_jsonld`         |

5. **linked_data** — Document non-goal: migrate to `generic` rather than invent type-as-key under a deprecated plugin
   key.

6. **Follow-up hard-cut** — Separate Task: reject `type:` / remove lift after migration window (same shape as flat
   generic / mycore_solr hard-cuts).

## Risks / Trade-offs

- **[Risk] Call sites assume `mapper.type` attribute** → Mitigation: keep a read-only `type` / `active_*` property on
  the config models after lift.
- **[Risk] Out-of-repo YAML lag** → Mitigation: warning-only; in-repo examples already nested after this change.
- **[Trade-off] Larger YAML for mappers with no type-local fields** (`inspire_general: {}`) → Accept empty mapping child
  for consistency.

## Migration Plan

1. Land soft-deprecate + nested SoT; flip in-repo YAML.
2. Operators migrate when they next touch configs (warnings guide them).
3. Follow-up issue hard-removes `type:` after the window.

## Open Questions

None — hard-cut deferred to the follow-up issue.
