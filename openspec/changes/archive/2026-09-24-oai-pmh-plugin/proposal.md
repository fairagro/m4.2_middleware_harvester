# Proposal

## Why

Operators need to harvest OAI-PMH endpoints that expose RDF/XML (and later other metadata formats) into ARC via shared
mappers. Issue [#142](https://github.com/fairagro/m4.2_middleware_harvester/issues/142) tracks this. OAI-PMH is a full
record protocol (verbs, resumption tokens, sets, deleted headers) with metadata **inline** in `ListRecords` responses —
it fits a dedicated plugin (like INSPIRE’s ownership of CSW), composed with **shared** `PayloadParser` + `DataMapper`
from `middleware.parsing` / `middleware.payload` (landed via
[#339](https://github.com/fairagro/m4.2_middleware_harvester/issues/339)), not a Generic `Protocol` registry entry.

## What Changes

- Add workspace package `middleware/oai_pmh` (plugin key `oai_pmh`): harvest loop using **oaipmh-scythe**, own
  HTTP/retry config (fields Scythe supports + optional robots/rate preflight), `AsyncGenerator` plugin contract.
- Config: OAI endpoint URL, configurable `metadata_prefix`, optional `sets: list[str]` (one `ListRecords` pass per set,
  or a single unfiltered pass when empty). Shared parser selection uses repository sibling `parser:` (not a field on the
  plugin config); shared mapper uses sibling `mapper:` — same pattern as `generic`.
- Deleted OAI records (`header/@status="deleted"`) → `SkippedRecord` (API tombstone/delete is out of scope; separate
  Middleware API follow-up).
- Register shared inline **RDF/XML** `PayloadParser` in `middleware.parsing` (`parser.type: rdf_xml`) that turns OAI
  `<metadata>` RDF/XML into `ParsedPayload(kind=rdf_graph)`, consuming a parsing-owned inline discovery unit (XML
  string/bytes + stable OAI identifier).
- Wire orchestrator / repository config / import-linter / principles for the new plugin (pass `mapper` + `parser` into
  the plugin like `GenericPlugin`).
- Dependency: `oaipmh-scythe` (and its httpx2 stack) for the OAI plugin only.
- Tests with OAI/RDF fixtures; OpenSpec domains below.

## Capabilities

### New Capabilities

- `oai-pmh-harvesting`: Dedicated OAI-PMH plugin — Scythe client, pagination, sets, deleted→skip, config, composition
  with shared parser + mapper.
- `rdf-xml-parser`: Shared inline RDF/XML `PayloadParser` producing `rdf_graph` (usable by OAI and later other
  producers).

### Modified Capabilities

- `harvester-configuration`: Allow `oai_pmh` plugin key; require sibling `mapper` + `parser` and kind alignment like
  `generic`; document OAI-specific plugin fields (no `parser_type` on the plugin config).
- `harvester-orchestration`: Dispatch `oai_pmh` via plugin registry with mapper + parser config.
- `payload-parser`: OAI plugin MUST align `parser.produces` with `mapper.accepts` the same way `generic` does;
  HTTP-optional parsers for inline discovery.
- `skipped-datasets`: OAI deleted records yield `SkippedRecord`.
- `principles`: Module graph — `oai_pmh` may import harvester + `middleware.payload` + `middleware.parsing`; MUST NOT
  own vocabulary mappers; MUST NOT import other protocol plugins.

## Impact

- New package under `middleware/oai_pmh`; root workspace / Docker / quality path overlays.
- `middleware.harvester` repository config + `PLUGIN_FACTORIES` (three-arg factory like `generic`).
- `middleware.parsing` gains `rdf_xml` parser + an inline XML/RDF discovery-unit type beside existing URL / JSON-LD
  units.
- No EPrints/aeprints vocabulary mapper in this change (follow-up PR); operators need a compatible `mapper.type` that
  accepts `rdf_graph` once such a mapper exists, or tests stop at parse/kind-check with fixtures.
- Does **not** implement Middleware API delete/tombstone; assumes #339 (`middleware.parsing` + sibling `parser:`) is
  already on the integration base.

## Non-goals

- Phenoroam / non-RDF OAI formats; DCAT-AP.
- EPrints/BIBO/DC `DataMapper` and aeprints as a production RDI config in this PR.
- Promoting OAI to a Generic `ProtocolType`.
- Mapping from `NiceHttpClientConfig` into Scythe (own comparable config fields only).
- API-side dataset deletion.
