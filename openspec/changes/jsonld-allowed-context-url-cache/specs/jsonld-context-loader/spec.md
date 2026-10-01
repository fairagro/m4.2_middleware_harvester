## Purpose

Shared allowlisted remote JSON-LD context resolution for PayloadParsers: one operator-configured root URL, polite HTTP
fetch on cache miss, process-lifetime document cache including transitive `@import` targets, so `graph.parse` never
performs uncached network context loads.

## ADDED Requirements

### Requirement: Optional single allowlisted context URL on parser config

The system SHALL accept an optional `parser.allowed_context_url` (http or https IRI). When unset, PayloadParsers that
consume this policy MUST reject remote `@context` IRIs on the discovery payload. When set, the only remote `@context`
string allowed on the payload (alone or as the sole remote string in a `@context` list) MUST equal that URL exactly;
inline object contexts remain allowed.

#### Scenario: Unset rejects remote payload context

- **WHEN** `allowed_context_url` is unset and the payload `@context` is a remote URL string
- **THEN** parse fails without fetching that URL

#### Scenario: Configured URL accepted

- **WHEN** `allowed_context_url` is `https://example.org/context.json` and the payload `@context` is that same string
- **THEN** parse may proceed using the shared context loader

#### Scenario: Wrong URL rejected

- **WHEN** `allowed_context_url` is set and the payload `@context` is a different remote URL
- **THEN** parse fails without fetching the payload URL

### Requirement: Process-lifetime cache and polite fetch

The system SHALL fetch the allowlisted root context document via the polite HTTP client only on a process-lifetime cache
miss for that URL, and SHALL reuse the cached document for later parses in the same process. Transitive `@import`
documents discovered while resolving the root context SHALL also be fetched on miss and cached by URL. Cache hits MUST
NOT perform HTTP.

#### Scenario: Second parse uses cache

- **WHEN** two records in one process both reference the configured context URL
- **THEN** the root context document is fetched at most once

#### Scenario: Import documents cached

- **WHEN** the allowlisted root context document contains `@import` of another http(s) document
- **THEN** that import is fetched on first miss and served from cache on later resolves without a second HTTP GET

### Requirement: No uncached rdflib context network during parse

After the shared loader has populated the cache for the needed URLs, JSON-LD `graph.parse` for `jsonld` and
`html_jsonld` MUST NOT trigger an additional uncached network retrieval of context documents.

#### Scenario: Parse does not bypass the cache

- **WHEN** a payload uses the configured remote `@context` and the cache already holds that document
- **THEN** completing parse does not issue a new HTTP GET for that context URL
