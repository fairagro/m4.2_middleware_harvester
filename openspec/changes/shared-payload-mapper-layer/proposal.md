## Why

The same semantic payload (e.g. an RDF graph) can arrive via different harvest protocols (HTML+sitemap today;
OAI-PMH and others later). Vocabulary mappers still live under `middleware.linked_data.linked_data_mapper`, so other
protocol plugins cannot share them. A cross-cutting intermediate-payload + mapper layer keeps transport in plugins and
record→ARC mapping reusable.

Tracked as GitHub [#140](https://github.com/fairagro/m4.2_middleware_harvester/issues/140). Refreshed from draft
[PR #162](https://github.com/fairagro/m4.2_middleware_harvester/pull/162) (OpenSpec-only, superseded) after explore on
current `main` (StableGraph / Schema.org / Regal ResourceView already landed).

## What Changes

- Add workspace package `middleware/payload` owning `PayloadKind`, `ParsedPayload`, `DataMapper` registry, and the full
  RDF mapping stack currently under `linked_data/linked_data_mapper/` (`LinkedDataMapper`, `StableGraph`, Schema.org +
  Regal implementations) — **one change**, tasks staged (scaffold → contracts → move → config → wiring).
- v1 `PayloadKind` is **`rdf_graph` only** (`rdflib.Graph`).
- Repository config gains a top-level `mapper:` block beside the plugin key; fail-fast when producer kind ≠ mapper
  `accepts`. Canonical YAML uses `mapper.type`. Deprecated: `linked_data.payload_type` is still accepted, emits a
  `DeprecationWarning`, and is lifted to `mapper.type` (conflict with a differing `mapper.type` fails closed).
- `linked_data` keeps Sitemap/Dataset orchestration but **calls** shared mappers; mapper selection leaves the plugin
  config (except the deprecated alias).
- Preserve call-scoped `StableGraph` / `_*Run` concurrency contracts during the move.
- Update principles dependency graph / extension points for `middleware.payload`.

### Non-goals

- Generic Protocol + PayloadParser plugin (→ [#141](https://github.com/fairagro/m4.2_middleware_harvester/issues/141))
- OAI-PMH / EPrints mapper (→ [#142](https://github.com/fairagro/m4.2_middleware_harvester/issues/142))
- Moving INSPIRE mapper / `inspire_record` kind (→ [#143](https://github.com/fairagro/m4.2_middleware_harvester/issues/143))
- Renaming or removing the `linked_data` plugin
- Auto-detecting mapper from payload bytes
- Permanent dual vocabulary (`payload_type` remains transitional only)

## Capabilities

### New Capabilities

- `payload`: Shared intermediate-payload contracts (`PayloadKind`, `ParsedPayload`) and `DataMapper` /
  `LinkedDataMapper` registry + RDF implementations in `middleware.payload`.

### Modified Capabilities

- `harvester-configuration`: Repository entries that use shared mappers MUST accept `mapper` beside the plugin key;
  validate mapper↔kind compatibility; `mapper` is not a plugin field for the exactly-one-plugin rule; deprecated
  `linked_data.payload_type` MAY be lifted to `mapper.type` with a deprecation warning.
- `linked-data-harvesting`: Plugin MUST resolve mappers from repository `mapper.type` / shared registry; plugin config
  MUST NOT model `payload_type` as a first-class field (legacy values are lifted at repository validation).
- `linked-data-mapper`: Mapper ownership and import paths move to `middleware.payload`; behavioural ARC mapping rules
  (including StableGraph / ResourceView) unchanged.
- `principles`: Module dependency graph and extension points MUST include `middleware.payload`.

## Impact

- New uv workspace member `middleware/payload`; MYPYPATH / quality path overlays as needed.
- Code move: `linked_data/linked_data_mapper/*` → `middleware/payload`; tests and YAML examples updated.
- `middleware/harvester` `RepositoryConfig` + demo/example configs.
- Follow-ups #141–#143 remain separate.
