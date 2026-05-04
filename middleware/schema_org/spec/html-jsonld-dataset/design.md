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
