# MyCoRe Solr Sitemap

## Purpose

Discover dataset URLs from a MyCoRe repository by querying its embedded Apache Solr index and yielding one `UrlDiscoveryResult` per published object. Treated as a discovery source equivalent to a standard XML sitemap.

## Requirements

### Requirement: Support SitemapType.mycore_solr in plugin configuration
The system SHALL ensure that support `SitemapType.mycore_solr` in plugin configuration.

#### Scenario: Satisfies — Support SitemapType.mycore_solr in plugin configuration
- **WHEN** the conditions described by this requirement apply
- **THEN** Support `SitemapType.mycore_solr` in plugin configuration

### Requirement: Accept a MyCoRe Solr select endpoint in sitemap_url; query parameters…
The system SHALL ensure that accept a MyCoRe Solr select endpoint in `sitemap_url`; query parameters are optional.

#### Scenario: Satisfies — Accept a MyCoRe Solr select endpoint in sitemap_url; query parameters…
- **WHEN** the conditions described by this requirement apply
- **THEN** Accept a MyCoRe Solr select endpoint in `sitemap_url`; query parameters are optional

### Requirement: When sitemap_url has no query string (or omits overridable params),…
The system SHALL ensure that when `sitemap_url` has no query string (or omits overridable params), fill defaults: `core=main`, `q=*:*`, `fl=id`, and `rows` from config `page_size`.

#### Scenario: Satisfies — When sitemap_url has no query string (or omits overridable params),…
- **WHEN** the conditions described by this requirement apply
- **THEN** When `sitemap_url` has no query string (or omits overridable params), fill defaults: `core=main`, `q=*:*`, `fl=id`, and `rows` from config `page_size`

### Requirement: Always set wt=json in software; ignore any wt already present…
The system SHALL ensure that always set `wt=json` in software; ignore any `wt` already present on `sitemap_url`.

#### Scenario: Satisfies — Always set wt=json in software; ignore any wt already present…
- **WHEN** the conditions described by this requirement apply
- **THEN** Always set `wt=json` in software; ignore any `wt` already present on `sitemap_url`

### Requirement: When sitemap_url already contains an overridable query parameter (q, fq,…
The system SHALL ensure that when `sitemap_url` already contains an overridable query parameter (`q`, `fq`, `core`, `fl`, `rows`, …), keep the operator-supplied value and do not overwrite it with a default.

#### Scenario: Satisfies — When sitemap_url already contains an overridable query parameter (q, fq,…
- **WHEN** the conditions described by this requirement apply
- **THEN** When `sitemap_url` already contains an overridable query parameter (`q`, `fq`, `core`, `fl`, `rows`, …), keep the operator-supplied value and do not overwrite it with a default

### Requirement: Always set pagination start in software; ignore any start already…
The system SHALL ensure that always set pagination `start` in software; ignore any `start` already present on `sitemap_url`.

#### Scenario: Satisfies — Always set pagination start in software; ignore any start already…
- **WHEN** the conditions described by this requirement apply
- **THEN** Always set pagination `start` in software; ignore any `start` already present on `sitemap_url`

### Requirement: When sitemap_url contains a rows parameter, use it as the…
The system SHALL ensure that when `sitemap_url` contains a `rows` parameter, use it as the page size (it overrides config `page_size`).

#### Scenario: Satisfies — When sitemap_url contains a rows parameter, use it as the…
- **WHEN** the conditions described by this requirement apply
- **THEN** When `sitemap_url` contains a `rows` parameter, use it as the page size (it overrides config `page_size`)

### Requirement: When sitemap_url has no rows parameter, use config page_size (default…
The system SHALL ensure that when `sitemap_url` has no `rows` parameter, use config `page_size` (default 200) as Solr `rows`.

#### Scenario: Satisfies — When sitemap_url has no rows parameter, use config page_size (default…
- **WHEN** the conditions described by this requirement apply
- **THEN** When `sitemap_url` has no `rows` parameter, use config `page_size` (default 200) as Solr `rows`

### Requirement: Yield RecordProcessingError for non-object Solr docs and docs missing id…
The system SHALL ensure that yield `RecordProcessingError` for non-object Solr docs and docs missing `id` (do not silently skip).

#### Scenario: Satisfies — Yield RecordProcessingError for non-object Solr docs and docs missing id…
- **WHEN** the conditions described by this requirement apply
- **THEN** Yield `RecordProcessingError` for non-object Solr docs and docs missing `id` (do not silently skip)

### Requirement: Issue an HTTP GET request to the Solr URL
The system SHALL ensure that issue an HTTP GET request to the Solr URL.

#### Scenario: Satisfies — Issue an HTTP GET request to the Solr URL
- **WHEN** the conditions described by this requirement apply
- **THEN** Issue an HTTP GET request to the Solr URL

### Requirement: Parse the Solr JSON response envelope: read response.numFound, response.start, and…
The system SHALL parse the Solr JSON response envelope: read `response.numFound`, `response.start`, and `response.docs`.

#### Scenario: Satisfies — Parse the Solr JSON response envelope: read response.numFound, response.start, and…
- **WHEN** the conditions described by this requirement apply
- **THEN** Parse the Solr JSON response envelope: read `response.numFound`, `response.start`, and `response.docs`

### Requirement: Extract the id field from each document in response.docs
The system SHALL ensure that extract the `id` field from each document in `response.docs`.

#### Scenario: Satisfies — Extract the id field from each document in response.docs
- **WHEN** the conditions described by this requirement apply
- **THEN** Extract the `id` field from each document in `response.docs`

### Requirement: Construct the dataset HTML page URL as {scheme}://{host}/receive/{id} where scheme…
The system SHALL ensure that construct the dataset HTML page URL as `{scheme}://{host}/receive/{id}` where scheme and host are derived from `sitemap_url`.

#### Scenario: Satisfies — Construct the dataset HTML page URL as {scheme}://{host}/receive/{id} where scheme…
- **WHEN** the conditions described by this requirement apply
- **THEN** Construct the dataset HTML page URL as `{scheme}://{host}/receive/{id}` where scheme and host are derived from `sitemap_url`

### Requirement: Yield one UrlDiscoveryResult per unique constructed URL
The system SHALL ensure that yield one `UrlDiscoveryResult` per unique constructed URL.

#### Scenario: Satisfies — Yield one UrlDiscoveryResult per unique constructed URL
- **WHEN** the conditions described by this requirement apply
- **THEN** Yield one `UrlDiscoveryResult` per unique constructed URL

### Requirement: Deduplicate discovered dataset URLs; skip any URL already yielded in…
The system SHALL ensure that deduplicate discovered dataset URLs; skip any URL already yielded in the current run.

#### Scenario: Satisfies — Deduplicate discovered dataset URLs; skip any URL already yielded in…
- **WHEN** the conditions described by this requirement apply
- **THEN** Deduplicate discovered dataset URLs; skip any URL already yielded in the current run

### Requirement: Support Solr pagination: when numFound > start + len(docs), issue…
The system SHALL ensure that support Solr pagination: when `numFound > start + len(docs)`, issue further requests by incrementing the `start` parameter until all pages are consumed.

#### Scenario: Satisfies — Support Solr pagination: when numFound > start + len(docs), issue…
- **WHEN** the conditions described by this requirement apply
- **THEN** Support Solr pagination: when `numFound > start + len(docs)`, issue further requests by incrementing the `start` parameter until all pages are consumed

### Requirement: Raise httpx.HTTPStatusError on non-2xx HTTP responses (do not swallow)
The system SHALL ensure that raise `httpx.HTTPStatusError` on non-2xx HTTP responses (do not swallow).

#### Scenario: Satisfies — Raise httpx.HTTPStatusError on non-2xx HTTP responses (do not swallow)
- **WHEN** the conditions described by this requirement apply
- **THEN** Raise `httpx.HTTPStatusError` on non-2xx HTTP responses (do not swallow)

### Requirement: Raise LinkedDataSitemapError when the JSON body is not an object…
The system SHALL ensure that raise `LinkedDataSitemapError` when the JSON body is not an object or lacks the expected `response` envelope (`numFound`, `start`, `docs`).

#### Scenario: Satisfies — Raise LinkedDataSitemapError when the JSON body is not an object…
- **WHEN** the conditions described by this requirement apply
- **THEN** Raise `LinkedDataSitemapError` when the JSON body is not an object or lacks the expected `response` envelope (`numFound`, `start`, `docs`)

### Requirement: Edge case — - Empty docs array on first page
The system SHALL handle this edge case: when - Empty `docs` array on first page, then yield zero results and exit cleanly. - A document missing the `id` field → yield `RecordProcessingError` without stopping discovery. - Non-object entry in `docs` → yield `RecordProcessingError` without stopping discovery. - `id` value already yielded in this run → `SkippedRecord` (deduplication). - `numFound` is zero → yield zero results without issuing further requests. - Last page has fewer docs than expected (partial page) → stop pagination correctly; do not request an empty page. - Query-free `sitemap_url` → request uses overridable defaults plus forced `wt=json`. - Operator filter such as `q=category.top:"mir_genres:research_data"` → overrides default `q=*:*`; other defaults still apply. - Operator `wt=xml` (or any other `wt`) on `sitemap_url` → ignored; request still uses `wt=json`. - Hosts whose `robots.txt` disallows `/servlets/` (e.g. OpenAgrar) block the Solr select path under the default polite client; operators must set `http.respect_robots_txt: false` for machine-to-machine Solr discovery on those RDIs.

#### Scenario: Edge case — - Empty docs array on first page
- **WHEN** - Empty `docs` array on first page
- **THEN** yield zero results and exit cleanly. - A document missing the `id` field → yield `RecordProcessingError` without stopping discovery. - Non-object entry in `docs` → yield `RecordProcessingError` without stopping discovery. - `id` value already yielded in this run → `SkippedRecord` (deduplication). - `numFound` is zero → yield zero results without issuing further requests. - Last page has fewer docs than expected (partial page) → stop pagination correctly; do not request an empty page. - Query-free `sitemap_url` → request uses overridable defaults plus forced `wt=json`. - Operator filter such as `q=category.top:"mir_genres:research_data"` → overrides default `q=*:*`; other defaults still apply. - Operator `wt=xml` (or any other `wt`) on `sitemap_url` → ignored; request still uses `wt=json`. - Hosts whose `robots.txt` disallows `/servlets/` (e.g. OpenAgrar) block the Solr select path under the default polite client; operators must set `http.respect_robots_txt: false` for machine-to-machine Solr discovery on those RDIs
