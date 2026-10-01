## Purpose

Shared remote JSON-LD context resolution for PayloadParsers: optional operator-pinned root URL, polite HTTP fetch on
cache miss, process-lifetime document cache including transitive `@import` targets, so `graph.parse` never performs
uncached network context loads. When the pin is unset, remotes are still fetched; `ParserConfig` warns at load (legacy
configs).

## ADDED Requirements

### Requirement: Optional single pinned context URL on parser config

The system SHALL accept an optional `parser.allowed_context_url` (http or https IRI). When set, the only remote
`@context` string allowed on the payload (alone or as the sole remote string in a `@context` list) MUST equal that URL
exactly; inline object contexts remain allowed. When unset, absolute http(s) remote `@context` IRIs on the payload MUST
still be accepted and resolved through the shared loader. When a JSON-LD `ParserConfig` is validated with
`allowed_context_url` unset, the system MUST emit a `logger.warning` recommending that operators set the field (same
pattern as other legacy config warnings). Relative or non-http(s) references MUST fail.

#### Scenario: Unset fetches remote payload context with warning

- **WHEN** a repository configures `parser.type` as `jsonld` or `html_jsonld` without `allowed_context_url`
- **THEN** config validation logs a warning recommending that operators set `allowed_context_url`

#### Scenario: Unset still resolves remote context at parse time

- **WHEN** `allowed_context_url` is unset, the payload `@context` is an absolute http(s) URL, and a polite HTTP client
  is provided
- **THEN** parse proceeds via the shared loader

#### Scenario: Unset without client fails

- **WHEN** `allowed_context_url` is unset, the payload `@context` is a remote URL, and `client` is null
- **THEN** parse fails indicating an HTTP client is required (without a silent network fetch)

#### Scenario: Configured URL accepted

- **WHEN** `allowed_context_url` is `https://example.org/context.json` and the payload `@context` is that same string
- **THEN** parse may proceed using the shared context loader (no unset-field warning)

#### Scenario: Wrong URL rejected

- **WHEN** `allowed_context_url` is set and the payload `@context` is a different remote URL
- **THEN** parse fails without fetching the payload URL

### Requirement: Process-lifetime cache and polite fetch

The system SHALL fetch remote context documents via the polite HTTP client only on a process-lifetime cache miss for
that URL, and SHALL reuse the cached document for later parses in the same process. Transitive `@import` documents
discovered while resolving a root context SHALL also be fetched on miss and cached by URL. Cache hits MUST NOT perform
HTTP.

#### Scenario: Second parse uses cache

- **WHEN** two records in one process both reference the same remote context URL
- **THEN** the root context document is fetched at most once

#### Scenario: Import documents cached

- **WHEN** the root context document contains `@import` of another http(s) document
- **THEN** that import is fetched on first miss and served from cache on later resolves without a second HTTP GET

### Requirement: No uncached rdflib context network during parse

After the shared loader has populated the cache for the needed URLs, JSON-LD `graph.parse` for `jsonld` and
`html_jsonld` MUST NOT trigger an additional uncached network retrieval of context documents.

#### Scenario: Parse does not bypass the cache

- **WHEN** a payload uses a remote `@context` and the cache already holds that document
- **THEN** completing parse does not issue a new HTTP GET for that context URL
