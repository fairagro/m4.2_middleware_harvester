# Design

## Context

See `proposal.md` for motivation. Explore lock-ins for
[#142](https://github.com/fairagro/m4.2_middleware_harvester/issues/142):

- Client: **oaipmh-scythe**; own plugin HTTP/retry config (only fields Scythe + preflight can honour) — not a mapped
  `NiceHttpClientConfig`.
- Form: dedicated **`oai_pmh` plugin** (INSPIRE-like ownership of the wire protocol), **new plugin principle**: no
  vocabulary mapper inside the plugin; shared `PayloadParser` + `DataMapper`.
- Baseline: [#339](https://github.com/fairagro/m4.2_middleware_harvester/issues/339) shipped `middleware.parsing`
  (`DiscoveryResult`, `PayloadParser` registry, sibling repository `parser:`) — this design consumes that layout.
- Deleted → `SkippedRecord`; `sets: list[str]`; `metadata_prefix` required and configurable; EPrints/aeprints mapper
  deferred.

Generic already composes Protocol → Parser → Mapper via shared registries. OAI does **not** register as `ProtocolType`;
Scythe’s `ListRecords` replaces that discovery stage inside the plugin, then uses the same shared parser + mapper path.

## Goals / Non-Goals

**Goals:**

- Ship a working `oai_pmh` plugin + shared inline RDF/XML parser + config/orchestrator wiring under the locked
  contracts.
- Preserve polite harvesting intent (UA, timeout, retries, optional robots + rate limit) within Scythe’s constraints.
- Keep mapper/parser registries plugin-agnostic in `middleware.payload` / `middleware.parsing`.

**Non-Goals:**

- Re-implementing #339 in this change.
- EPrints/`eprints_general` mapper or production aeprints Helm/YAML as acceptance of this PR.
- Middleware API delete/tombstone.
- `oai_dc` or other non-RDF metadata handlers (extension point only).
- Async-native OAI client (Scythe is sync; use `asyncio.to_thread` like OWSLib).

## Decisions

### 1. Dedicated plugin package `middleware/oai_pmh`, not Generic `ProtocolType`

**Choice:** New workspace package + repository key `oai_pmh`.

**Why:** OAI owns pagination, sets, deleted headers, and prefix negotiation; forcing it into Generic’s URL-oriented
Protocol registry obscures the model and fights Scythe’s sync httpx2 client vs NiceHttp.

**Alternatives:** Generic `oai_pmh` Protocol — rejected in explore.

### 2. oaipmh-scythe for verbs/pagination; map policies into `HTTPConfig` / `RetryConfig`

**Choice:** Depend on `oaipmh-scythe`; construct `HTTPConfig(user_agent=…, timeout=…)` and
`RetryConfig(max_retries=…, retry_status_codes=…, …)` from the plugin’s own Pydantic config fields.

**Why:** Correct resumption-token exclusivity, OAI error types, deleted flags without reimplementing the protocol.

**Alternatives:** DIY NiceHttp ListRecords — more control, more Spec risk; Sickle — unmaintained.

### 3. Own config model (supported fields only); parser via sibling `parser:`

**Plugin fields (indicative):** `endpoint_url`, `metadata_prefix`, `sets: list[str] = []`, `user_agent`, `timeout`,
retry block (`max_retries`, `retry_status_codes`, `default_retry_after`, `retry_on_transport_error`, `initial_backoff`),
optional `respect_robots_txt`, optional `max_requests_per_second`.

**Repository siblings (required for `oai_pmh`, same as `generic`):** `parser: { type: … }` and `mapper: { type: … }`.
The plugin `Config` MUST NOT carry `parser_type`.

**Why:** Matches post-#339 hard-cut; Scythe policies stay on the plugin; registries stay beside the plugin key. Do not
subtype/map `NiceHttpClientConfig`. Robots/rate-limit are preflight/wrapper around Scythe, not fake Scythe features.

### 4. Discovery unit = inline metadata + OAI identifier in `middleware.parsing`

**Choice:** Add a parsing-owned discovery subclass (e.g. XML/string inline payload + `identifier`) beside
`UrlDiscoveryResult` / `JsonLdDiscoveryResult`. OAI emits that unit from ListRecords; the RDF/XML parser consumes it and
MUST NOT fetch.

**Why:** Same pattern as Regal inline JSON-LD; RDF/XML parser stays reusable across plugins.

### 5. Shared parser type key `rdf_xml` in `middleware.parsing`

**Choice:** Register inline RDF/XML parser under `ParserType.rdf_xml` / `parser.type: rdf_xml` in `middleware.parsing`;
OAI sets `metadata_prefix` independently (e.g. `rdf`). Raise `ParserError` on unusable metadata; plugin harvest loop
catches it as record-level failure (same pattern as `GenericPlugin` + `ParserError`).

**Why:** Prefix names vary by repo; keep wire prefix and parse handler separate; share error base with other parsers.

### 6. Sets as sequential ListRecords passes

**Choice:** Empty `sets` → one unfiltered harvest; non-empty → one pass per `setSpec` in list order.

**Why:** Matches OAI’s single-`set` argument per request; avoids inventing multi-set protocol behaviour.

### 7. Sync Scythe behind `asyncio.to_thread` (+ optional host throttle)

**Choice:** Run Scythe iteration/blocking HTTP off the event loop; apply rate-limit sleeps in the wrapper.

**Why:** Aligns with CSW/OWSLib pattern (`async-concurrency`); Scythe has no async API.

### 8. Mapper out of scope; kind alignment still enforced

**Choice:** Tests/fixtures prove parse → `rdf_graph`; full ARC path tested with a registered `rdf_graph` mapper when
available, or stop at ParsedPayload / kind-check in unit tests. No EPrints mapper in this PR. Startup validates
`parser.produces` vs `mapper.accepts` via repository `parser` + `mapper` blocks.

**Why:** Explore deferred aeprints mapper to a follow-up.

### 9. Orchestrator wiring mirrors `generic`

**Choice:** `PLUGIN_FACTORIES["oai_pmh"]` constructs the plugin with `(plugin_config, mapper_config, parser_config)`.
`RepositoryConfig` requires `mapper` and `parser` when `oai_pmh` is set; `_NON_PLUGIN_FIELDS` already excludes both.

**Why:** One pattern for every shared-parser plugin.

## Risks / Trade-offs

| Risk                                           | Mitigation                                                                                                                             |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Scythe httpx2 ≠ NiceHttp / project httpx       | Document; map UA/timeout/retry; robots + RPS outside Scythe                                                                            |
| XML hardening weaker than CSW (`recover=True`) | Prefer parsing metadata with project-hardened RDF/XML path in the shared parser where possible; limit trust in Scythe’s envelope parse |
| No EPrints mapper → incomplete end-to-end demo | Explicit non-goal; follow-up issue/PR                                                                                                  |
| #339 not on integration base                   | Apply blocked until `middleware.parsing` + sibling `parser:` available on the merge base                                               |
| Large repos / many sets                        | Sequential sets; pagination via Scythe; expected count often `None`                                                                    |

## Migration Plan

1. Land #339 (shared parsers) — done on the OAI working branch via merge.
2. Land this change: package + parsing discovery/parser + config + tests.
3. Follow-up: EPrints mapper + aeprints example config; Middleware API delete issue for tombstones.
4. Rollback: remove `oai_pmh` repos from config; no data migration.

## Open Questions

- Exact name of the inline XML discovery dataclass (`XmlDiscoveryResult` vs `RdfXmlDiscoveryResult`) — pick one at apply
  time; keep it in `middleware.parsing.discovery`.
- Whether `get_expected_datasets` should call `Identify` / use `completeListSize` when present — prefer `None` unless
  cheap and reliable in implementation.
