# XML Sitemap Parser

Parse standard XML sitemap documents and yield discovery results for Schema.org harvesting.

## Requirements

- [ ] Support `SitemapType.xml` in plugin configuration.
- [ ] Accept a single sitemap entry point URL in plugin configuration.
- [ ] Parse XML sitemap documents according to the sitemap protocol.
- [ ] Support both `urlset` and `sitemapindex` document roots.
- [ ] Recursively follow nested sitemap indexes.
- [ ] Prevent sitemap loops by tracking already visited sitemap URLs.
- [ ] Deduplicate discovered dataset URLs before yielding results.
- [ ] Yield one `UrlDiscoveryResult` per unique dataset URL found in a `urlset`.
- [ ] Use safe XML parsing (`defusedxml`) for untrusted content.
- [ ] Fail fast with a `ValueError` when the root element is neither `urlset` nor `sitemapindex`.

## Edge Cases

- Duplicate dataset URLs across nested sitemaps → yield only the first occurrence.
- A sitemap URL already visited in the current traversal → skip silently.
- Missing or empty `<loc>` elements → skip without stopping discovery.
- Empty `urlset` → yield zero results and exit cleanly.
