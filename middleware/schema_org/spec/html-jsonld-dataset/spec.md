# HTML JSON-LD Dataset

Fetch an HTML page and extract embedded JSON-LD markup into an `rdflib.Graph` for downstream Schema.org mapping.

## Requirements

- [ ] Accept a URL pointing to an HTML page as the dataset source.
- [ ] Fetch the HTML page over HTTP using the plugin's shared `httpx.AsyncClient`.
- [ ] Follow HTTP redirects when fetching the HTML page (e.g. DOI resolver → repository landing page).
- [ ] Extract all `<script type="application/ld+json">` blocks from the fetched HTML.
- [ ] If a JSON-LD block contains invalid JSON, include the full invalid block text in the parse error message.
- [ ] Parse each JSON-LD block into an `rdflib.Graph` using `rdflib`'s JSON-LD parser.
- [ ] Return the union of all parsed graphs from `to_graph()`.
- [ ] Use the page URL as the stable dataset identifier.
- [ ] Raise a `ValueError` when the HTTP response is not a successful 2xx status.
- [ ] Raise a `ValueError` when the HTML contains no `<script type="application/ld+json">` blocks.

## Retry

- [ ] Retry a failed request on transient errors: network/connection errors, read timeouts, and HTTP 5xx responses.
- [ ] The maximum number of retry attempts is configurable (default: 3); 0 disables retries.
- [ ] Wait between retries using exponential backoff: `base_delay × factor^(attempt − 1)`.
- [ ] The backoff base delay (seconds) and growth factor are each configurable (defaults: base 1 s, factor 1.5).
- [ ] Apply ± 10 % random jitter to each calculated backoff interval to avoid thundering-herd conditions.
- [ ] On an HTTP 429 or 503 response, use the `Retry-After` header value as the wait time if present; fall back to the calculated backoff otherwise.
- [ ] After all retry attempts are exhausted, log an error with the URL and the last error detail and skip the dataset.

## HTTP Timeouts

- [ ] Apply a configurable connect timeout to every outgoing request (default: 10 s).
- [ ] Apply a configurable read timeout to every outgoing request (default: 30 s).

## Polite Harvesting

- [ ] Send a descriptive `User-Agent` header on every request: `FAIRagro-Harvester/1.0 (+<contact_email>)`, where `contact_email` is a configurable string.
- [ ] Fetch and cache `robots.txt` for each host before issuing any request to that host.
- [ ] Skip any URL whose path is disallowed for the harvester's user-agent by `robots.txt`; log a warning and treat the dataset as unavailable.
- [ ] Respect the `Crawl-delay` directive in `robots.txt` as the minimum per-host inter-request delay when present.
- [ ] Apply a configurable minimum delay between consecutive requests to the same host (default: 1 s); the `Crawl-delay` value takes precedence when it is larger.
- [ ] Limit the total number of concurrent outgoing requests via the existing `max_connections` configuration parameter.

## Edge Cases

- An HTML page with multiple JSON-LD blocks → parse each block and merge all triples into a single graph.
- A JSON-LD block that is not valid JSON → raise a descriptive `ValueError`.
- A JSON-LD block that is valid JSON but not valid JSON-LD → rdflib raises; propagate the error as-is.
- HTTP 4xx or 5xx response → raise `ValueError` with the URL and status code.
- Empty `<script type="application/ld+json">` block → skip silently (rdflib parses empty JSON-LD to an empty graph).
- URL resolves via one or more redirects (e.g. `https://doi.org/…` → repository landing page) → follow all redirects transparently and parse the final response.
- `robots.txt` fetch fails or times out → treat host as "allow all" and log a warning.
- `Retry-After` value exceeds a configured maximum wait → cap the wait at the maximum and log a warning.
- All retries exhausted → log an error with the URL and the last error detail; the dataset is skipped and harvesting continues with the next URL.
