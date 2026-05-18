# MyCoRe Solr Sitemap

Discover dataset URLs from a MyCoRe repository by querying its embedded Apache Solr index and yielding one `UrlDiscoveryResult` per published object. Treated as a discovery source equivalent to a standard XML sitemap.

## Requirements

- [ ] Support `SitemapType.mycore_solr` in plugin configuration.
- [ ] Accept a fully-formed Solr query URL (including all query parameters) in the existing `sitemap_url` config field.
- [ ] Issue an HTTP GET request to the Solr URL.
- [ ] Parse the Solr JSON response envelope: read `response.numFound`, `response.start`, and `response.docs`.
- [ ] Extract the `id` field from each document in `response.docs`.
- [ ] Construct the dataset HTML page URL as `{scheme}://{host}/receive/{id}` where scheme and host are derived from `sitemap_url`.
- [ ] Yield one `UrlDiscoveryResult` per unique constructed URL.
- [ ] Deduplicate discovered dataset URLs; skip any URL already yielded in the current run.
- [ ] Support Solr pagination: when `numFound > start + len(docs)`, issue further requests by incrementing the `start` parameter until all pages are consumed.
- [ ] Raise `httpx.HTTPStatusError` on non-2xx HTTP responses (do not swallow).
- [ ] Raise `ValueError` when the JSON response does not contain the expected `response.docs` key.

## Edge Cases

- Empty `docs` array on first page → yield zero results and exit cleanly.
- A document missing the `id` field → skip that document without stopping discovery.
- `id` value already yielded in this run → skip silently (deduplication).
- `numFound` is zero → yield zero results without issuing further requests.
- Last page has fewer docs than expected (partial page) → stop pagination correctly; do not request an empty page.
