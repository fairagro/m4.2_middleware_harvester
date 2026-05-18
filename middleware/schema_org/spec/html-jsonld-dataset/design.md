# HTML JSON-LD Dataset — Design

## Architecture overview

`HtmlJsonLdDataset` is a `Dataset` subclass registered under `DatasetType.html_jsonld`. It receives a URL from a `UrlDiscoveryResult`, fetches the HTML page via the plugin's shared `httpx.AsyncClient`, and extracts embedded JSON-LD blocks using `html.parser` from the Python standard library. The extracted JSON-LD strings are parsed into `rdflib.Graph` objects using rdflib's built-in JSON-LD parser, and the resulting triples are merged into a single graph returned by `to_graph()`.

The `httpx.AsyncClient` instance is injected at construction time via `from_discovery_result()`. Because `Dataset.from_discovery_result()` only receives a `DiscoveryResult`, the client is passed separately through a dedicated constructor argument. The plugin is responsible for supplying the client when creating the dataset instance.

## Key Decisions

1. **Use `html.parser` (stdlib) to extract JSON-LD blocks, not a full HTML parser library**
   — JSON-LD blocks in HTML are self-contained `<script>` elements with a fixed `type` attribute. Extracting them with `html.parser` requires no additional dependencies and avoids the complexity of a full DOM tree. An alternative like `lxml` or `BeautifulSoup` would add a dependency without providing meaningful benefit for this narrow task.

2. **Use rdflib's built-in JSON-LD parser, not `json-ld` or third-party alternatives**
   — rdflib is already a project dependency and its JSON-LD parser handles the conversion to an `rdflib.Graph` directly. Using a separate JSON-LD library would require an intermediate step to convert the result to rdflib's graph model.

3. **Inject `httpx.AsyncClient` as a constructor argument, not as a parameter to `to_graph()`**
   — The `to_graph()` interface is fixed by the `Dataset` abstract base class and must not carry plugin-level infrastructure. The client is part of the dataset's construction context, not its payload extraction logic, so it belongs in `__init__`.

4. **Register under `DatasetType.html_jsonld`, not a generic `DatasetType.html`**
   — A single `html` type would imply auto-detection of the embedded format (JSON-LD, RDFa, Microdata). Explicit type names keep each implementation simple and independently testable. RDFa and Microdata support can be added later as separate `DatasetType` values without changing existing code.

5. **Pass `follow_redirects=True` on each `client.get()` call, not globally on the `AsyncClient`**
   — Dataset URLs frequently resolve via external redirect services (e.g. DOI resolvers). Redirects must be followed at the individual request level so the final response body can be inspected. Enabling redirect-following per request rather than on the shared client keeps the behaviour explicit and scoped to the single call that requires it; the shared client is also used for sitemap discovery where the redirect policy may differ.

6. **Implement retry with exponential backoff + jitter in `HtmlJsonLdDataset`, not via an httpx transport**
   — httpx provides a `Retry` transport adapter, but it only covers connection-level errors and gives no control over HTTP-level retries (5xx, 429, 503) or backoff strategy. Implementing retry logic directly in `to_graph()` keeps the retry policy explicit, testable, and independent of the HTTP transport. Jitter (± 10 %) is applied to each backoff interval to avoid synchronised retries when multiple dataset fetches fail at the same time.
   — On 429/503 the `Retry-After` header is used as the wait time when present; this respects the server's explicit back-pressure signal rather than guessing a delay.

7. **Configure connect and read timeouts independently via `httpx.Timeout`, not a single scalar**
   — httpx exposes a `Timeout` object with four axes: `connect`, `read`, `write`, and `pool`. For a read-only harvester the relevant pair is `connect` (TCP handshake + TLS) and `read` (inter-chunk idle time). Separating them matters because some repository servers accept connections quickly but serve large HTML responses slowly; a single timeout would either trigger prematurely on large pages or hide hung connections. `write` and `pool` can remain at their httpx defaults.

8. **Manage polite-harvesting state (robots.txt cache, per-host semaphores, last-request timestamps) inside the plugin, not inside `HtmlJsonLdDataset`**
   — `HtmlJsonLdDataset` is a single-URL abstraction. Per-host coordination state is inherently cross-dataset and belongs to the component that issues multiple dataset fetches. The plugin passes the shared `httpx.AsyncClient` to each dataset; it can equally pass or apply per-host rate-limiting and concurrency control before calling `to_graph()`.
   — `robots.txt` is cached per host for the lifetime of a single harvest run. A fetch failure is non-fatal: the host is treated as "allow all" and a warning is logged, consistent with the lenient interpretation used by most crawlers.
   — The `User-Agent` string format `FAIRagro-Harvester/1.0 (+<email>)` follows the de-facto convention used by well-behaved crawlers: a product token plus a bracketed contact URI. The email makes it easy for server operators to reach the project if the harvester causes problems.
