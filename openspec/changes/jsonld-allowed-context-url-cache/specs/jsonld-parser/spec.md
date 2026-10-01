## MODIFIED Requirements

### Requirement: Never load remote JSON-LD contexts

The parser SHALL NOT perform uncached network retrieval of JSON-LD contexts during parse. When
`parser.allowed_context_url` is unset, payloads containing a string-valued remote `@context` (or remote `@import` on the
payload) MUST fail with `ParserError`. When `allowed_context_url` is set, a payload remote `@context` string MUST equal
that URL exactly (alone or as the sole remote string in a list); the parser MUST resolve it through the shared context
loader (process-lifetime cache, polite HTTP on miss, including transitive `@import` from the root document). Inline
object contexts remain allowed. The Schema.org-only `@vocab` substitution exception is removed. When
`allowed_context_url` is set and a cache miss requires HTTP, the parser MUST receive a non-null polite HTTP client.

#### Scenario: Remote context rejected

- **WHEN** `allowed_context_url` is unset and the payload's `@context` is a URL string
- **THEN** parse fails with `ParserError` without network access

#### Scenario: Schema.org context localized without fetch

- **WHEN** the payload's top-level `@context` is a Schema.org IRI and `allowed_context_url` is unset
- **THEN** parse fails with `ParserError` (no `@vocab` stub); operators MUST set `allowed_context_url` to that IRI

#### Scenario: Remote context rejected when unset

- **WHEN** `allowed_context_url` is unset and the payload's `@context` is a non-Schema.org URL string
- **THEN** parse fails with `ParserError` without network access

#### Scenario: Allowlisted context resolved via cache

- **WHEN** `allowed_context_url` matches the payload `@context` URL and a polite HTTP client is provided
- **THEN** parse succeeds using the shared loader and does not leave context fetch to an uncached rdflib default

#### Scenario: Client required on cache miss

- **WHEN** `allowed_context_url` is set, the cache misses, and `client` is null
- **THEN** parse fails indicating an HTTP client is required
