# JSON-LD Parser

## Purpose

Shared PayloadParser in `middleware.parsing` that turns an inline JSON-LD discovery payload into an `rdf_graph`
ParsedPayload for any Protocol that discovers JSON-LD records without a second HTTP fetch.

## ADDED Requirements

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

The parser SHALL reject payloads containing a string-valued (remote) `@context` or `@import` anywhere in the document
with `ParserError`; inline object contexts are allowed.

#### Scenario: Remote context rejected

- **WHEN** the payload's `@context` is a URL string
- **THEN** parse fails with `ParserError` without any network access

### Requirement: Fail closed on unusable JSON-LD

The parser SHALL raise `ParserError` when the payload is empty, cannot be parsed as JSON-LD, or yields an empty graph.

#### Scenario: Empty graph fails the record

- **WHEN** the payload parses to zero triples
- **THEN** the parser fails with a descriptive error for that discovery unit
