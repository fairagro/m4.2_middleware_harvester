# Regal JSON-LD Harvesting

Extend the linked_data plugin with Regal (hbz) discovery, payload, and mapping
strategies so repositories such as PUBLISSO FRL can be harvested without a
separate plugin. Discovery uses the Regal `/find` JSON API; each record is
native Regal JSON-LD (not schema.org); mapping produces ARC RO-Crate JSON-LD.

Record-level outcomes must surface through the plugin yield contract so the
orchestrator can update harvest-report statistics and the failure list
([`harvest-report`](../../../harvester/spec/harvest-report/),
[`error-handling`](../../../../spec/error-handling/),
[`skipped-datasets`](../../../../spec/skipped-datasets/)). Local logging alone
is not sufficient for operator-visible discovery or mapping problems.

## Requirements

### Discovery (`Sitemap`)

- [x] Support a dedicated Regal sitemap type in plugin configuration.
- [x] Accept a Regal `/find` endpoint in `sitemap_url`; query parameters are optional.
- [x] When `sitemap_url` omits overridable params, fill defaults: `q=contentType:researchData` and `until` from config `page_size`.
- [x] When `sitemap_url` already contains an overridable query parameter (`q`, extra filters, …), keep the operator-supplied value.
- [x] Always set `format=json` and pagination `from` in software; ignore those keys on `sitemap_url`.
- [x] When `sitemap_url` contains `until`, use it as the page size (overrides config `page_size`); otherwise use config `page_size` (default 200).
- [x] Use optional `resource_base_url` to expand compact Regal `@id` values to absolute IRIs; when unset, derive `{scheme}://{host}/resource/` from `sitemap_url`.
- [x] Issue HTTP GET requests to the constructed `/find` URL.
- [x] Parse the response as a JSON array of Regal JSON-LD records.
- [x] Yield one discovery result per record that carries the record's JSON-LD payload inline (no follow-up HTML fetch).
- [x] Use each record's `@id` as the stable discovery identity for deduplication and error reporting.
- [x] Deduplicate discovered records by `@id` within a single harvest run.
- [x] Paginate by advancing the `from` query parameter by the number of records returned until a page is empty or shorter than the requested page size.
- [x] Expose `get_expected_count()` as unknown (`None`) when the `/find` response does not provide a total hit count.
- [x] Raise `httpx.HTTPStatusError` on non-2xx HTTP responses (do not swallow).
- [x] Raise `LinkedDataSitemapError` when the response body is not a JSON array (fatal discovery failure; not a per-record yield).
- [x] Do not silently drop malformed or unusable `/find` array entries; yield `RecordProcessingError` (shared harvester type, same as inspire CSW) so the orchestrator can update the harvest report.
- [x] Treat a record object missing `@id` as a record-level failure (not a deliberate skip): yield `RecordProcessingError` so `failed_datasets` increments and `fairagro:failedRecords` gains an entry.
- [x] Treat a non-object JSON array element as a record-level failure: yield `RecordProcessingError` the same way (message must identify page offset / array index when no `@id` exists).

### Dataset payload

- [x] Support a dedicated Regal dataset type in plugin configuration.
- [x] Construct the dataset from an inline Regal JSON-LD discovery result without requiring an HTTP client.
- [x] Parse the inline JSON-LD into an `rdflib.Graph` via rdflib's JSON-LD parser.
- [x] Use the record `@id` as the stable dataset identifier (DOI is a publication attribute, not the discovery identity).
- [x] Raise a dataset error when the discovery result type is unsupported.
- [x] Raise a dataset error when the payload is not valid JSON-LD for rdflib.

### Mapping (`payload_type`)

- [x] Support a dedicated Regal payload type that selects a Regal→ARC mapper.
- [x] Map Regal `ResearchData` graphs to serialized ARC RO-Crate JSON-LD as defined in [`docs/regal_mapping.md`](../../../../docs/regal_mapping.md) and [`regal-to-arc-mapping`](../regal-to-arc-mapping/spec.md).
- [x] Keep Regal mapping logic separate from schema.org mapping implementations (`GeneralSchemaOrgMapper`).
- [x] Yield a mapping error (as `HarvesterError`) when the graph lacks mappable ResearchData metadata; do not crash the plugin.

### Plugin / report integration

- [x] Yield `SkippedRecord` for duplicate discovery identifiers (counts toward `skipped_datasets`, not failures).
- [x] Yield `RecordProcessingError` for unusable discovery entries (same shared type as inspire); the plugin forwards them to the orchestrator without a plugin-local failure wrapper type.
- [x] Prefer a stable `@id` as `record_id` when known; otherwise use a synthetic discovery key so the failure still appears in `fairagro:failedRecords`.

## Edge Cases

- Empty JSON array on the first page → yield zero discovery results and exit cleanly.
- Record missing `@id` → yield `RecordProcessingError` (DOI alone is not accepted as identity); orchestrator increments `failed_datasets` and appends `fairagro:failedRecords`; discovery continues.
- Non-object JSON array element → same `RecordProcessingError` path as missing `@id` (include index in the message); discovery continues.
- `@id` already yielded in this run → `SkippedRecord` → `skipped_datasets`; do not count as a failure.
- Last page shorter than the requested page size → stop pagination; do not request a further empty page.
- Inline payload present but JSON-LD context unresolved / parse failure → emit a dataset or mapping error for that record (`HarvesterError`) and continue.
- Configured Regal dataset type receiving a URL-only discovery result → raise a descriptive dataset construction error (plugin yields `HarvesterError`).
- Non-`ResearchData` Regal types in the result set → map-error that record (`HarvesterError`); do not abort the run.
- Operator `format=xml` (or any other `format`) on `sitemap_url` → ignored; request still uses `format=json`.
- Operator `q=…` on `sitemap_url` → overrides default `contentType:researchData`.
- Operator `until=N` on `sitemap_url` → overrides config `page_size` for pagination.
- Fatal `/find` transport or response-shape failure (non-array body, HTTP error) → raise (full plugin failure), not yield.
