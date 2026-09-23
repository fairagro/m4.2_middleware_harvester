## Context

See `proposal.md` for motivation. Explore lock-in is **option C**: new
`middleware/generic` beside `middleware/linked_data`, migrate incrementally.

Today `LinkedDataPlugin` composes `Sitemap` + `Dataset` + shared `DataMapper`
(`middleware.payload`). `DiscoveryResult` / `UrlDiscoveryResult` /
`JsonLdDiscoveryResult` live under `linked_data.dataset`. Shared registry helper
already exists in `middleware.payload.registry`.

## Goals / Non-Goals

**Goals:**

- Introduce Protocol / PayloadParser ABCs + registries in `middleware.generic`
- GenericPlugin orchestration with kind-check against repository `mapper:`
- First migrated pair: XML sitemap protocol + HTML JSON-LD parser
- Keep `linked_data` working for unmigrated sources

**Non-Goals:**

- Deleting `linked_data` in the first apply PR
- OAI (#142) or INSPIRE-in-generic
- Moving `DiscoveryResult` into `middleware.payload` (payload stays
  kind/mapper-only)

## Decisions

### 1. Package layout: `middleware/generic`

Own `protocol/`, `parser/`, `plugin.py`, `config.py`, `pipeline` reuse or thin
wrap of linked_data's bounded pipeline if needed (YAGNI: start by importing or
copying the minimal hook; extract shared pipeline only if both plugins need
identical code after first migration).

**Alternative considered:** Rename in place inside `linked_data` (option A) —
rejected by explore lock-in C.

### 2. Discovery types home

**Decision:** Move (or copy-then-delete in a later task) `DiscoveryResult`
hierarchy into `middleware.generic.discovery` (or `protocol.discovery`).
`linked_data` re-exports or depends on generic for those types during
coexistence so Sitemap/Dataset keep compiling.

**Alternative:** Leave types in `linked_data` and have `generic` import them —
creates plugin→plugin dependency, forbidden by principles. Rejected.

### 3. First migration: adapters vs move

**Decision:** Prefer **move** XML sitemap + HtmlJsonLdDataset into generic
registries under new type names (`protocol_type=xml`, `parser_type=html_jsonld`)
with thin shims in `linked_data` registries that delegate to the same
implementations until linked_data configs are gone. Avoid long-lived dual
implementations.

### 4. Config shape

```yaml
generic:
  protocol_type: xml
  parser_type: html_jsonld
  # protocol-specific fields (sitemap_url, http, …) — mirror today's linked_data
  # fields needed by the selected protocol/parser; design keeps a single Config
  # model with optional fields validated against selected types (same pattern as
  # linked_data Config), not a free-form dict.
mapper:
  type: schema_org_general
```

**Alternative:** Nested `protocol:` / `parser:` objects — defer; YAGNI until a
protocol needs disjoint required fields that break a flat model.

### 5. Pipeline / concurrency

**Decision:** First slice reuses the existing bounded pipeline approach from
linked_data (import shared helper if extracted, else duplicate minimally inside
generic). Do not block the abstraction work on a perfect shared pipeline
package.

### 6. Principles graph

Update `openspec/principles.md`: `generic/plugin.py` → protocol/parser →
`payload/`; `linked_data` may temporarily depend on `generic.discovery` types;
plugins still must not import each other's plugin modules.

## Risks / Trade-offs

- [Dual registries during shim] → Document shim lifetime; remove when last
  linked_data yaml migrates
- [Discovery type move churn] → One move task + re-export; keep public import
  paths stable where tests rely on them
- [Large apply PR] → Tasks staged: scaffold → contracts → plugin → first
  migration → config examples → later protocols as separate task groups /
  follow-up issues

## Migration Plan

1. Land package + abstractions + generic plugin with xml + html_jsonld
2. Switch one demo/example repository YAML to `generic:`
3. Migrate remaining linked_data pairs in follow-up PRs (`mycore_solr`,
   `regal_*`)
4. Deprecate `linked_data` key (logger.warning) then remove in a breaking change

Rollback: leave `linked_data` intact; operators stay on old key.

## Open Questions

- Whether bounded pipeline extraction into `middleware.harvester` or a tiny
  shared module happens in this change or after the second plugin needs it
  (default: after).
