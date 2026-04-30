# XML Sitemap Parser

Parse standard XML sitemap documents to discover dataset URLs for Schema.org harvesting.

## Requirements

- [ ] Support `SitemapType.xml` in plugin configuration.
- [ ] Accept a single sitemap entry point URL in plugin configuration.
- [ ] Parse XML sitemap documents according to the sitemap protocol.
- [ ] Support both `urlset` and `sitemapindex` roots.
- [ ] Recursively follow nested sitemap indexes and deduplicate discovered dataset URLs.
- [ ] Emit `Dataset` descriptors for each discovered dataset URL without parsing dataset payloads.
- [ ] Use safe XML parsing for untrusted content.
- [ ] Fail fast when the sitemap type is unsupported.
- [ ] On HTTP fetch or XML parse errors, emit a dataset-level processing error and continue with remaining sitemaps.

## Edge Cases

- Duplicate dataset URLs across sitemaps must be suppressed.
- Empty sitemap documents must yield zero datasets.
- Sitemap documents with unsupported root elements must fail with an explicit error.
- Missing or empty `<loc>` elements must be skipped without stopping discovery.
