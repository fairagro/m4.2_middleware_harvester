## Why

`linked_data` is already a mini generic plugin restricted to RDF discovery/fetch (`Sitemap` + `Dataset` + shared
`DataMapper`). A true **generic** harvest plugin composing **Protocol** (discovery/transport) + **PayloadParser**
(raw → `ParsedPayload`) + repository `mapper:` unlocks HTML+JSON-LD, later OAI+RDF (#142), and other pairs without new
plugin packages per combination — as long as `parser.produces == mapper.accepts`. #140 landed the shared mapper layer;
this change introduces the protocol/parser composition package.

Tracked as GitHub [#141](https://github.com/fairagro/m4.2_middleware_harvester/issues/141). Explore lock-in: **option C**
— new `middleware/generic` package beside `linked_data`, migrate sources incrementally, thin/deprecate `linked_data`
after parity.

## What Changes

- Add workspace package `middleware/generic` owning:
  - `Protocol` ABC + registry (discovery → `DiscoveryResult` stream; count hint)
  - `PayloadParser` ABC + registry (discovery result + HTTP → `ParsedPayload` with `PayloadKind`)
  - `GenericPlugin` `run()` / `get_expected_datasets()`: Protocol → Parser → kind-check → shared `DataMapper` → yield
    `HarvestedArc` / `HarvesterError` / `SkippedRecord`
  - Plugin `Config` with explicit `protocol_type` + `parser_type` (no auto-infer)
- Wire repository config plugin key `generic:` (mutual exclusion with `inspire` / `linked_data`); reuse top-level
  `mapper:` from #140; fail-fast when `parser.produces != mapper.accepts`
- **Incremental migration** from `linked_data`:
  1. First slice: XML sitemap protocol + `html_jsonld` parser (adapters wrapping or moving existing implementations)
  2. Later slices: `mycore_solr`, `regal_find` + `regal_jsonld` (same PR series or follow-ups)
  3. After parity: thin or deprecate `linked_data` plugin key (documented **BREAKING** for operators who still use it)
- OpenSpec: new generic capabilities; deltas on harvester configuration; coexistence notes for linked-data specs until
  migration completes
- Update `openspec/principles.md` module graph: `generic/` → `payload/`; plugins must not import each other

### Non-goals

- OAI-PMH / EPrints (#142)
- Moving INSPIRE/CSW into generic (#143 — not planned)
- New `PayloadKind` values beyond `rdf_graph` unless a migrated parser already needs one
- Big-bang delete of `linked_data` in the first implementation PR
- Auto-detecting protocol/parser/mapper from bytes or URL

## Capabilities

### New Capabilities

- `generic-harvesting`: Generic plugin entrypoint, config (`protocol_type`, `parser_type`), orchestration loop,
  kind-check against repository `mapper:`, yield contract parity with linked-data/INSPIRE.
- `harvest-protocol`: `Protocol` ABC, registry, discovery stream / expected-count contract (generalizes today’s
  `Sitemap` role without requiring the name “sitemap”).
- `payload-parser`: `PayloadParser` ABC, registry, `produces: PayloadKind`, parse path to `ParsedPayload` (generalizes
  today’s `Dataset` role beyond RDF-only `to_graph()`).

### Modified Capabilities

- `harvester-configuration`: Allow exactly one of `inspire` | `linked_data` | `generic` per repository; document
  `generic` + required `mapper:` for generic repositories.
- `linked-data-harvesting`: Coexistence — `linked_data` remains valid during migration; no requirement removal until a
  later deprecate change. Add a requirement that migrated repository configs MAY use `generic:` with equivalent
  protocol/parser pairs without changing harvest outcomes for the first migrated pair (xml + html_jsonld).

## Impact

- New package: `middleware/generic` (+ tests, workspace member, Docker/Bake metadata as for other plugins)
- `middleware/harvester` config / plugin factory
- `middleware/linked_data` remains until migration tasks complete; first slice may share types (`DiscoveryResult`) via
  a neutral home (prefer `middleware.generic` or thin re-export — design decides; avoid `payload` owning discovery)
- Operator YAML: optional switch to `generic:` for migrated sources; example/demo configs
- Specs under `openspec/specs/` as listed; principles module graph
- Follow-on: #142 can register an OAI protocol + RDF parser against this package without a third dedicated plugin
