# XML Sitemap Parser — Design

## Architecture overview

`XmlSitemap` translates standard XML sitemap documents into `UrlDiscoveryResult` objects. It does not parse dataset payloads, instantiate `Dataset` objects, or perform any mapping.

The parser starts from a single configured URL and traverses nested `sitemapindex` documents recursively. Deduplication operates at two levels: sitemap-level (visited sitemap URLs, to prevent cycles) and dataset-level (visited dataset URLs, to suppress duplicates).

## Key Decisions

1. **Implement sitemap parsing in `XmlSitemap` inside `sitemap.py`**
   — This isolates XML protocol handling and allows additional sitemap source types to be added as separate registered subclasses.

2. **Yield `UrlDiscoveryResult` objects, not `Dataset` instances**
   — The sitemap parser only knows URL strings. Constructing a `Dataset` from a URL requires provider-specific knowledge (e.g., whether to fetch the URL, whether to parse embedded JSON-LD). That responsibility belongs to the `Dataset` subclass via `from_discovery_result()`.

3. **Use `defusedxml` for XML parsing**
   — Sitemap content comes from external sources and must be treated as untrusted. `defusedxml` prevents XML entity attacks.
