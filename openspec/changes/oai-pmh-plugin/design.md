# Design

## Context

See `proposal.md` for motivation. Explore lock-ins for
[#142](https://github.com/fairagro/m4.2_middleware_harvester/issues/142):

- Client: **oaipmh-scythe**; own plugin HTTP/retry config (only fields Scythe + preflight can honour) — not a mapped
  `NiceHttpClientConfig`.
- Form: dedicated **`oai_pmh` plugin** (INSPIRE-like ownership of the wire protocol), **new plugin principle**: no
  vocabulary mapper inside the plugin; shared `PayloadParser` + `DataMapper`.
- Baseline assumption: [#339](https://github.com/fairagro/m4.2_middleware_harvester/issues/339) already moved
  `PayloadParser` / `DiscoveryResult` into the shared layer; this design consumes that layout.
- Deleted → `SkippedRecord`; `sets: list[str]`; `metadata_prefix` required and configurable; EPrints/aeprints mapper
  deferred.

Generic already composes Protocol → Parser → Mapper. OAI does **not** register as `ProtocolType`; Scythe’s `ListRecords`
replaces that discovery stage inside the plugin.

## Goals / Non-Goals

**Goals:**

- Ship a working `oai_pmh` plugin + shared inline RDF/XML parser + config/orchestrator wiring under the locked
  contracts.
- Preserve polite harvesting intent (UA, timeout, retries, optional robots + rate limit) within Scythe’s constraints.
- Keep mapper/parser registries plugin-agnostic.

**Non-Goals:**

- Implementing #339 in this change.
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

### 3. Own config model (supported fields only)

**Fields (indicative):** `endpoint_url`, `metadata_prefix`, `sets: list[str] = []`, `parser_type`, `user_agent`,
`timeout`, retry block (`max_retries`, `retry_status_codes`, `default_retry_after`, `retry_on_transport_error`,
`initial_backoff`), optional `respect_robots_txt`, optional `max_requests_per_second`.

**Why:** User lock-in — do not subtype/map `NiceHttpClientConfig`. Robots/rate-limit are preflight/wrapper around
Scythe, not fake Scythe features.

### 4. Discovery unit = inline metadata + OAI identifier

**Choice:** Emit a shared discovery type (post-#339) carrying OAI identifier + raw `<metadata>` XML (bytes/str). Parser
does not fetch.

**Why:** Same pattern as Regal inline JSON-LD; RDF/XML parser stays reusable.

### 5. Shared parser type key `rdf_xml` (name)

**Choice:** Register inline RDF/XML parser under `rdf_xml` in the shared parser registry; OAI config sets
`parser_type: rdf_xml` with `metadata_prefix` independently (e.g. `rdf`).

**Why:** Prefix names vary by repo; keep wire prefix and parse handler separate.

### 6. Sets as sequential ListRecords passes

**Choice:** Empty `sets` → one unfiltered harvest; non-empty → one pass per `setSpec` in list order.

**Why:** Matches OAI’s single-`set` argument per request; avoids inventing multi-set protocol behaviour.

### 7. Sync Scythe behind `asyncio.to_thread` (+ optional host throttle)

**Choice:** Run Scythe iteration/blocking HTTP off the event loop; apply rate-limit sleeps in the wrapper.

**Why:** Aligns with CSW/OWSLib pattern (`async-concurrency`); Scythe has no async API.

### 8. Mapper out of scope; kind alignment still enforced

**Choice:** Tests/fixtures prove parse → `rdf_graph`; full ARC path tested with a registered `rdf_graph` mapper when
available, or stop at ParsedPayload / kind-check in unit tests. No EPrints mapper in this PR.

**Why:** Explore deferred aeprints mapper to a follow-up.

## Risks / Trade-offs

| Risk                                           | Mitigation                                                                                                                             |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Scythe httpx2 ≠ NiceHttp / project httpx       | Document; map UA/timeout/retry; robots + RPS outside Scythe                                                                            |
| XML hardening weaker than CSW (`recover=True`) | Prefer parsing metadata with project-hardened RDF/XML path in the shared parser where possible; limit trust in Scythe’s envelope parse |
| No EPrints mapper → incomplete end-to-end demo | Explicit non-goal; follow-up issue/PR                                                                                                  |
| #339 not actually merged when apply starts     | Apply blocked until #339 on `main`; this change assumes it                                                                             |
| Large repos / many sets                        | Sequential sets; pagination via Scythe; expected count often `None`                                                                    |

## Migration Plan

1. Land #339 (shared parsers).
2. Land this change: package + parser + config + tests.
3. Follow-up: EPrints mapper + aeprints example config; Middleware API delete issue for tombstones.
4. Rollback: remove `oai_pmh` repos from config; no data migration.

## Open Questions

- Exact shared-package module path for parsers after #339 (`middleware.payload.parser` vs sibling) — follow whatever
  #339 ships; tasks reference “shared parser registry” not a frozen path.
- Whether `get_expected_datasets` should call `Identify` / use `completeListSize` when present — prefer `None` unless
  cheap and reliable in implementation.
