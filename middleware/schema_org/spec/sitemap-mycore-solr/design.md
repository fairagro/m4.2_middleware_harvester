# MyCoRe Solr Sitemap — Design

## Architecture Overview

`MycoreSolrSitemap` is a concrete `Sitemap` subclass registered under `SitemapType.mycore_solr`. It follows the same structural contract as `XmlSitemap`: injected with a shared `httpx.AsyncClient` and the plugin `Config`, it implements `_discover()` as an async generator yielding `UrlDiscoveryResult` objects.

Internally it delegates to a private `_fetch_page(client, url, start)` coroutine that issues a single paginated Solr request and returns `(numFound, docs)`. The outer loop in `_discover()` advances `start` by `len(docs)` until all pages are exhausted.

Dataset HTML URLs are assembled using `urllib.parse.urlparse` to extract `scheme` and `netloc` from `sitemap_url`, then concatenated with `/receive/{id}`.

```text
_discover(client)
  ├── start = 0
  ├── loop:
  │     numFound, docs = await _fetch_page(client, sitemap_url, start)
  │     for doc in docs:
  │         id = doc.get("id")  → skip if absent
  │         url = f"{base_url}/receive/{id}"  → skip if duplicate
  │         yield UrlDiscoveryResult(url)
  │     start += len(docs)
  │     break if start >= numFound or docs is empty
```

## Key Decisions

1. **Full Solr URL in `sitemap_url`, no extra config fields**
   — The complete Solr query URL (including `core`, `q`, `fl`, `wt`, `rows`) is supplied by the operator directly in the existing `sitemap_url` field. Building a query from separate fields would require a query-builder layer that adds complexity without increasing expressiveness. Operators already know how to construct a Solr URL from the admin interface.

2. **`base_url` derived from `sitemap_url` at runtime**
   — Rather than adding a separate `base_url` config field, the receive-page base URL is computed once by extracting the scheme and host from `sitemap_url`. This avoids configuration duplication while keeping the derivation rule explicit and testable.

3. **Named `mycore_solr`, not `openagrar`**
   — The Solr endpoint path (`/servlets/solr/select`), the `response.docs` / `id` field structure, and the `/receive/{id}` URL pattern are standardised across all MyCoRe Repository installations. The name reflects the underlying platform, not a single institution, making it reusable for any MyCoRe-based data portal.

4. **Treated as a `Sitemap` despite being an API response**
   — The conceptual role of this source is identical to an XML sitemap: it enumerates dataset URLs that feed the subsequent `Dataset` fetching stage. Implementing `Sitemap` reuses the existing registration, injection, and deduplication infrastructure without any interface changes.

5. **Pagination via `start` query parameter, not cursor**
   — Solr supports both offset (`start`) and cursor-based pagination. Offset pagination is simpler to implement and sufficient here because the result set is bounded (`rows=1000` per request, total typically in the hundreds to low thousands). Cursor pagination would be needed only if result sets could change between pages, which is negligible for a read-only harvesting window.
