# Regal JSON-LD Harvesting

## Purpose

Extend the linked_data plugin with Regal (hbz) discovery, payload, and mapping
strategies so repositories such as PUBLISSO FRL can be harvested without a
separate plugin. Discovery uses the Regal `/find` JSON API; each record is
native Regal JSON-LD (not schema.org); mapping produces ARC RO-Crate JSON-LD.

Record-level outcomes must surface through the plugin yield contract so the
orchestrator can update harvest-report statistics and the failure list
([`harvest-report`](../harvest-report/),
[`error-handling`](../error-handling/),
[`skipped-datasets`](../skipped-datasets/)). Local logging alone
is not sufficient for operator-visible discovery or mapping problems.

## Requirements

### Requirement: Support a dedicated Regal sitemap type in plugin configuration
The system SHALL support a dedicated Regal sitemap type in plugin configuration.

#### Scenario: Satisfies — Support a dedicated Regal sitemap type in plugin configuration
- **WHEN** the conditions described by this requirement apply
- **THEN** Support a dedicated Regal sitemap type in plugin configuration

### Requirement: Accept a Regal /find endpoint in sitemap_url; query parameters are…
The system SHALL accept a Regal `/find` endpoint in `sitemap_url`; query parameters are optional.

#### Scenario: Satisfies — Accept a Regal /find endpoint in sitemap_url; query parameters are…
- **WHEN** the conditions described by this requirement apply
- **THEN** Accept a Regal `/find` endpoint in `sitemap_url`; query parameters are optional

### Requirement: When sitemap_url omits overridable params, fill defaults: q=contentType:researchData and until…
The system SHALL ensure that when `sitemap_url` omits overridable params, fill defaults: `q=contentType:researchData` and `until` from config `page_size`.

#### Scenario: Satisfies — When sitemap_url omits overridable params, fill defaults: q=contentType:researchData and until…
- **WHEN** the conditions described by this requirement apply
- **THEN** When `sitemap_url` omits overridable params, fill defaults: `q=contentType:researchData` and `until` from config `page_size`

### Requirement: When sitemap_url already contains an overridable query parameter (q, extra…
The system SHALL ensure that when `sitemap_url` already contains an overridable query parameter (`q`, extra filters, …), keep the operator-supplied value.

#### Scenario: Satisfies — When sitemap_url already contains an overridable query parameter (q, extra…
- **WHEN** the conditions described by this requirement apply
- **THEN** When `sitemap_url` already contains an overridable query parameter (`q`, extra filters, …), keep the operator-supplied value

### Requirement: Always set format=json and pagination from in software; ignore those…
The system SHALL always set `format=json` and pagination `from` in software; ignore those keys on `sitemap_url`.

#### Scenario: Satisfies — Always set format=json and pagination from in software; ignore those…
- **WHEN** the conditions described by this requirement apply
- **THEN** Always set `format=json` and pagination `from` in software; ignore those keys on `sitemap_url`

### Requirement: When sitemap_url contains until, use it as the page size…
The system SHALL ensure that when `sitemap_url` contains `until`, use it as the page size (overrides config `page_size`); otherwise use config `page_size` (default 200).

#### Scenario: Satisfies — When sitemap_url contains until, use it as the page size…
- **WHEN** the conditions described by this requirement apply
- **THEN** When `sitemap_url` contains `until`, use it as the page size (overrides config `page_size`); otherwise use config `page_size` (default 200)

### Requirement: Use optional resource_base_url to expand compact Regal @id values to…
The system SHALL use optional `resource_base_url` to expand compact Regal `@id` values to absolute IRIs; when unset, derive `{scheme}://{host}/resource/` from `sitemap_url`.

#### Scenario: Satisfies — Use optional resource_base_url to expand compact Regal @id values to…
- **WHEN** the conditions described by this requirement apply
- **THEN** Use optional `resource_base_url` to expand compact Regal `@id` values to absolute IRIs; when unset, derive `{scheme}://{host}/resource/` from `sitemap_url`

### Requirement: Issue HTTP GET requests to the constructed /find URL
The system SHALL issue HTTP GET requests to the constructed `/find` URL.

#### Scenario: Satisfies — Issue HTTP GET requests to the constructed /find URL
- **WHEN** the conditions described by this requirement apply
- **THEN** Issue HTTP GET requests to the constructed `/find` URL

### Requirement: Parse the response as a JSON array of Regal JSON-LD…
The system SHALL parse the response as a JSON array of Regal JSON-LD records.

#### Scenario: Satisfies — Parse the response as a JSON array of Regal JSON-LD…
- **WHEN** the conditions described by this requirement apply
- **THEN** Parse the response as a JSON array of Regal JSON-LD records

### Requirement: Yield one discovery result per record that carries the record's…
The system SHALL yield one discovery result per record that carries the record's JSON-LD payload inline (no follow-up HTML fetch).

#### Scenario: Satisfies — Yield one discovery result per record that carries the record's…
- **WHEN** the conditions described by this requirement apply
- **THEN** Yield one discovery result per record that carries the record's JSON-LD payload inline (no follow-up HTML fetch)

### Requirement: Use each record's @id as the stable discovery identity for…
The system SHALL use each record's `@id` as the stable discovery identity for deduplication and error reporting.

#### Scenario: Satisfies — Use each record's @id as the stable discovery identity for…
- **WHEN** the conditions described by this requirement apply
- **THEN** Use each record's `@id` as the stable discovery identity for deduplication and error reporting

### Requirement: Deduplicate discovered records by @id within a single harvest run
The system SHALL deduplicate discovered records by `@id` within a single harvest run.

#### Scenario: Satisfies — Deduplicate discovered records by @id within a single harvest run
- **WHEN** the conditions described by this requirement apply
- **THEN** Deduplicate discovered records by `@id` within a single harvest run

### Requirement: Paginate by advancing the from query parameter by the number…
The system SHALL paginate by advancing the `from` query parameter by the number of records returned until a page is empty or shorter than the requested page size.

#### Scenario: Satisfies — Paginate by advancing the from query parameter by the number…
- **WHEN** the conditions described by this requirement apply
- **THEN** Paginate by advancing the `from` query parameter by the number of records returned until a page is empty or shorter than the requested page size

### Requirement: Expose get_expected_count() as unknown (None) when the /find response does…
The system SHALL expose `get_expected_count()` as unknown (`None`) when the `/find` response does not provide a total hit count.

#### Scenario: Satisfies — Expose get_expected_count() as unknown (None) when the /find response does…
- **WHEN** the conditions described by this requirement apply
- **THEN** Expose `get_expected_count()` as unknown (`None`) when the `/find` response does not provide a total hit count

### Requirement: Raise httpx.HTTPStatusError on non-2xx HTTP responses (do not swallow)
The system SHALL raise `httpx.HTTPStatusError` on non-2xx HTTP responses (do not swallow).

#### Scenario: Satisfies — Raise httpx.HTTPStatusError on non-2xx HTTP responses (do not swallow)
- **WHEN** the conditions described by this requirement apply
- **THEN** Raise `httpx.HTTPStatusError` on non-2xx HTTP responses (do not swallow)

### Requirement: Raise LinkedDataSitemapError when the response body is not a JSON…
The system SHALL raise `LinkedDataSitemapError` when the response body is not a JSON array (fatal discovery failure; not a per-record yield).

#### Scenario: Satisfies — Raise LinkedDataSitemapError when the response body is not a JSON…
- **WHEN** the conditions described by this requirement apply
- **THEN** Raise `LinkedDataSitemapError` when the response body is not a JSON array (fatal discovery failure; not a per-record yield)

### Requirement: Do not silently drop malformed or unusable /find array entries;…
The system SHALL do not silently drop malformed or unusable `/find` array entries; yield `RecordProcessingError` (shared harvester type, same as inspire CSW) so the orchestrator can update the harvest report.

#### Scenario: Satisfies — Do not silently drop malformed or unusable /find array entries;…
- **WHEN** the conditions described by this requirement apply
- **THEN** Do not silently drop malformed or unusable `/find` array entries; yield `RecordProcessingError` (shared harvester type, same as inspire CSW) so the orchestrator can update the harvest report

### Requirement: Treat a record object missing @id as a record-level failure…
The system SHALL treat a record object missing `@id` as a record-level failure (not a deliberate skip): yield `RecordProcessingError` so `failed_datasets` increments and `fairagro:failures` gains an entry.

#### Scenario: Satisfies — Treat a record object missing @id as a record-level failure…
- **WHEN** the conditions described by this requirement apply
- **THEN** Treat a record object missing `@id` as a record-level failure (not a deliberate skip): yield `RecordProcessingError` so `failed_datasets` increments and `fairagro:failures` gains an entry

### Requirement: Treat a non-object JSON array element as a record-level failure:…
The system SHALL treat a non-object JSON array element as a record-level failure: yield `RecordProcessingError` the same way (message must identify page offset / array index when no `@id` exists).

#### Scenario: Satisfies — Treat a non-object JSON array element as a record-level failure:…
- **WHEN** the conditions described by this requirement apply
- **THEN** Treat a non-object JSON array element as a record-level failure: yield `RecordProcessingError` the same way (message must identify page offset / array index when no `@id` exists)

### Requirement: Support a dedicated Regal dataset type in plugin configuration
The system SHALL support a dedicated Regal dataset type in plugin configuration.

#### Scenario: Satisfies — Support a dedicated Regal dataset type in plugin configuration
- **WHEN** the conditions described by this requirement apply
- **THEN** Support a dedicated Regal dataset type in plugin configuration

### Requirement: Construct the dataset from an inline Regal JSON-LD discovery result…
The system SHALL construct the dataset from an inline Regal JSON-LD discovery result without requiring an HTTP client.

#### Scenario: Satisfies — Construct the dataset from an inline Regal JSON-LD discovery result…
- **WHEN** the conditions described by this requirement apply
- **THEN** Construct the dataset from an inline Regal JSON-LD discovery result without requiring an HTTP client

### Requirement: Parse the inline JSON-LD into an rdflib.Graph via rdflib's JSON-LD…
The system SHALL parse the inline JSON-LD into an `rdflib.Graph` via rdflib's JSON-LD parser.

#### Scenario: Satisfies — Parse the inline JSON-LD into an rdflib.Graph via rdflib's JSON-LD…
- **WHEN** the conditions described by this requirement apply
- **THEN** Parse the inline JSON-LD into an `rdflib.Graph` via rdflib's JSON-LD parser

### Requirement: Use the record @id as the stable dataset identifier (DOI…
The system SHALL use the record `@id` as the stable dataset identifier (DOI is a publication attribute, not the discovery identity).

#### Scenario: Satisfies — Use the record @id as the stable dataset identifier (DOI…
- **WHEN** the conditions described by this requirement apply
- **THEN** Use the record `@id` as the stable dataset identifier (DOI is a publication attribute, not the discovery identity)

### Requirement: Raise a dataset error when the discovery result type is…
The system SHALL raise a dataset error when the discovery result type is unsupported.

#### Scenario: Satisfies — Raise a dataset error when the discovery result type is…
- **WHEN** the conditions described by this requirement apply
- **THEN** Raise a dataset error when the discovery result type is unsupported

### Requirement: Raise a dataset error when the payload is not valid…
The system SHALL raise a dataset error when the payload is not valid JSON-LD for rdflib.

#### Scenario: Satisfies — Raise a dataset error when the payload is not valid…
- **WHEN** the conditions described by this requirement apply
- **THEN** Raise a dataset error when the payload is not valid JSON-LD for rdflib

### Requirement: Support a dedicated Regal payload type that selects a Regal→ARC…
The system SHALL support a dedicated Regal payload type that selects a Regal→ARC mapper.

#### Scenario: Satisfies — Support a dedicated Regal payload type that selects a Regal→ARC…
- **WHEN** the conditions described by this requirement apply
- **THEN** Support a dedicated Regal payload type that selects a Regal→ARC mapper

### Requirement: Map Regal ResearchData graphs to serialized ARC RO-Crate JSON-LD as…
The system SHALL map Regal `ResearchData` graphs to serialized ARC RO-Crate JSON-LD as defined in [`docs/regal_mapping.md`](../../../docs/regal_mapping.md) and [`regal-to-arc-mapping`](../regal-to-arc-mapping/spec.md).

#### Scenario: Satisfies — Map Regal ResearchData graphs to serialized ARC RO-Crate JSON-LD as…
- **WHEN** the conditions described by this requirement apply
- **THEN** Map Regal `ResearchData` graphs to serialized ARC RO-Crate JSON-LD as defined in [`docs/regal_mapping.md`](../../../docs/regal_mapping.md) and [`regal-to-arc-mapping`](../regal-to-arc-mapping/spec.md)

### Requirement: Keep Regal mapping logic separate from schema.org mapping implementations (GeneralSchemaOrgMapper)
The system SHALL keep Regal mapping logic separate from schema.org mapping implementations (`GeneralSchemaOrgMapper`).

#### Scenario: Satisfies — Keep Regal mapping logic separate from schema.org mapping implementations (GeneralSchemaOrgMapper)
- **WHEN** the conditions described by this requirement apply
- **THEN** Keep Regal mapping logic separate from schema.org mapping implementations (`GeneralSchemaOrgMapper`)

### Requirement: Yield a mapping error (as HarvesterError) when the graph lacks…
The system SHALL yield a mapping error (as `HarvesterError`) when the graph lacks mappable ResearchData metadata; do not crash the plugin.

#### Scenario: Satisfies — Yield a mapping error (as HarvesterError) when the graph lacks…
- **WHEN** the conditions described by this requirement apply
- **THEN** Yield a mapping error (as `HarvesterError`) when the graph lacks mappable ResearchData metadata; do not crash the plugin

### Requirement: Yield SkippedRecord for duplicate discovery identifiers (counts toward skipped_datasets, not…
The system SHALL yield `SkippedRecord` for duplicate discovery identifiers (counts toward `skipped_datasets`, not failures).

#### Scenario: Satisfies — Yield SkippedRecord for duplicate discovery identifiers (counts toward skipped_datasets, not…
- **WHEN** the conditions described by this requirement apply
- **THEN** Yield `SkippedRecord` for duplicate discovery identifiers (counts toward `skipped_datasets`, not failures)

### Requirement: Yield RecordProcessingError for unusable discovery entries (same shared type as…
The system SHALL yield `RecordProcessingError` for unusable discovery entries (same shared type as inspire); the plugin forwards them to the orchestrator without a plugin-local failure wrapper type.

#### Scenario: Satisfies — Yield RecordProcessingError for unusable discovery entries (same shared type as…
- **WHEN** the conditions described by this requirement apply
- **THEN** Yield `RecordProcessingError` for unusable discovery entries (same shared type as inspire); the plugin forwards them to the orchestrator without a plugin-local failure wrapper type

### Requirement: Prefer a stable @id as record_id when known; otherwise use…
The system SHALL prefer a stable `@id` as `record_id` when known; otherwise use a synthetic discovery key so the failure still appears in `fairagro:failures`.

#### Scenario: Satisfies — Prefer a stable @id as record_id when known; otherwise use…
- **WHEN** the conditions described by this requirement apply
- **THEN** Prefer a stable `@id` as `record_id` when known; otherwise use a synthetic discovery key so the failure still appears in `fairagro:failures`

### Requirement: Edge case — - Empty JSON array on the first page
The system SHALL handle this edge case: when - Empty JSON array on the first page, then yield zero discovery results and exit cleanly. - Record missing `@id` → yield `RecordProcessingError` (DOI alone is not accepted as identity); orchestrator increments `failed_datasets` and appends `fairagro:failures`; discovery continues. - Non-object JSON array element → same `RecordProcessingError` path as missing `@id` (include index in the message); discovery continues. - `@id` already yielded in this run → `SkippedRecord` → `skipped_datasets`; do not count as a failure. - Last page shorter than the requested page size → stop pagination; do not request a further empty page. - Inline payload present but JSON-LD context unresolved / parse failure → emit a dataset or mapping error for that record (`HarvesterError`) and continue. - Configured Regal dataset type receiving a URL-only discovery result → raise a descriptive dataset construction error (plugin yields `HarvesterError`). - Non-`ResearchData` Regal types in the result set → map-error that record (`HarvesterError`); do not abort the run. - Operator `format=xml` (or any other `format`) on `sitemap_url` → ignored; request still uses `format=json`. - Operator `q=…` on `sitemap_url` → overrides default `contentType:researchData`. - Operator `until=N` on `sitemap_url` → overrides config `page_size` for pagination. - Fatal `/find` transport or response-shape failure (non-array body, HTTP error) → raise (full plugin failure), not yield; the plugin producer converts such failures (including `RobotsTxtDisallowedError`) into a yielded `LinkedDataSitemapError` so the orchestrator does not see an opaque `ExceptionGroup`. - PUBLISSO FRL `robots.txt` is `User-agent: *` / `Disallow: /` while `/find` remains a public JSON API. Operators must set `http.respect_robots_txt: false` for this RDI (see config examples / helm values); the default polite client otherwise blocks discovery before any records are fetched.

#### Scenario: Edge case — - Empty JSON array on the first page
- **WHEN** - Empty JSON array on the first page
- **THEN** yield zero discovery results and exit cleanly. - Record missing `@id` → yield `RecordProcessingError` (DOI alone is not accepted as identity); orchestrator increments `failed_datasets` and appends `fairagro:failures`; discovery continues. - Non-object JSON array element → same `RecordProcessingError` path as missing `@id` (include index in the message); discovery continues. - `@id` already yielded in this run → `SkippedRecord` → `skipped_datasets`; do not count as a failure. - Last page shorter than the requested page size → stop pagination; do not request a further empty page. - Inline payload present but JSON-LD context unresolved / parse failure → emit a dataset or mapping error for that record (`HarvesterError`) and continue. - Configured Regal dataset type receiving a URL-only discovery result → raise a descriptive dataset construction error (plugin yields `HarvesterError`). - Non-`ResearchData` Regal types in the result set → map-error that record (`HarvesterError`); do not abort the run. - Operator `format=xml` (or any other `format`) on `sitemap_url` → ignored; request still uses `format=json`. - Operator `q=…` on `sitemap_url` → overrides default `contentType:researchData`. - Operator `until=N` on `sitemap_url` → overrides config `page_size` for pagination. - Fatal `/find` transport or response-shape failure (non-array body, HTTP error) → raise (full plugin failure), not yield; the plugin producer converts such failures (including `RobotsTxtDisallowedError`) into a yielded `LinkedDataSitemapError` so the orchestrator does not see an opaque `ExceptionGroup`. - PUBLISSO FRL `robots.txt` is `User-agent: *` / `Disallow: /` while `/find` remains a public JSON API. Operators must set `http.respect_robots_txt: false` for this RDI (see config examples / helm values); the default polite client otherwise blocks discovery before any records are fetched
