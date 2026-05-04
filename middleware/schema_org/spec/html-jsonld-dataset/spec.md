# HTML JSON-LD Dataset

Fetch an HTML page and extract embedded JSON-LD markup into an `rdflib.Graph` for downstream Schema.org mapping.

## Requirements

- [ ] Accept a URL pointing to an HTML page as the dataset source.
- [ ] Fetch the HTML page over HTTP using the plugin's shared `httpx.AsyncClient`.
- [ ] Extract all `<script type="application/ld+json">` blocks from the fetched HTML.
- [ ] Parse each JSON-LD block into an `rdflib.Graph` using `rdflib`'s JSON-LD parser.
- [ ] Return the union of all parsed graphs from `to_graph()`.
- [ ] Use the page URL as the stable dataset identifier.
- [ ] Raise a `ValueError` when the HTTP response is not a successful 2xx status.
- [ ] Raise a `ValueError` when the HTML contains no `<script type="application/ld+json">` blocks.

## Edge Cases

- An HTML page with multiple JSON-LD blocks → parse each block and merge all triples into a single graph.
- A JSON-LD block that is not valid JSON → raise a descriptive `ValueError`.
- A JSON-LD block that is valid JSON but not valid JSON-LD → rdflib raises; propagate the error as-is.
- HTTP 4xx or 5xx response → raise `ValueError` with the URL and status code.
- Empty `<script type="application/ld+json">` block → skip silently (rdflib parses empty JSON-LD to an empty graph).
