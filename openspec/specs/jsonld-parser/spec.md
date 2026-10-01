# jsonld-parser Specification

## Purpose

Shared PayloadParser in `middleware.parsing` that turns an inline JSON-LD discovery payload into an `rdf_graph`
ParsedPayload for any Protocol that discovers JSON-LD records without a second HTTP fetch.

## Requirements

### Requirement: Provide an inline JSON-LD PayloadParser producing rdf_graph

The system SHALL provide a PayloadParser selectable by registry key `jsonld` (`parser.type: jsonld`) that accepts a
`JsonLdDiscoveryResult` and returns `ParsedPayload` with `kind` `rdf_graph` and the discovery unit's identifier. It MUST
NOT require an HTTP client and MUST NOT restrict the vocabulary.

#### Scenario: Inline JSON-LD parses to rdf_graph

- **WHEN** a `JsonLdDiscoveryResult` carries well-formed JSON-LD and `client` is null
- **THEN** parse succeeds with `ParsedPayload.kind == rdf_graph`

#### Scenario: Other discovery units are rejected

- **WHEN** the parser receives a non-JSON-LD discovery unit
- **THEN** parse fails with a descriptive error

### Requirement: Never load remote JSON-LD contexts

The parser SHALL NOT perform uncached network retrieval of JSON-LD contexts during parse. Remote `@context` / `@import`
IRIs MUST be resolved through the shared context loader (process-lifetime cache, polite HTTP on miss, including
transitive `@import`). Inline object contexts remain allowed. The Schema.org-only `@vocab` substitution exception is
removed.

When `parser.allowed_context_url` is set, a payload remote `@context` string MUST equal that URL exactly (alone or as
the sole remote string in a list). When unset, absolute http(s) remotes MUST still be resolved through the shared
loader. `ParserConfig` MUST warn at validation time when a JSON-LD parser omits `allowed_context_url`. Relative or
non-http(s) references MUST fail with `ParserError`. Whenever a remote context must be resolved and the cache miss path
needs HTTP, the parser MUST receive a non-null polite HTTP client.

#### Scenario: Unset remote context requires client

- **WHEN** `allowed_context_url` is unset, the payload's `@context` is a URL string, and `client` is null
- **THEN** parse fails with `ParserError` indicating an HTTP client is required

#### Scenario: Unset remote context fetched

- **WHEN** `allowed_context_url` is unset, the payload's `@context` is an absolute http(s) URL, and a polite HTTP client
  is provided
- **THEN** parse succeeds via the shared loader

#### Scenario: Allowlisted context resolved via cache

- **WHEN** `allowed_context_url` matches the payload `@context` URL and a polite HTTP client is provided
- **THEN** parse succeeds using the shared loader and does not leave context fetch to an uncached rdflib default

#### Scenario: Client required on cache miss

- **WHEN** a remote context must be resolved, the cache misses, and `client` is null
- **THEN** parse fails indicating an HTTP client is required

#### Scenario: Wrong allowlisted URL rejected

- **WHEN** `allowed_context_url` is set and the payload `@context` is a different remote URL
- **THEN** parse fails without fetching that URL

### Requirement: Fail closed on unusable JSON-LD

The parser SHALL raise `ParserError` when the payload is empty, cannot be parsed as JSON-LD, or yields an empty graph.

#### Scenario: Empty graph fails the record

- **WHEN** the payload parses to zero triples
- **THEN** the parser fails with a descriptive error for that discovery unit
