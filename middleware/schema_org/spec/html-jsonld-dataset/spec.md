# HTML JSON-LD Dataset

Fetch an HTML page and extract embedded JSON-LD markup into an `rdflib.Graph` for downstream Schema.org mapping.

## Requirements

- [ ] Accept a URL pointing to an HTML page as the dataset source.
- [ ] Fetch the HTML page over HTTP using the plugin's shared `NiceHttpClient`
  (via `NiceHttpClient.retry_get()`); follow HTTP redirects transparently
  (e.g. DOI resolver → repository landing page).
- [ ] Extract all `<script type="application/ld+json">` blocks from the fetched HTML.
- [ ] If a JSON-LD block contains invalid JSON, include the full invalid block text in the parse error message.
- [ ] Parse each JSON-LD block into an `rdflib.Graph` using `rdflib`'s JSON-LD parser.
- [ ] Return the union of all parsed graphs from `to_graph()`.
- [ ] Use the page URL as the stable dataset identifier.
- [ ] Raise a `SchemaOrgDatasetError` when the HTTP request fails.
- [ ] Raise a `SchemaOrgDatasetError` when the HTML contains no `<script type="application/ld+json">` blocks.

## HTTP behaviour

All retry logic, timeouts, per-host rate limiting, robots.txt enforcement, and
`User-Agent` handling are delegated to `NiceHttpClient` / `NiceHttpClientConfig`
(see `spec/nice-http-client/spec.md`). This component adds no HTTP config of its own.

## Edge Cases

- An HTML page with multiple JSON-LD blocks → parse each block and merge all triples into a single graph.
- A JSON-LD block that is not valid JSON → raise a descriptive `SchemaOrgDatasetError`.
- A JSON-LD block that is valid JSON but not valid JSON-LD → rdflib raises; propagate as `SchemaOrgDatasetError`.
- HTTP error response → raise `SchemaOrgDatasetError` with the URL and error detail.
- Empty `<script type="application/ld+json">` block → skip silently (rdflib parses empty JSON-LD to an empty graph).
- URL resolves via one or more redirects (e.g. `https://doi.org/…` → repository landing page) → follow all redirects transparently and parse the final response.
- `robots.txt` fetch fails or times out → handled by `NiceHttpClient`: treat host as "allow all" and log a warning.
- All retries exhausted → `NiceHttpClient.retry_get` raises; `_fetch_html` wraps it in `SchemaOrgDatasetError`; the dataset is skipped and harvesting continues.
