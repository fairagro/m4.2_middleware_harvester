# MyCoRe Solr Sitemap

Discover dataset URLs from a MyCoRe repository by querying its embedded Apache Solr index and yielding one `UrlDiscoveryResult` per published object. Treated as a discovery source equivalent to a standard XML sitemap.

## Requirements

- [ ] Support `SitemapType.mycore_solr` in plugin configuration.
- [ ] Accept a MyCoRe Solr select endpoint in `sitemap_url`; query parameters are optional.
- [ ] When `sitemap_url` has no query string (or omits overridable params), fill defaults: `core=main`, `q=*:*`, `fl=id`, and `rows` from config `page_size`.
- [ ] Always set `wt=json` in software; ignore any `wt` already present on `sitemap_url`.
- [ ] When `sitemap_url` already contains an overridable query parameter (`q`, `fq`, `core`, `fl`, `rows`, …), keep the operator-supplied value and do not overwrite it with a default.
- [ ] Always set pagination `start` in software; ignore any `start` already present on `sitemap_url`.
- [ ] When `sitemap_url` contains a `rows` parameter, use it as the page size (it overrides config `page_size`).
- [ ] When `sitemap_url` has no `rows` parameter, use config `page_size` (default 200) as Solr `rows`.
- [x] Yield `RecordProcessingError` for non-object Solr docs and docs missing `id` (do not silently skip).
- [ ] Issue an HTTP GET request to the Solr URL.
- [ ] Parse the Solr JSON response envelope: read `response.numFound`, `response.start`, and `response.docs`.
- [ ] Extract the `id` field from each document in `response.docs`.
- [ ] Construct the dataset HTML page URL as `{scheme}://{host}/receive/{id}` where scheme and host are derived from `sitemap_url`.
- [ ] Yield one `UrlDiscoveryResult` per unique constructed URL.
- [ ] Deduplicate discovered dataset URLs; skip any URL already yielded in the current run.
- [ ] Support Solr pagination: when `numFound > start + len(docs)`, issue further requests by incrementing the `start` parameter until all pages are consumed.
- [ ] Raise `httpx.HTTPStatusError` on non-2xx HTTP responses (do not swallow).
- [ ] Raise `LinkedDataSitemapError` when the JSON body is not an object or lacks the expected `response` envelope (`numFound`, `start`, `docs`).

## Edge Cases

- Empty `docs` array on first page → yield zero results and exit cleanly.
- A document missing the `id` field → yield `RecordProcessingError` without stopping discovery.
- Non-object entry in `docs` → yield `RecordProcessingError` without stopping discovery.
- `id` value already yielded in this run → `SkippedRecord` (deduplication).
- `numFound` is zero → yield zero results without issuing further requests.
- Last page has fewer docs than expected (partial page) → stop pagination correctly; do not request an empty page.
- Query-free `sitemap_url` → request uses overridable defaults plus forced `wt=json`.
- Operator filter such as `q=category.top:"mir_genres:research_data"` → overrides default `q=*:*`; other defaults still apply.
- Operator `wt=xml` (or any other `wt`) on `sitemap_url` → ignored; request still uses `wt=json`.
- Hosts whose `robots.txt` disallows `/servlets/` (e.g. OpenAgrar) block the Solr select path under the default polite client; operators must set `http.respect_robots_txt: false` for machine-to-machine Solr discovery on those RDIs.
