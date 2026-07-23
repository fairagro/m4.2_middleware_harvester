# XML Sitemap Parser

Parse standard XML sitemap documents and yield discovery results for Schema.org harvesting.

## Requirements

- [ ] Support `SitemapType.xml` in plugin configuration.
- [ ] Accept a single sitemap entry point URL in plugin configuration.
- [ ] Parse XML sitemap documents according to the sitemap protocol.
- [ ] Support both `urlset` and `sitemapindex` document roots.
- [ ] Recursively follow nested sitemap indexes.
- [ ] Prevent sitemap loops by tracking already visited sitemap URLs.
- [x] Deduplicate discovered dataset URLs before yielding results (as `SkippedRecord`).
- [x] Yield `RecordProcessingError` for empty `<loc>` elements (do not silently skip).
- [ ] Yield one `UrlDiscoveryResult` per unique dataset URL found in a `urlset`.
- [ ] Use safe XML parsing (`defusedxml`) for untrusted content.
- [ ] Fail fast with `LinkedDataSitemapError` when XML parsing fails (malformed
      or truncated body) or when the root element is neither `urlset` nor
      `sitemapindex`.

## Edge Cases

- Duplicate dataset URLs across nested sitemaps → yield only the first occurrence.
- A sitemap URL already visited in the current traversal → skip silently.
- Missing or empty `<loc>` elements → yield `RecordProcessingError` without stopping discovery.
- Duplicate dataset URL already yielded in this run → `SkippedRecord`.
- Empty `urlset` → yield zero results and exit cleanly.
- Malformed / non-XML body → raise `LinkedDataSitemapError` (fatal discovery failure;
  plugin producer yields it into the harvest report).
- Unsupported root element → raise `LinkedDataSitemapError` the same way.
