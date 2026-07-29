# HTML JSON-LD Dataset

## Purpose

Fetch an HTML page and extract embedded JSON-LD markup into an `rdflib.Graph` for downstream Schema.org mapping.

## Requirements

### Requirement: Accept a URL pointing to an HTML page as the…
The system SHALL ensure that accept a URL pointing to an HTML page as the dataset source.

#### Scenario: Satisfies — Accept a URL pointing to an HTML page as the…
- **WHEN** the conditions described by this requirement apply
- **THEN** Accept a URL pointing to an HTML page as the dataset source

### Requirement: Fetch the HTML page over HTTP using the plugin's shared…
The system SHALL ensure that fetch the HTML page over HTTP using the plugin's shared `NiceHttpClient`.

#### Scenario: Satisfies — Fetch the HTML page over HTTP using the plugin's shared…
- **WHEN** the conditions described by this requirement apply
- **THEN** Fetch the HTML page over HTTP using the plugin's shared `NiceHttpClient`

### Requirement: Extract all <script type="application/ld+json"> blocks from the fetched HTML
The system SHALL ensure that extract all `<script type="application/ld+json">` blocks from the fetched HTML.

#### Scenario: Satisfies — Extract all <script type="application/ld+json"> blocks from the fetched HTML
- **WHEN** the conditions described by this requirement apply
- **THEN** Extract all `<script type="application/ld+json">` blocks from the fetched HTML

### Requirement: If a JSON-LD block contains invalid JSON, include the full…
The system SHALL ensure that if a JSON-LD block contains invalid JSON, include the full invalid block text in the parse error message.

#### Scenario: Satisfies — If a JSON-LD block contains invalid JSON, include the full…
- **WHEN** the conditions described by this requirement apply
- **THEN** If a JSON-LD block contains invalid JSON, include the full invalid block text in the parse error message

### Requirement: Parse each JSON-LD block into an rdflib.Graph using rdflib's JSON-LD…
The system SHALL parse each JSON-LD block into an `rdflib.Graph` using `rdflib`'s JSON-LD parser.

#### Scenario: Satisfies — Parse each JSON-LD block into an rdflib.Graph using rdflib's JSON-LD…
- **WHEN** the conditions described by this requirement apply
- **THEN** Parse each JSON-LD block into an `rdflib.Graph` using `rdflib`'s JSON-LD parser

### Requirement: Return the union of all parsed graphs from to_graph()
The system SHALL ensure that return the union of all parsed graphs from `to_graph()`.

#### Scenario: Satisfies — Return the union of all parsed graphs from to_graph()
- **WHEN** the conditions described by this requirement apply
- **THEN** Return the union of all parsed graphs from `to_graph()`

### Requirement: Use the page URL as the stable dataset identifier
The system SHALL ensure that use the page URL as the stable dataset identifier.

#### Scenario: Satisfies — Use the page URL as the stable dataset identifier
- **WHEN** the conditions described by this requirement apply
- **THEN** Use the page URL as the stable dataset identifier

### Requirement: Raise a LinkedDataDatasetError when the HTTP request fails
The system SHALL ensure that raise a `LinkedDataDatasetError` when the HTTP request fails.

#### Scenario: Satisfies — Raise a LinkedDataDatasetError when the HTTP request fails
- **WHEN** the conditions described by this requirement apply
- **THEN** Raise a `LinkedDataDatasetError` when the HTTP request fails

### Requirement: Raise a LinkedDataDatasetError when the HTML contains no <script type="application/ld+json">…
The system SHALL ensure that raise a `LinkedDataDatasetError` when the HTML contains no `<script type="application/ld+json">` blocks.

#### Scenario: Satisfies — Raise a LinkedDataDatasetError when the HTML contains no <script type="application/ld+json">…
- **WHEN** the conditions described by this requirement apply
- **THEN** Raise a `LinkedDataDatasetError` when the HTML contains no `<script type="application/ld+json">` blocks

### Requirement: Edge case — - An HTML page with multiple JSON-LD blocks
The system SHALL handle this edge case: when - An HTML page with multiple JSON-LD blocks, then parse each block and merge all triples into a single graph. - A JSON-LD block that is not valid JSON → raise a descriptive `LinkedDataDatasetError`. - A JSON-LD block that is valid JSON but not valid JSON-LD → rdflib raises; propagate as `LinkedDataDatasetError`. - HTTP error response → raise `LinkedDataDatasetError` with the URL and error detail. - Empty `<script type="application/ld+json">` block → skip silently (rdflib parses empty JSON-LD to an empty graph). - URL resolves via one or more redirects (e.g. `https://doi.org/…` → repository landing page) → follow all redirects transparently and parse the final response. - `robots.txt` fetch fails or times out → handled by `NiceHttpClient`: treat host as "allow all" and log a warning. - All retries exhausted → `NiceHttpClient.retry_get` raises; `_fetch_html` wraps it in `LinkedDataDatasetError`; the dataset is skipped and harvesting continues.

#### Scenario: Edge case — - An HTML page with multiple JSON-LD blocks
- **WHEN** - An HTML page with multiple JSON-LD blocks
- **THEN** parse each block and merge all triples into a single graph. - A JSON-LD block that is not valid JSON → raise a descriptive `LinkedDataDatasetError`. - A JSON-LD block that is valid JSON but not valid JSON-LD → rdflib raises; propagate as `LinkedDataDatasetError`. - HTTP error response → raise `LinkedDataDatasetError` with the URL and error detail. - Empty `<script type="application/ld+json">` block → skip silently (rdflib parses empty JSON-LD to an empty graph). - URL resolves via one or more redirects (e.g. `https://doi.org/…` → repository landing page) → follow all redirects transparently and parse the final response. - `robots.txt` fetch fails or times out → handled by `NiceHttpClient`: treat host as "allow all" and log a warning. - All retries exhausted → `NiceHttpClient.retry_get` raises; `_fetch_html` wraps it in `LinkedDataDatasetError`; the dataset is skipped and harvesting continues

## HTTP behaviour

All retry logic, timeouts, per-host rate limiting, robots.txt enforcement, and
`User-Agent` handling are delegated to `NiceHttpClient` / `NiceHttpClientConfig`
(see `openspec/specs/nice-http-client/spec.md`). This component adds no HTTP config of its own.
