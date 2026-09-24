# Proposal

## Why

Operators need to harvest OAI-PMH endpoints that expose RDF/XML (and later other metadata formats) into ARC via shared
mappers. Issue [#142](https://github.com/fairagro/m4.2_middleware_harvester/issues/142) tracks this. OAI-PMH is a full
record protocol (verbs, resumption tokens, sets, deleted headers) with metadata **inline** in `ListRecords` responses —
it fits a dedicated plugin (like INSPIRE’s ownership of CSW), composed with **shared** `PayloadParser` + `DataMapper`
(post-[#339](https://github.com/fairagro/m4.2_middleware_harvester/issues/339)), not a Generic `Protocol` registry
entry.

## What Changes

- Add workspace package `middleware/oai_pmh` (plugin key `oai_pmh`): harvest loop using **oaipmh-scythe**, own
  HTTP/retry config (fields Scythe supports + optional robots/rate preflight), `AsyncGenerator` plugin contract.
- Config: OAI endpoint URL, configurable `metadata_prefix`, optional `sets: list[str]` (one `ListRecords` pass per set,
  or a single unfiltered pass when empty), `parser_type` selecting a shared parser, repository-level `mapper:`.
- Deleted OAI records (`header/@status="deleted"`) → `SkippedRecord` (API tombstone/delete is out of scope; separate
  Middleware API follow-up).
- Register shared inline **RDF/XML** `PayloadParser` (assumes #339 already moved parsers into the shared layer) that
  turns OAI `<metadata>` RDF/XML into `ParsedPayload(kind=rdf_graph)`.
- Wire orchestrator / repository config / import-linter / principles for the new plugin.
- Dependency: `oaipmh-scythe` (and its httpx2 stack) for the OAI plugin only.
- Tests with OAI/RDF fixtures; OpenSpec domains below.

## Capabilities

### New Capabilities

- `oai-pmh-harvesting`: Dedicated OAI-PMH plugin — Scythe client, pagination, sets, deleted→skip, config, composition
  with shared parser + mapper.
- `rdf-xml-parser`: Shared inline RDF/XML `PayloadParser` producing `rdf_graph` (usable by OAI and later other
  producers).

### Modified Capabilities

- `harvester-configuration`: Allow `oai_pmh` plugin key; require `mapper` + `parser_type` alignment like other shared-
  mapper plugins; document OAI-specific fields.
- `harvester-orchestration`: Dispatch `oai_pmh` via plugin registry.
- `payload-parser`: Parsers are shared (baseline #339); OAI plugin MUST align `parser.produces` with `mapper.accepts`
  the same way generic does; HTTP-optional parsers for inline discovery.
- `skipped-datasets`: OAI deleted records yield `SkippedRecord`.
- `principles`: Module graph — `oai_pmh` plugin may import harvester + shared payload/parsers; MUST NOT own vocabulary
  mappers; MUST NOT import other protocol plugins.

## Impact

- New package under `middleware/oai_pmh`; root workspace / Docker / quality path overlays.
- `middleware.harvester` repository config + `PLUGIN_FACTORIES`.
- Shared parser registry (post-#339 location) gains `rdf_xml` (name TBD in design).
- No EPrints/aeprints vocabulary mapper in this change (follow-up PR); operators need a compatible `mapper.type` that
  accepts `rdf_graph` once such a mapper exists, or tests stop at parse/kind-check with fixtures.
- Does **not** implement Middleware API delete/tombstone; does **not** depend on implementing #339 in this PR (assumed
  already on `main`).

## Non-goals

- Phenoroam / non-RDF OAI formats; DCAT-AP.
- EPrints/BIBO/DC `DataMapper` and aeprints as a production RDI config in this PR.
- Promoting OAI to a Generic `ProtocolType`.
- Mapping from `NiceHttpClientConfig` into Scythe (own comparable config fields only).
- API-side dataset deletion.
