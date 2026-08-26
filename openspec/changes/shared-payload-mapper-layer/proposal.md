## Why

The same semantic payload (e.g. an RDF graph) can arrive via different harvest protocols (HTML+sitemap today; OAI-PMH and others later). Mappers currently live inside `linked_data`, so protocol plugins cannot share them. We need a cross-cutting intermediate-payload + mapper layer so transport stays in plugins while record→ARC mapping is reusable.

Tracked as GitHub [#140](https://github.com/fairagro/m4.2_middleware_harvester/issues/140).

## What Changes

- Add workspace package `middleware/payload` owning `PayloadKind`, `ParsedPayload`, `DataMapper` registry, and RDF refinement `LinkedDataMapper` (Schema.org + Regal implementations move here).
- v1 `PayloadKind` is **`rdf_graph` only** (`rdflib.Graph`).
- Repository config gains a top-level `mapper:` block beside the plugin config; fail-fast when producer kind ≠ mapper `accepts`.
- `linked_data` keeps Sitemap/Dataset orchestration but **calls** shared mappers instead of owning them; `payload_type` selection moves to (or is mirrored by) repository `mapper.type`.
- Update principles dependency graph / extension points for the shared package.

### Non-goals

- Generic Protocol + PayloadParser plugin (→ [#141](https://github.com/fairagro/m4.2_middleware_harvester/issues/141))
- OAI-PMH / EPrints mapper (→ [#142](https://github.com/fairagro/m4.2_middleware_harvester/issues/142))
- Moving INSPIRE mapper / `inspire_record` kind (→ [#143](https://github.com/fairagro/m4.2_middleware_harvester/issues/143))
- Renaming or removing the `linked_data` plugin in this change
- Auto-detecting mapper from payload bytes

## Capabilities

### New Capabilities

- `payload`: Shared intermediate-payload contracts (`PayloadKind`, `ParsedPayload`) and `DataMapper` / `LinkedDataMapper` registry in `middleware.payload`.

### Modified Capabilities

- `harvester-configuration`: Repository entries MUST accept a `mapper` config beside the plugin key; validate mapper↔kind compatibility.
- `linked-data-harvesting`: Plugin MUST resolve mappers from the shared payload package / repository mapper config.
- `linked-data-mapper`: Mapper ownership and import paths move to `middleware.payload`; behavioural mapping rules unchanged.
- `principles`: Module dependency graph and extension points MUST include `middleware.payload` as the shared mapping home.

## Impact

- New uv workspace member `middleware/payload`.
- Code moves: `linked_data/linked_data_mapper/*` → `middleware/payload` (with stable re-exports or import updates in tests).
- `middleware/harvester` config (`RepositoryConfig`) and example YAML configs.
- OpenSpec: new `payload` domain; deltas for configuration, harvesting, mapper, principles.
- Follow-ups #141–#143 remain separate changes.
