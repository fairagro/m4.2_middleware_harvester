# MyCoRe Solr Sitemap — Design

## Architecture Overview

`MycoreSolrProtocol` is the SoT implementation under `middleware.generic`, registered as `ProtocolType.mycore_solr`.
`MycoreSolrSitemap` in `linked_data` is a thin shim that delegates to that Protocol (same pattern as `XmlSitemap` →
`XmlProtocol`) until YAML migrates to `generic:` + nested `protocol.mycore_solr`.

Both follow the shared discovery contract: injected with a polite HTTP client and config exposing `sitemap_url` /
`page_size`, they implement `_discover()` as an async generator yielding `UrlDiscoveryResult` objects.

Internally the Protocol delegates to a private `_fetch_page(client, url, start)` coroutine that issues a single
paginated Solr request and returns `(numFound, docs)`. The outer loop in `_discover()` advances `start` by `len(docs)`
until all pages are exhausted. A first-page cache supports `get_expected_count()` without an extra round-trip when
discovery starts at `start=0`.

Dataset HTML URLs are assembled using `urllib.parse.urlparse` to extract `scheme` and `netloc` from `sitemap_url`, then
concatenated with `/receive/{id}`.

```text
_discover(client)
  ├── start = 0
  ├── loop:
  │     numFound, docs = await _fetch_page(client, sitemap_url, start)
  │     for doc in docs:
  │         id = doc.get("id")  → skip if absent
  │         url = f"{base_url}/receive/{id}"  → skip if duplicate
  │         yield UrlDiscoveryResult(url, harvest_source_id=id)
  │     start += len(docs)
  │     break if start >= numFound or docs is empty
```

## Key Decisions

1. **Query-free select URL with mergeable defaults** — Like Regal `/find`, operators may supply only the select endpoint
   (e.g. `https://host/servlets/solr/select`). Missing overridable parameters are filled automatically: `core=main`,
   `q=*:*`, `fl=id`, and `rows` from config `page_size` (default 200). Unlike Regal (which ignores any query string),
   operator-supplied Solr params override those defaults so repository-specific filters (`q`, `fq`, …) remain
   expressible without repeating boilerplate. Response format is not operator-configurable: `wt=json` is always set by
   the software because discovery parses the Solr JSON envelope. Pagination always sets `start` (URL `start` is
   ignored). URL `rows` still wins over config `page_size`.

2. **`base_url` derived from `sitemap_url` at runtime** — Rather than adding a separate `base_url` config field, the
   receive-page base URL is computed once by extracting the scheme and host from `sitemap_url`. This avoids
   configuration duplication while keeping the derivation rule explicit and testable.

3. **Named `mycore_solr`, not `openagrar`** — The Solr endpoint path (`/servlets/solr/select`), the `response.docs` /
   `id` field structure, and the `/receive/{id}` URL pattern are standardised across all MyCoRe Repository
   installations. The name reflects the underlying platform, not a single institution, making it reusable for any
   MyCoRe-based data portal.

4. **Protocol SoT + linked_data Sitemap shim** — Discovery logic lives on `MycoreSolrProtocol` so `generic:`
   repositories can use `protocol.mycore_solr` (deprecated flat `protocol_type: mycore_solr` still lifts). The
   linked_data `SitemapType.mycore_solr` entry remains as a temporary shim that reuses the same Protocol instance
   (preserving the first-page cache across `get_expected_count` and `discover`).

5. **Pagination via `start` query parameter, not cursor** — Solr supports both offset (`start`) and cursor-based
   pagination. Offset pagination is simpler to implement and sufficient here because the result set is bounded (`rows`
   per request, total typically in the hundreds to low thousands). Cursor pagination would be needed only if result sets
   could change between pages, which is negligible for a read-only harvesting window.
